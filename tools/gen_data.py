#!/usr/bin/env python3
"""Generate pack/kubejs/server_scripts/ttl/generated/data.js from design/data/*.toml.

Gameplay numbers live in TOML so balancing never needs a code change. The scripts read them as `TtlData`.
Usage: gen_data.py            write the file
       gen_data.py --check    exit 1 if the file is out of date (used by validate.py)
"""
import json
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "design" / "data"
TARGET = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl" / "generated" / "data.js"
CANON = ROOT / "pack" / "config" / "ttl" / "canon_regions.json"
SCRIPTS = ROOT / "pack" / "kubejs" / "server_scripts" / "ttl"


def check_skills(skills: dict) -> None:
    seen = {}
    for rarity in ("legendary", "rare", "common"):
        if rarity not in skills["caps"]:
            raise SystemExit(f"skills.toml: caps.{rarity} missing")
        for skill in skills[rarity]["skills"]:
            if skill in seen:
                raise SystemExit(f"skills.toml: {skill} is both {seen[skill]} and {rarity}")
            seen[skill] = rarity


def check_guide(guide: dict) -> None:
    # life/guide.js opens these sets by name; the guide screen needs a title and a body on every page.
    for name in ("main", "corridor", "life2"):
        pages = guide.get(name)
        if not isinstance(pages, list) or not pages:
            raise SystemExit(f"guide.toml: [[{name}]] pages missing")
    for name, pages in guide.items():
        for i, page in enumerate(pages, 1):
            if not str(page.get("title", "")).strip() or not str(page.get("body", "")).strip():
                raise SystemExit(f"guide.toml: {name} page {i} needs a title and a body")


def check_mortal_banned(banned: dict) -> None:
    # life/mortal_banned.js matches item ids against these lists; a typo would silently ban nothing.
    patterns = {"namespaces": r"[a-z0-9_.-]+", "items": r"[a-z0-9_.-]+:[a-z0-9_/.-]+",
                "tags": r"[a-z0-9_.-]+:[a-z0-9_/.-]+", "allow": r"[a-z0-9_.-]+:[a-z0-9_/.-]+"}
    for key, pattern in patterns.items():
        values = banned.get(key)
        if not isinstance(values, list):
            raise SystemExit(f"mortal_banned.toml: {key} must be a list (use [] for none)")
        for v in values:
            if not isinstance(v, str) or not re.fullmatch(pattern, v):
                raise SystemExit(f"mortal_banned.toml: {key} entry {v!r} is not a valid "
                                 f"{'namespace, like tensura' if key == 'namespaces' else 'full id, like mod:thing'}")
        if len(set(values)) != len(values):
            raise SystemExit(f"mortal_banned.toml: {key} lists an entry twice")


def settlement_box(script: str, anchor: str, footprint: str) -> tuple[int, int, int, int]:
    """World box (x0, z0, x1, z1, margin included) of Tempest or Dwargon, as their scripts compute it."""
    m = re.search(anchor + r":\s*\{\s*x:\s*(-?\d+),\s*z:\s*(-?\d+)", (SCRIPTS / "life" / script).read_text(encoding="utf-8"))
    line = next(t for t in (SCRIPTS / "generated" / footprint).read_text(encoding="utf-8").splitlines()
                if t.startswith("const ") and "Footprint = " in t)
    f = json.loads(line[line.index("{"):])
    x0, z0 = int(m.group(1)) - f["arrival"][0], int(m.group(2)) - f["arrival"][2]
    return x0 - f["margin"], z0 - f["margin"], x0 + f["size"][0] + f["margin"] - 1, z0 + f["size"][2] + f["margin"] - 1


