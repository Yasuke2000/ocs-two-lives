#!/usr/bin/env python3
"""Copy the staging server's mod configs into pack/config/ so the repo holds every config.

packwiz then ships them and the server rewrites them from git on each start (the repo is the source of
truth). Client-only configs stay out so players keep their own client settings, and so do binary files:
some mods keep a database in config/ (CervLogger's SQLite), and shipping that overwrites and corrupts the
live file on every start. Files already in pack/config are kept unless --overwrite is given.

Usage: import_configs.py [--overwrite] [--dry-run]
"""
import io
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cluster  # noqa: E402
TARGET = ROOT / "pack" / "config"
NUL = bytes([0])

# Client-only, machine-local or runtime data: never ship these from the server.
SKIP = [
    re.compile(p) for p in (
        r"(^|/)[^/]*client[^/]*$",   # *-client.toml, *_client.json, ...
        r"^jei/", r"^spark/", r"^chunky/", r"^worldedit/(schematics|sessions)/",
        r"\.(db|sqlite)(-.*)?$", r"-(wal|shm)$",
        r"^fml\.toml$", r"\.(log|lock|bak|tmp)$", r"(^|/)\.", r"cache",
    )
]
MAX_BYTES = 512 * 1024


def fetch() -> tarfile.TarFile:
    result = cluster.mc("tar -C /data -cf - config")
    if result.returncode != 0:
        raise SystemExit(f"could not read the server's config: {result.stderr.decode(errors='replace').strip()}")
    data = result.stdout
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
            content = tar.extractfile(member).read()
            if NUL in content[:4096]:
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
            dest.write_bytes(content.replace(b"\r\n", b"\n"))
    print(f"added {added}, kept {kept} curated, skipped {skipped} client/local/binary")


if __name__ == "__main__":
    main()
