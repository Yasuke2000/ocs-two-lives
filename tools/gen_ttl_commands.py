#!/usr/bin/env python3
"""Builds docs/dev/ttl-commands.md, the reference of every /ttl command, from the KubeJS registration source.

What is read from the source (pack/kubejs/server_scripts/ttl/**, every `event.register(Commands.literal('ttl')...)`):
the command tree (literals and arguments), which nodes need op level 2 (`.requires(...)`), which nodes can run on
their own (`.executes(...)`) and the argument types. What cannot be read from code is written by hand in
docs/dev/ttl-commands.toml: the group, one line of what it does, what it is for, and the notes per command.

  python tools/gen_ttl_commands.py            write docs/dev/ttl-commands.md
  python tools/gen_ttl_commands.py --discord  print the Discord messages (separated by --- lines) for tools/post_ttl_commands.sh
  python tools/gen_ttl_commands.py --compare-help FILE   compare the parsed tree with a pasted `/help ttl` listing
  python tools/gen_ttl_commands.py --check    exit 1 when the file is stale or the toml and the source disagree
  python tools/gen_ttl_commands.py --tree     print the parsed tree (one syntax line per command), for debugging
  python tools/gen_ttl_commands.py --usage    print the usage lines the way `/help ttl` shows them

The output is sorted and carries no date, so the same source gives the same bytes (the date of a Discord post
comes from tools/post_ttl_commands.sh).
"""
import copy
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "pack/kubejs/server_scripts/ttl"
TOML = ROOT / "docs/dev/ttl-commands.toml"
OUT = ROOT / "docs/dev/ttl-commands.md"

GROUPS = [
    ("life", "Life and rebirth"),
    ("story", "Story and quests"),
    ("world", "World and map"),
    ("builds", "Builds and landmarks"),
    ("bosses", "Bosses and arenas"),
    ("nations", "Nations and economy"),
    ("paths", "Paths (necro, artifice, roads, choices)"),
    ("social", "Social (party, companion, guild)"),
    ("ops", "Ops and testing"),
]
EXTRA_ROOTS = ["locate"]    # other commands this repo adds a node to; the toml key is "<root> <word>", e.g. "locate place"
AUDIENCES = {
    "player": "PLAYER",
    "staff": "staff",
    "test": "test bot",
}


