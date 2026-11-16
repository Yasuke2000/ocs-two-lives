"""PostToolUse hook: syntax-check the file just edited (JSON, KubeJS JS). Exit 2 feeds the error back."""
import json
import shutil
import subprocess
import sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")

if path.endswith(".json"):
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
    except ValueError as e:
        print(f"Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)
elif path.endswith(".js") and shutil.which("node"):
    r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    if r.returncode:
        print(f"JS syntax error in {path}:\n{r.stderr}", file=sys.stderr)
        sys.exit(2)
