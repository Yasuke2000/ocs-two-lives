"""PreToolUse hook: block hand edits to generated files (packwiz metadata, generated FTB Quests SNBT)."""
import json
import re
import sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "").replace("\\", "/")

GENERATED = [
    (re.compile(r"/pack/mods/[^/]+\.pw\.toml$"), "use `packwiz` (/add-mod) instead of editing .pw.toml"),
    (re.compile(r"/pack/index\.toml$"), "run `packwiz refresh` instead of editing index.toml"),
    (re.compile(r"/pack/config/ftbquests/quests/"), "edit design/quests/*.yaml and run /gen-quests"),
]

for pattern, hint in GENERATED:
    if pattern.search(path):
        print(f"Blocked: {path} is generated — {hint}.", file=sys.stderr)
        sys.exit(2)
