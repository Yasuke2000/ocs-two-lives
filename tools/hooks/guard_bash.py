"""PreToolUse hook: block commands that delete the world or the server's data volume."""
import json
import re
import sys

cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")

DANGEROUS = re.compile(
    r"rm\s+-\w*r\w*\s+\S*(world|/data\b)"
    r"|delete\s+(pvc|persistentvolumeclaim)\b"
    r"|delete\s+(ns|namespace)\s+ocs-two-lives",
    re.I,
)

if DANGEROUS.search(cmd):
    print("Blocked: this would delete the world or the server volume. Ask the owner first.", file=sys.stderr)
    sys.exit(2)