def check_landmarks(landmarks: dict) -> None:
    # life/landmarks.js places these; x/z come from canon_regions.json unless given, and every landmark keeps
    # `keepout` blocks (plus its reach) clear of Tempest's and Dwargon's boxes.
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    refs = {lm["name"]: lm["ref"] for lm in canon["landmarks"]}
    scale = canon["width"] / 2570
    boxes = {"Tempest": settlement_box("tempest.js", "LANDMARK", "tempest_footprint.js"),
             "Dwargon": settlement_box("dwargon.js", "GATE", "dwargon_footprint.js")}
    seen = set()
    for lm in landmarks["landmark"]:
        name = lm.get("name", "")
        where = f"landmarks.toml: {name or '?'}"
        if not re.fullmatch(r"[a-z0-9_]+", name) or name in seen:
            raise SystemExit(f"{where}: name must be unique [a-z0-9_]")
        seen.add(name)
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", str(lm.get("structure", ""))):
            raise SystemExit(f"{where}: structure must be a namespaced id")
        if lm.get("surface") not in ("land", "water", "any"):
            raise SystemExit(f"{where}: surface must be land, water or any")
        for key in ("reach", "version"):
            if not isinstance(lm.get(key), int) or lm[key] < 1:
                raise SystemExit(f"{where}: {key} must be a positive integer")
        if "canon" in lm and lm["canon"] not in refs:
            raise SystemExit(f"{where}: canon landmark {lm['canon']!r} not in canon_regions.json")
        if ("x" in lm) != ("z" in lm):
            raise SystemExit(f"{where}: give both x and z, or neither")
        if "x" not in lm:
            if "canon" not in lm:
                raise SystemExit(f"{where}: needs x/z or canon")
            ref = refs[lm["canon"]]
            lm["x"] = round((ref[0] - canon["origin"][0]) * scale)
            lm["z"] = round((ref[1] - canon["origin"][1]) * scale)
        for label, (x0, z0, x1, z1) in boxes.items():
            gap = math.hypot(max(x0 - lm["x"], 0, lm["x"] - x1), max(z0 - lm["z"], 0, lm["z"] - z1))
            if gap < landmarks["keepout"] + lm["reach"]:
                raise SystemExit(f"{where}: ({lm['x']}, {lm['z']}) is {gap:.0f} blocks from {label}, "
                                 f"needs {landmarks['keepout'] + lm['reach']} (keepout + reach)")

MASTER_COIN_LIST = ROOT / "pack" / "config" / "lightmanscurrency" / "MasterCoinList.json"


def coin_table(where: str, table, coins: list) -> None:
    if not isinstance(table, dict) or not table:
        raise SystemExit(f"{where}: must be a non-empty coin table like {{ silver = 3 }}")
    for coin, n in table.items():
        if coin not in coins or not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise SystemExit(f"{where}: {coin} = {n!r} (coins are {', '.join(coins)}; amounts are positive integers)")


