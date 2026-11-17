#!/usr/bin/env python3
"""Copy the staging server's mod configs into pack/config/ so the repo holds every config.

packwiz then ships them and the server rewrites them from git on each start (the repo is the source of
truth). Client-only configs stay out so players keep their own client settings. Files already in
pack/config are kept unless --overwrite is given (they are curated: shipped decisions live there).

Usage: import_configs.py [--overwrite] [--dry-run]
"""
import io
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "pack" / "config"
NODE = os.environ.get("TTL_NODE", "root@100.109.28.21")

# Client-only or machine-local: never ship these from the server.
SKIP = [
    re.compile(p) for p in (
        r"(^|/)[^/]*client[^/]*$",   # *-client.toml, *_client.json, ...
        r"^jei/", r"^spark/", r"^chunky/", r"^fml\.toml$", r"\.(log|lock|bak|tmp)$", r"(^|/)\.", r"cache",
    )
]
MAX_BYTES = 512 * 1024


def fetch() -> tarfile.TarFile:
    cmd = ["ssh", "-n", "-o", "ConnectTimeout=10", "-o", "LogLevel=ERROR", NODE,
           "k3s kubectl -n ocs-two-lives exec deploy/mc -- tar -C /data -cf - config"]
    data = subprocess.run(cmd, capture_output=True, check=True).stdout
    return tarfile.open(fileobj=io.BytesIO(data))


def main() -> None:
    overwrite = "--overwrite" in sys.argv
    dry = "--dry-run" in sys.argv
    added = kept = skipped = 0
    with fetch() as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.startswith("config/"):
                continue
            rel = member.name[len("config/"):]
            if any(p.search(rel) for p in SKIP) or member.size > MAX_BYTES:
                skipped += 1
                continue
            dest = TARGET / rel
            if dest.exists() and not overwrite:
                kept += 1
                continue
            added += 1
            if dry:
                print("would add", rel)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = tar.extractfile(member).read().replace(b"\r\n", b"\n")
            dest.write_bytes(content)
    print(f"added {added}, kept {kept} curated, skipped {skipped} client/local")


if __name__ == "__main__":
    main()