# ---------------------------------------------------------------------------------------------
# Parsing the registration source
# ---------------------------------------------------------------------------------------------
def strip_comments(s):
    """Removes // and /* */ comments outside strings and template literals; keeps line numbers."""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"`":
            j = i + 1
            while j < n and s[j] != c:
                if s[j] == "\\":
                    j += 1
                j += 1
            out.append(s[i:j + 1])
            i = j + 1
        elif s.startswith("//", i):
            while i < n and s[i] != "\n":
                i += 1
        elif s.startswith("/*", i):
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * s.count("\n", i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def match_paren(s, i):
    """s[i] == '(' -> index of the matching ')' (strings and template literals are skipped)."""
    depth, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"`":
            j = i + 1
            while j < n and s[j] != c:
                if s[j] == "\\":
                    j += 1
                j += 1
            i = j
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced parentheses")


class Node:
    def __init__(self, kind, name, arg_type=None):
        self.kind = kind            # "lit" or "arg"
        self.name = name
        self.arg_type = arg_type    # for arguments: INTEGER, PLAYER, STRING, GREEDY_STRING, ...
        self.op = False             # .requires(...) on this node
        self.runs = False           # .executes(...) on this node
        self.children = []
        self.where = ""             # file:line of the literal
        self.values = None          # a literal made in a loop: the names it stands for

    def add(self, other):
        """Adds a child; a node registered twice (two files, or two chains) is merged into the first."""
        if other.values is not None:
            vals, other.values = other.values, None
            for v in vals:
                clone = copy.deepcopy(other)
                clone.name = v
                self.add(clone)
            return other
        for c in self.children:
            if c.kind == other.kind and c.name == other.name:
                c.op = c.op or other.op
                c.runs = c.runs or other.runs
                c.where = c.where or other.where
                for g in other.children:
                    c.add(g)
                return c
        self.children.append(other)
        return other


NODE_START = re.compile(r"(?:Commands|C)\.(?:literal|argument)\(")
FUNC_DEF = re.compile(r"var\s+(\w+)\s*=\s*(?:\(([^)]*)\)|(\w+))\s*=>\s*")
VAR_DEF = re.compile(r"var\s+(\w+)\s*=\s*")
REASSIGN = re.compile(r"(\w+)\s*=\s*(\w+)\s*\.then\(")
def register_re(root):
    return re.compile(r"event\.register\(\s*(?:Commands|C)\.literal\('" + root + r"'\)")
CALL = re.compile(r"(\w+)\(")
DOT_CALL = re.compile(r"\.(\w+)\(")
WORD = re.compile(r"\w+")


def split_args(text, start, end):
    """Top-level comma separated argument spans of text[start:end] as (from, to) pairs."""
    spans, depth, i, last = [], 0, start, start
    while i < end:
        c = text[i]
        if c in "'\"`":
            j = i + 1
            while j < end and text[j] != c:
                if text[j] == "\\":
                    j += 1
                j += 1
            i = j
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            spans.append((last, i))
            last = i + 1
        i += 1
    if text[last:end].strip():
        spans.append((last, end))
    return spans


def parse_file(path, root_name="ttl"):
    text = strip_comments(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT).as_posix() if ROOT in path.parents else path.name
    funcs = {}   # name -> (params, body start): a node builder, called with arguments
    nodes = {}   # name -> Node: a node held in a variable (grown with x = x.then(...) in loops)
    arrays = {}  # name -> list of strings (for forEach loops over a named array)

    def line_of(pos):
        return text.count("\n", 0, pos) + 1

    def skip_ws(i):
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        return i

    def loop_values(pos, ident):
        """The strings a `[...].forEach(ident => ...)` (or `array.forEach`) loop around pos goes over."""
        head = text[max(0, pos - 600):pos]
        hits = list(re.finditer(r"(\[[^\]]*\]|\w+)\s*\.forEach\(\s*\(?\s*" + re.escape(ident) + r"\b", head))
        if not hits:
            return None
        src = hits[-1].group(1)
        if src.startswith("["):
            return re.findall(r"'([^']*)'", src)
        return arrays.get(src)

    def parse_primary(i, env):
        i = skip_ws(i)
        m = NODE_START.match(text, i)
        if m:
            end = match_paren(text, m.end() - 1)
            args = split_args(text, m.end(), end)
            first = text[args[0][0]:args[0][1]].strip() if args else ""
            kind = "lit" if text[i:m.end()].endswith("literal(") else "arg"
            at = re.search(r"Arguments\.(\w+)", text[m.end():end])
            node = Node(kind, "?", at.group(1) if at else None)
            if re.fullmatch(r"'[^']*'", first):
                node.name = first[1:-1]
            elif first in env:
                a, b, _ = env[first]
                node.name = text[a:b].strip().strip("'")
            elif re.fullmatch(r"\w+", first):
                node.values = loop_values(i, first)
                node.name = "{" + first + "}"
            elif "||" in first:   # name || 'default'
                node.name = re.findall(r"'([^']*)'", first)[-1]
            if kind == "lit":
                node.where = f"{rel}:{line_of(i)}"
            return node, end + 1
        m = CALL.match(text, i)
        if m and m.group(1) in funcs:
            params, body = funcs[m.group(1)]
            end = match_paren(text, m.end() - 1)
            spans = split_args(text, m.end(), end)
            inner = {p: (a, b, env) for p, (a, b) in zip(params, spans)}
            node, _ = parse_chain(body, inner)
            return node, end + 1
        m = CALL.match(text, i)
        if m and m.group(1) == "xz":   # world/domain_commands.js: <x> <z> (outcome|outcome), a builder with a block body
            end = match_paren(text, m.end() - 1)
            names = re.findall(r"'([^']*)'", text[m.end():end])
            x, z = Node("arg", "x", "INTEGER"), Node("arg", "z", "INTEGER")
            x.add(z)
            for o in names:
                leaf = Node("lit", o)
                leaf.runs = True
                z.add(leaf)
            return x, end + 1
        m = WORD.match(text, i)
        if m and m.group(0) in env:          # a node handed to a builder: .then(then)
            a, b, caller = env[m.group(0)]
            node, _ = parse_chain(a, caller)
            return node, m.end()
        if m and m.group(0) in nodes:
            return copy.deepcopy(nodes[m.group(0)]), m.end()
        raise ValueError(f"{rel}:{line_of(i)}: cannot parse a command node at {text[i:i + 60]!r}")

    def parse_chain(i, env):
        node, i = parse_primary(i, env)
        while True:
            m = DOT_CALL.match(text, skip_ws(i))
            if not m:
                return node, i
            what = m.group(1)
            if what == "then":
                child, _ = parse_chain(m.end(), env)
                node.add(child)
            elif what == "requires":
                # requires(op) / requires(ops) are op level 2 (checked: every such variable is hasPermission(2)); an
                # explicit hasPermission(0) is everyone.
                node.op = not re.search(r"hasPermission\(\s*0\s*\)", text[m.end():match_paren(text, m.end() - 1)])
            elif what == "executes":
                node.runs = True
            i = match_paren(text, m.end() - 1) + 1

    # Definitions, reassignments and registrations are processed in file order.
    events = []
    for m in FUNC_DEF.finditer(text):
        body = CALL.match(text, m.end())
        if NODE_START.match(text, m.end()) or (body and body.group(1) in funcs_so_far(text, m.start())):
            events.append((m.start(), "func", m))
    for m in VAR_DEF.finditer(text):
        events.append((m.start(), "var", m))
        arr = re.compile(r"\[([^\]]*)\]").match(text, m.end())
        if arr and re.fullmatch(r"(\s*'[^']*'\s*,?)+", arr.group(1) or "x"):
            arrays[m.group(1)] = re.findall(r"'([^']*)'", arr.group(1))
    for m in REASSIGN.finditer(text):
        if m.group(1) == m.group(2):
            events.append((m.start(), "re", m))
    for m in register_re(root_name).finditer(text):
        events.append((m.start(), "reg", m))
    events.sort(key=lambda e: (e[0], e[1] != "func"))
    root = Node("lit", root_name)
    for _, kind, m in events:
        if kind == "func":
            plist = m.group(2) if m.group(2) is not None else m.group(3)
            funcs[m.group(1)] = ([p.strip() for p in plist.split(",") if p.strip()], m.end())
        elif kind == "var":
            if m.group(1) in funcs or FUNC_DEF.match(text, m.start()):
                continue
            try:
                nodes[m.group(1)], _ = parse_chain(m.end(), {})
            except ValueError:
                pass   # not a command node (an ordinary variable)
        elif kind == "re" and m.group(1) in nodes:
            child, _ = parse_chain(m.end(), {})
            nodes[m.group(1)].add(child)
        elif kind == "reg":
            end = match_paren(text, text.index("(", m.start()))
            i = m.end()
            while True:
                mm = DOT_CALL.match(text, skip_ws(i))
                if not mm or mm.start() >= end:
                    break
                if mm.group(1) == "then":
                    child, _ = parse_chain(mm.end(), {})
                    root.add(child)
                i = match_paren(text, mm.end() - 1) + 1
    return root


def funcs_so_far(text, pos):
    """Names of node builders defined before pos (a builder whose body is a call to another builder)."""
    return {m.group(1) for m in FUNC_DEF.finditer(text, 0, pos) if NODE_START.match(text, m.end())}


def build_tree(root_name="ttl"):
    root = Node("lit", root_name)
    for path in sorted(SRC.rglob("*.js")):
        if f"literal('{root_name}')" not in path.read_text(encoding="utf-8"):
            continue
        sub = parse_file(path, root_name)
        for c in sub.children:
            root.add(c)
    return root


# ---------------------------------------------------------------------------------------------
# Syntax
# ---------------------------------------------------------------------------------------------
def label(n):
    return n.name if n.kind == "lit" else f"<{n.name}>"


def usage(n):
    """The `/help ttl` style syntax of a node's subtree, e.g. `absorb [status|duel|...]` or `answer <word>`."""
    head = label(n)
    kids = n.children
    if not kids:
        return head
    if len(kids) == 1:
        tail = usage(kids[0])
        return f"{head} [{tail}]" if n.runs else f"{head} {tail}"
    body = "|".join(label(c) for c in kids)
    return f"{head} [{body}]" if n.runs else f"{head} ({body})"


def base_of(top):
    """Descends through single-argument chains: `karma <target>` -> (['<target>'], node of <target>)."""
    tokens, n = [], top
    while len(n.children) == 1 and n.children[0].kind == "arg":
        c = n.children[0]
        tokens.append(f"[{label(c)}]" if n.runs else label(c))
        n = c
    return tokens, n


def find(node, token):
    for c in node.children:
        if label(c) == token:
            return c
    return None


def walk_path(base, path):
    """Nodes along a row's path (relative to base), or None when the path is not in the source."""
    nodes, n = [], base
    for tok in path.split():
        n = find(n, tok)
        if n is None:
            return None
        nodes.append(n)
    return nodes


# ---------------------------------------------------------------------------------------------
# Checking the hand-written file against the source, and rendering
# ---------------------------------------------------------------------------------------------
def load_toml():
    with TOML.open("rb") as f:
        return tomllib.load(f)


def problems_and_rows(root, doc):
    """Returns (problems, entries): entries are the documented commands in render order."""
    problems = []
    tops = {c.name: c for c in root.children}
    for extra in EXTRA_ROOTS:   # commands added to another command's node: /locate place <id>
        for c in build_tree(extra).children:
            tops[f"{extra} {c.name}"] = c
    cmds = {k: v for k, v in doc.items() if k != "meta"}
    for name in sorted(set(tops) - set(cmds)):
        problems.append(f"/{name if ' ' in name else 'ttl ' + name}: in the source ({tops[name].where}) but not in {TOML.name}")
    for name in sorted(set(cmds) - set(tops)):
        problems.append(f"/ttl {name}: in {TOML.name} but not in the source (removed or renamed?)")
    entries = []
    for name, c in cmds.items():
        top = tops.get(name)
        if top is None:
            continue
        if c.get("group") not in dict(GROUPS):
            problems.append(f"/ttl {name}: unknown group {c.get('group')!r}")
        if c.get("who") not in AUDIENCES or "does" not in c:
            problems.append(f"/ttl {name}: needs who (player|staff|test) and does")
            continue
        for text in [c["does"]] + [r[2] for r in c.get("subs", [])]:
            if re.search(r"[<>]", re.sub(r"`[^`]*`", "", text)):
                problems.append(f"/ttl {name}: put `<...>` in backticks in {text[:50]!r} (Markdown and Discord eat bare angle brackets)")
        runtime = bool(c.get("runtime_ops"))
        if c["who"] == "player" and top.op:
            problems.append(f"/ttl {name}: marked player but the source requires op level 2")
        if c["who"] != "player" and not top.op and not runtime:
            problems.append(f"/ttl {name}: marked {c['who']} but the source lets everyone run it (set runtime_ops when the handler checks)")
        tokens, base = base_of(top)
        rows, covered = [], set()
        for row in c.get("subs", []):
            path, who, does = row
            nodes = walk_path(base, path)
            if nodes is None:
                problems.append(f"/ttl {name} {path}: not in the source")
                continue
            if who not in AUDIENCES:
                problems.append(f"/ttl {name} {path}: unknown who {who!r}")
                continue
            op = top.op or any(n.op for n in nodes)
            if who == "player" and op:
                problems.append(f"/ttl {name} {path}: marked player but the source requires op level 2")
            if who != "player" and not op and not runtime:
                problems.append(f"/ttl {name} {path}: marked {who} but the source lets everyone run it")
            covered.add(path.split()[0])
            toks = path.split()
            rows.append((" ".join(toks[:-1] + [usage(nodes[-1])]), who, does))
        for kid in base.children:
            if label(kid) not in covered:
                problems.append(f"/ttl {name} {label(kid)}: a subcommand in the source ({kid.where or top.where}) without a row in {TOML.name}")
        entries.append((name, c, tokens, rows))
    return problems, entries


def head_text(name, tokens):
    """`/ttl wish <id>`, or `/locate place <id>` for a command of another root (key "locate place")."""
    return ("/" + name if " " in name else "/ttl " + name) + "".join(" " + t for t in tokens)


def tag(who):
    return "**PLAYER**" if who == "player" else AUDIENCES[who]


GROUP_INTRO = {
    "life": "Life 1, the Spirit Corridor and the rebirth into Life 2; karma, the soul carryover, the unique-skill registry, eras and how uniques change hands.",
    "story": "The story core (Oath, acts), the story cast, the quest book and the side jobs of the adventurers.",
    "world": "The World Chronicle, faction domains, world events and the places that define where souls arrive.",
    "builds": "Canon builds and landmarks, the chunk tickets the placers use and the Mortal Realm's spawn.",
    "bosses": "The boss framework and the PvP and party arenas, including the Walpurgis Hall.",
    "nations": "Nations, the coin economy, merit and reputation.",
    "paths": "The player paths: Necromancer, Artificer, the two roads and the moral-choice scenes.",
    "social": "Parties, companions, the Free Guild, the guide and the leaderboard.",
    "ops": "Debug, Discord and test tooling for staff and the test bots.",
}


def render(entries, doc):
    meta = doc.get("meta", {})
    n_sub = sum(len(r) for _, _, _, r in entries)
    verified = (f" and matched the live server's `/help ttl` ({meta.get('help_entries')} entries) on {meta.get('verified')}"
                if meta.get("verified") else "")
    if meta.get("newer_than_help"):
        verified += "; " + meta["newer_note"]
    out = [
        "# /ttl command reference",
        "",
        "<!-- Generated by tools/gen_ttl_commands.py from pack/kubejs/server_scripts/ttl/** and docs/dev/ttl-commands.toml. "
        "Edit the toml (descriptions) or the KubeJS source (commands), then re-run the generator; do not edit this file by hand. -->",
        "",
        f"Every `/ttl` command of OCS Two Lives with what it does and what it is for: {len(entries)} commands and {n_sub} subcommand rows. "
        f"The command tree is read from the KubeJS registration source{verified}.",
        "",
        "- **PLAYER**: anyone can run it (permission level 0). Some only work in a given life or place.",
        "- staff: op level 2 (`hasPermission(2)`): admin tools and fixes.",
        "- test: op level 2 too, but only for the test bots and `tests/ingame/*.rcon` (`expect`, `test*` hooks); they print `ttl: ...` when an assertion fails.",
        "- `<name>` is a required argument, `[x]` an optional part, `(a|b)` a choice.",
        "",
    ]
    for key, title in GROUPS:
        mine = [e for e in entries if e[1]["group"] == key]
        if not mine:
            continue
        out += [f"## {title}", "", GROUP_INTRO[key], ""]
        for name, c, tokens, rows in mine:
            out.append(f"### `{head_text(name, tokens)}`")
            out.append(f"{tag(c['who'])} {c['does']}")
            for text, who, does in [r for r in rows if r[1] != "test"]:
                out.append(f"- {tag(who)} `{text}`: {does}")
            tests = [r for r in rows if r[1] == "test"]
            if tests:
                out.append("- test: " + " ".join(f"`{t}` {d}" for t, _, d in tests))
            out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


LIMIT = 1900          # characters per Discord message (Discord's own limit is 2000)
MARK = "-# /ttl command reference"   # last line of every bot message; tools/post_ttl_commands.sh finds its messages by it
REPO_URL = "https://github.com/Yasuke2000/ocs-two-lives"


def blocks_of(entries, key):
    """Discord text of every command block of a group, one (heading, lines) pair per command; test hooks by name only."""
    out = []
    for name, c, tokens, rows in entries:
        if c["group"] != key:
            continue
        head = f"**`{head_text(name, tokens)}`**"
        lines = [f"{tag(c['who'])} {c['does']}"]
        for text, who, does in [r for r in rows if r[1] != "test"]:
            lines.append(f"- {tag(who)} `{text}`: {does}")
        tests = [r for r in rows if r[1] == "test"]
        if tests:
            lines.append("- test: " + ", ".join(f"`{t}`" for t, _, _ in tests))
        out.append((head, lines))
    return out


def split_block(head, lines, room):
    """One command block as one or more texts that fit in `room` characters (a long block continues under its heading)."""
    texts, cur = [], [head]
    for line in lines:
        if len("\n".join(cur + [line])) > room and len(cur) > 1:
            texts.append("\n".join(cur))
            cur = [f"{head} (continued)"]
        cur.append(line)
    texts.append("\n".join(cur))
    return texts


def discord_messages(entries, doc):
    """The messages of the Discord post: a header, then every group in as few messages as fit, in order.
    The header carries {date}, which tools/post_ttl_commands.sh fills in at post time."""
    meta = doc.get("meta", {})
    n_sub = sum(len(r) for _, _, _, r in entries)
    bodies = []
    for key, title in GROUPS:
        texts = []
        for head, lines in blocks_of(entries, key):
            texts += split_block(head, lines, LIMIT - 200)
        if not texts:
            continue
        parts, cur = [], ""
        for t in texts:
            if cur and len(cur) + 2 + len(t) > LIMIT - 130:
                parts.append(cur)
                cur = ""
            cur = f"{cur}\n\n{t}" if cur else t
        parts.append(cur)
        for i, p in enumerate(parts):
            label = f"**{title}**" + (f" ({i + 1}/{len(parts)})" if len(parts) > 1 else "")
            intro = f"\n{GROUP_INTRO[key]}" if i == 0 else ""
            bodies.append(f"{label}{intro}\n\n{p}")
    total = len(bodies) + 1
    verified = (f"; the tree matched the live `/help ttl` ({meta.get('help_entries')} entries) on {meta.get('verified')}"
                if meta.get("verified") else "")
    if meta.get("newer_than_help"):
        verified += "; " + meta["newer_note"]
    header = "\n".join([
        "**/ttl command reference**, generated from the repo, updated {date}",
        f"{len(entries)} commands and {n_sub} subcommand rows in {len(bodies)} messages below, grouped by system. "
        f"Source: <{REPO_URL}/blob/main/docs/dev/ttl-commands.md>, read from the KubeJS command registration{verified}.",
        "**PLAYER** = anyone can run it · staff = op level 2 · test = op level 2, only for the test bots and `tests/ingame/*.rcon` "
        "(listed by name here; what each one asserts is in the file)",
        "`<x>` is required, `[x]` optional, `(a|b)` a choice.",
        "Wrong or missing? Fix `docs/dev/ttl-commands.toml` or the command itself in a pull request; these messages are re-posted from the repo "
        "with `tools/post_ttl_commands.sh`, so do not edit them by hand.",
    ])
    msgs = [header] + bodies
    out = [f"{m}\n{MARK} {i + 1}/{total}" for i, m in enumerate(msgs)]
    for m in out:
        assert len(m) <= 2000, f"a message is {len(m)} characters"
    return out


def compare_help(root, path, newer=()):
    """Compares the command tree with a pasted `/help ttl` listing. /help folds deep branches (`arrival [expect]`), so
    only the first level is compared strictly: every direct subcommand must be shown by /help, and every word /help
    shows must exist somewhere in the parsed subtree."""
    norm = lambda line: re.sub(r"[\[\]()]", " ", line).replace("|", " ").split()
    want = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            t = norm(line)
            want[t[1]] = set(t[2:])
    tops = {c.name: c for c in root.children if c.name not in newer}

    def words(n):
        out = {label(n)}
        for c in n.children:
            out |= words(c)
        return out

    bad = []
    for k in sorted(set(want) | set(tops)):
        if k not in tops:
            bad.append(f"/ttl {k}: in /help but not parsed")
        elif k not in want:
            bad.append(f"/ttl {k}: parsed but not in /help")
        else:
            direct = {label(c) for c in tops[k].children}
            if direct - want[k]:
                bad.append(f"/ttl {k}: parsed but not in /help: {sorted(direct - want[k])}")
            if want[k] - words(tops[k]):
                bad.append(f"/ttl {k}: in /help but not parsed: {sorted(want[k] - words(tops[k]))}")
    return bad, len(want)


def main(argv):
    root = build_tree()
    if "--tree" in argv:
        def dump(n, d=0):
            print("  " * d + label(n) + ("  [op]" if n.op else "") + ("  [runs]" if n.runs else ""))
            for c in n.children:
                dump(c, d + 1)
        dump(root)
        return 0
    if "--usage" in argv:
        for c in sorted(root.children, key=lambda x: x.name):
            print("/ttl " + usage(c))
        return 0
    if "--compare-help" in argv:
        newer = load_toml().get("meta", {}).get("newer_than_help", [])
        bad, n = compare_help(root, argv[argv.index("--compare-help") + 1], newer)
        print("\n".join(bad) if bad else f"the parsed tree matches the {n} entries of /help ttl")
        return 1 if bad else 0
    doc = load_toml()
    problems, entries = problems_and_rows(root, doc)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    if "--discord" in argv:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        print("\n---\n".join(discord_messages(entries, doc)))
        return 0
    text = render(entries, doc)
    if "--check" in argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(ROOT)} is stale: run python tools/gen_ttl_commands.py", file=sys.stderr)
            return 1
        print(f"ok: {len(entries)} commands documented")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(entries)} commands, {len(text)} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