def check_economy(eco: dict, data: dict) -> None:
    # economy/*.js read the coin chain, bounties and fees from here; the Lightman's Currency config must agree with
    # the coin chain, or the shops, ATMs and bounty payouts would count different money.
    coins = eco["coins"]["chain"]
    items, rates = eco["coins"]["item"], eco["coins"]["rate"]
    if set(items) != set(coins) or set(rates) != set(coins[1:]):
        raise SystemExit("economy.toml: [coins.item] needs every coin and [coins.rate] every coin but the first")
    for coin in coins:
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", items[coin]):
            raise SystemExit(f"economy.toml: coins.item.{coin} {items[coin]!r} is not a namespaced id")
        if coin in rates and (not isinstance(rates[coin], int) or rates[coin] < 2):
            raise SystemExit(f"economy.toml: coins.rate.{coin} must be an integer >= 2")
    if MASTER_COIN_LIST.exists():
        main = [c for c in json.loads(MASTER_COIN_LIST.read_text(encoding="utf-8"))["Chains"] if c["chain"] == "main"]
        if len(main) != 1:
            raise SystemExit("MasterCoinList.json: needs exactly one chain named main")
        core = main[0]["CoreChain"]
        want = [(items[c], None if i == 0 else rates[c]) for i, c in enumerate(coins)]
        have = [(e["Coin"], e.get("exchangeRate")) for e in core]
        if want != have:
            raise SystemExit(f"economy.toml [coins] and MasterCoinList.json main CoreChain disagree: {want} vs {have}")
    ranks = [r["id"] for r in eco["rank"]]
    if not ranks or eco["rank"][0]["points"] != 0 or len(set(ranks)) != len(ranks) or             [r["points"] for r in eco["rank"]] != sorted(r["points"] for r in eco["rank"]):
        raise SystemExit("economy.toml: [[rank]] ids must be unique and points ascending from 0")
    if eco["guild"].get("announce_rank") not in ranks:
        raise SystemExit("economy.toml: guild.announce_rank is not a rank id")
    landmarks = {lm["name"] for lm in data.get("landmarks", {}).get("landmark", [])}
    factions = {f["id"] for f in data.get("factions", {}).get("faction", [])}
    g = eco["guild"]
    # giver: desk (guild receptionists) or fuze (the guild master); Fuze's bounties are exactly the ones at
    # fuze_min_rank and above, so a receptionist never has to hand out a contract she may not let anyone accept.
    fuze_from = g.get("fuze_min_rank", ranks[-1])
    if fuze_from not in ranks:
        raise SystemExit("economy.toml: guild.fuze_min_rank is not a rank id")
    seen, per = set(), {"daily": 0, "weekly": 0}
    for b in eco["bounty"]:
        where = f"economy.toml: bounty {b.get('id', '?')}"
        if not re.fullmatch(r"[a-z0-9_]+", b.get("id", "")) or b["id"] in seen:
            raise SystemExit(f"{where}: id must be unique [a-z0-9_]")
        seen.add(b["id"])
        if b.get("kind") not in ("kill", "deliver", "visit") or b.get("period") not in per:
            raise SystemExit(f"{where}: kind is kill|deliver|visit and period daily|weekly")
        if b.get("min_rank") not in ranks:
            raise SystemExit(f"{where}: min_rank is not a rank id")
        giver = b.get("giver", "desk")
        if giver not in ("desk", "fuze"):
            raise SystemExit(f"{where}: giver is desk or fuze")
        if (giver == "fuze") != (ranks.index(b["min_rank"]) >= ranks.index(fuze_from)):
            raise SystemExit(f"{where}: giver {giver} but min_rank {b['min_rank']} (Fuze gives rank {fuze_from} and up, "
                             f"the desk everything below)")
        if not all(isinstance(b.get(k), int) and b[k] >= 0 for k in ("count", "points", "weight")) or b["count"] < 1:
            raise SystemExit(f"{where}: count >= 1, points and weight >= 0 (integers)")
        if b["kind"] == "visit":
            if landmarks and b["target"] not in landmarks:
                raise SystemExit(f"{where}: target {b['target']!r} is not a landmark in landmarks.toml")
        elif not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", b.get("target", "")):
            raise SystemExit(f"{where}: target must be a namespaced id")
        if "region" in b and (b["kind"] != "kill" or (factions and b["region"] not in factions)):
            raise SystemExit(f"{where}: region is a faction id and only for kill bounties")
        coin_table(f"{where} reward.coins", b.get("reward", {}).get("coins"), coins)
        for f, n in b["reward"].get("rep", {}).items():
            if (factions and f not in factions) or not isinstance(n, int) or n < 1:
                raise SystemExit(f"{where}: reward.rep.{f} = {n!r} (a faction id and a positive integer)")
        if b["weight"] > 0:
            per[b["period"]] += 1
    first = ranks[0]
    for giver, period, n in (("desk", "daily", g["daily"]), ("desk", "weekly", g["weekly"]),
                             ("fuze", "daily", g.get("fuze_daily", 0)), ("fuze", "weekly", g.get("fuze_weekly", 0))):
        pool = [b for b in eco["bounty"] if b.get("giver", "desk") == giver and b["period"] == period and b["weight"] > 0]
        if len(pool) < n or (giver == "desk" and period == "daily" and not any(b["min_rank"] == first for b in pool)):
            raise SystemExit(f"economy.toml: needs >= {n} {giver} {period} bounties with weight > 0 "
                             f"(the desk's daily ones need at least one for rank {first})")
    if not isinstance(g.get("fuze_turnin_at_desk", False), bool):
        raise SystemExit("economy.toml: guild.fuze_turnin_at_desk is true or false")
    for name, table in eco["sinks"].items():
        coin_table(f"economy.toml: sinks.{name}", table, coins)
    for block in eco["merit"]["blocks"]:
        if not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_/.-]+", block):
            raise SystemExit(f"economy.toml: merit block {block!r} is not a namespaced id")


def render() -> str:
    data = {}
    for path in sorted(SOURCES.glob("*.toml")):
        with path.open("rb") as f:
            data[path.stem] = tomllib.load(f)
    if "skills" in data:
        check_skills(data["skills"])
    if "guide" in data:
        check_guide(data["guide"])
    if "mortal_banned" in data:
        check_mortal_banned(data["mortal_banned"])
    if "landmarks" in data:
        check_landmarks(data["landmarks"])
    if "economy" in data:
        check_economy(data["economy"], data)
    body = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
    return (
        "// priority: 200\n"
        "// GENERATED by tools/gen_data.py from design/data/*.toml. Do not edit; edit the TOML and regenerate.\n"
        f"const TtlData = {body}\n"
    )


def main() -> None:
    text = render()
    if "--check" in sys.argv:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != text:
            print("FAIL generated/data.js is stale: run python tools/gen_data.py")
            sys.exit(1)
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
