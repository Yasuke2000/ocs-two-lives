#!/usr/bin/env python3
"""Audit the quest web (design/quests/*.toml) and print it as mermaid (design/quests.md, "The web").

The generator (gen_quests.py) already refuses unknown or looping dependencies. This tool asks the next questions:
  * can every quest be unlocked at all (a quest with `min_deps` N needs N of its dependencies to be unlockable)?
  * are the chapters one connected web, and which quests nothing depends on (dead ends)?
Stdlib only. Usage: quest_graph.py            print the chapter map and the Life 1 / Life 2 maps as mermaid
                   quest_graph.py --check    exit 1 on a quest that can never unlock or a chapter outside the web
"""
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_quests  # noqa: E402

# Quests that may have no dependency at all: the two ways a soul enters the book (Life 1 at Wayfarer's Rest, Life 2 on rebirth).
ROOTS = {("mortal_life", "only_once"), ("reborn", "eyes_open")}


def load(sources: Path | None = None):
    """Return (chapters, quests): chapters {key: chapter table}, quests {(chapter, key): {deps, min, optional, life, title}}."""
    chapters, quests = {}, {}
    for src in sorted((sources or gen_quests.SOURCES).glob("*.toml")):
        with src.open("rb") as f:
            data = tomllib.load(f)
        ch = data["chapter"]
        chapters[ch["key"]] = ch
        for q in data.get("quests", []):
            deps = [gen_quests.split_dep(ch["key"], d) for d in q.get("deps", [])]
            quests[(ch["key"], q["key"])] = {
                "deps": deps, "min": int(q.get("min_deps", len(deps))), "optional": bool(q.get("optional")),
                "title": q["title"], "life": ch.get("life"), "repeatable": bool(q.get("repeatable")),
            }
    return chapters, quests


def unlockable(quests) -> set:
    """Fixed point: a quest unlocks once `min` of its dependencies do (a quest with no dependency always unlocks)."""
    done: set = set()
    changed = True
    while changed:
        changed = False
        for k, q in quests.items():
            if k not in done and sum(d in done for d in q["deps"]) >= q["min"]:
                done.add(k)
                changed = True
    return done


def dead_ends(quests) -> list:
    """Non-optional quests that no other quest depends on."""
    used = {d for q in quests.values() for d in q["deps"]}
    return sorted(k for k, q in quests.items() if k not in used and not q["optional"])


def chapter_edges(quests) -> dict:
    """{(from_chapter, to_chapter): [(from_quest, to_quest), ...]} for every cross-chapter dependency."""
    out: dict = {}
    for k, q in quests.items():
        for d in q["deps"]:
            if d[0] != k[0]:
                out.setdefault((d[0], k[0]), []).append((d[1], k[1]))
    return out


def components(chapters, edges) -> list:
    """Weakly connected groups of chapters."""
    parent = {c: c for c in chapters}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    for a, b in edges:
        parent[find(a)] = find(b)
    groups: dict = {}
    for c in chapters:
        groups.setdefault(find(c), []).append(c)
    return sorted(groups.values())


def problems(chapters=None, quests=None) -> list[str]:
    if chapters is None:
        chapters, quests = load()
    out = []
    unlock = unlockable(quests)
    for k in sorted(set(quests) - unlock):
        out.append(f"{k[0]}/{k[1]} can never unlock (its dependencies loop or are themselves locked)")
    roots = {k for k, q in quests.items() if not q["deps"]}
    for k in sorted(roots - ROOTS):
        out.append(f"{k[0]}/{k[1]} has no dependency but is not a book entry ({', '.join('/'.join(r) for r in sorted(ROOTS))}): an orphan root")
    for k in sorted(ROOTS - roots):
        out.append(f"{k[0]}/{k[1]} is a book entry and must have no dependencies")
    groups = components(chapters, chapter_edges(quests))
    if len(groups) > 1:
        out.append("the chapters are not one web: " + " | ".join(",".join(g) for g in groups))
    return out


# ---- mermaid -----------------------------------------------------------------------------------------------------

def _id(chapter: str, key: str) -> str:
    return f"{chapter}__{key}"


def mermaid_chapters(chapters, quests) -> str:
    """One node per chapter (grouped Life 1 / Life 2 / both), one arrow per distinct cross-chapter link, labelled with the first
    quest pair of the link and how many links there are."""
    edges = chapter_edges(quests)
    lines = ["flowchart LR"]
    for title, pred in (("Life 1", lambda c: c.get("life") == 1), ("Both lives", lambda c: c.get("life") == "both"),
                        ("Life 2", lambda c: c.get("life") == 2)):
        ks = sorted((k for k, c in chapters.items() if pred(c)), key=lambda k: chapters[k].get("order", 0))
        lines.append(f'  subgraph {title.replace(" ", "_")}["{title}"]')
        for k in ks:
            n = sum(1 for q in quests if q[0] == k)
            lines.append(f'    {k}["{chapters[k]["title"]}<br/>{n} quests"]')
        lines.append("  end")
    for (a, b), pairs in sorted(edges.items()):
        label = f"{pairs[0][0]} to {pairs[0][1]}" + (f" (+{len(pairs) - 1})" if len(pairs) > 1 else "")
        lines.append(f'  {a} -->|"{label}"| {b}')
    return "\n".join(lines)


def mermaid_quests(chapters, quests, chapter_keys, spine=None) -> str:
    """The quests of the given chapters as nodes, with every dependency inside the group; only the spine chapter shows its
    own quests when `spine` names a chapter (the others are drawn as their capstones and entries only)."""
    keep = {k for k in quests if k[0] in chapter_keys}
    used = {d for k in keep for d in quests[k]["deps"] if d in keep}
    lines = ["flowchart TD"]
    for ck in chapter_keys:
        lines.append(f'  subgraph {ck}["{chapters[ck]["title"]}"]')
        for k in sorted(keep):
            if k[0] != ck:
                continue
            q = quests[k]
            is_entry = any(d[0] != ck for d in q["deps"])
            is_exit = any(k in quests[o]["deps"] and o[0] != ck for o in keep)
            if spine and ck != spine and not (is_entry or is_exit or k in used and not q["deps"]):
                continue
            shape = ("([", "])") if q["optional"] else ("[", "]")
            lines.append(f'    {_id(*k)}{shape[0]}"{q["title"]}"{shape[1]}')
        lines.append("  end")
    shown = {line.split("[")[0].split("(")[0].strip() for line in lines if "[" in line or "(" in line}
    for k in sorted(keep):
        for d in quests[k]["deps"]:
            if d in keep and _id(*d) in shown and _id(*k) in shown:
                dotted = quests[k]["min"] < len(quests[k]["deps"])
                lines.append(f"  {_id(*d)} {'-.->' if dotted else '-->'} {_id(*k)}")
    return "\n".join(lines)


def main() -> None:
    chapters, quests = load()
    if "--check" in sys.argv:
        bad = problems(chapters, quests)
        for line in bad:
            print("FAIL quest web:", line)
        sys.exit(1 if bad else 0)
    print("```mermaid\n" + mermaid_chapters(chapters, quests) + "\n```")
    ends = dead_ends(quests)
    print(f"\n{len(quests)} quests, {len(unlockable(quests))} unlockable, dead ends (non-optional, nothing depends on them):")
    for c, k in ends:
        print(f"  {c}/{k}")


if __name__ == "__main__":
    main()
