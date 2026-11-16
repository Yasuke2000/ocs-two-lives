"""Read a server log on stdin; print [ttl] errors, mod-loading failures and exceptions. Exit 1 if any."""
import re
import sys

PATTERNS = [
    re.compile(r"\[ttl\].*(error|fail)", re.I),
    re.compile(r"ERROR.*kubejs", re.I),
    re.compile(r"Mod Loading has failed|Missing or unsupported mandatory dependencies|Crash report", re.I),
    re.compile(r"^\S*Exception: ", re.M),
]

hits = [line.rstrip() for line in sys.stdin if any(p.search(line) for p in PATTERNS)]
for h in hits:
    print(h)
print(f"{len(hits)} problem line(s)" if hits else "log clean")
sys.exit(1 if hits else 0)
