#!/usr/bin/env python3
"""Build and release the ttl-portals mod locally (no GitHub Actions), then link it into the pack.

Steps: bump mod/gradle.properties → gradlew build → `gh release create mod-v<ver>` with the jar →
packwiz relinks ttl-portals to the release URL → validate.py → commit + push.
Needs: Java 17+ (Gradle downloads JDK 21 itself), gh (logged in), packwiz.

Usage: release_mod.py [--bump patch|minor|major] [--no-push]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD = ROOT / "mod"
PROPS = MOD / "gradle.properties"


def run(cmd, cwd=ROOT, **kw):
    print("$", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=cwd, check=True, **kw)


def packwiz() -> str:
    found = shutil.which("packwiz")
    for name in ("packwiz.exe", "packwiz"):
        candidate = Path.home() / "go" / "bin" / name
        if not found and candidate.exists():
            found = str(candidate)
    if not found:
        sys.exit("packwiz not found (go install github.com/packwiz/packwiz@latest)")
    return found


def bump(version: str, part: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bump", choices=["patch", "minor", "major"], default="patch")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()

    text = PROPS.read_text(encoding="utf-8")
    current = re.search(r"(?m)^mod_version=(.+)$", text).group(1).strip()
    version = bump(current, args.bump)
    PROPS.write_text(re.sub(r"(?m)^mod_version=.+$", f"mod_version={version}", text), encoding="utf-8", newline="\n")
    print(f"ttl-portals {current} -> {version}")

    gradlew = MOD / ("gradlew.bat" if os.name == "nt" else "gradlew")
    run([str(gradlew), "build", "--no-daemon", "-q"], cwd=MOD)
    jar = MOD / "build" / "libs" / f"ttl-portals-{version}.jar"
    if not jar.exists():
        sys.exit(f"build did not produce {jar}")

    repo = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                          cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    tag = f"mod-v{version}"
    run(["gh", "release", "create", tag, str(jar), "--title", f"ttl-portals {version}",
         "--notes", "Two Lives mod, built locally with tools/release_mod.py."])
    url = f"https://github.com/{repo}/releases/download/{tag}/{jar.name}"

    pw = packwiz()
    subprocess.run([pw, "remove", "ttl-portals"], cwd=ROOT / "pack", capture_output=True)
    run([pw, "url", "add", "OCS Two Lives Portals", url, "--meta-name", "ttl-portals", "-y"],
        cwd=ROOT / "pack", stdin=subprocess.DEVNULL)

    env = dict(os.environ, PATH=str(Path(pw).parent) + os.pathsep + os.environ.get("PATH", ""))
    validate = [sys.executable, "-I", str(ROOT / "tools" / "validate.py")]
    if subprocess.run(validate, cwd=ROOT, env=env).returncode != 0:
        run(validate, env=env)  # first run refreshes the packwiz index; the second must pass

    run(["git", "add", str(PROPS), "pack"])
    run(["git", "commit", "-q", "-m", f"release ttl-portals {version}"])
    if not args.no_push:
        run(["git", "push", "-q"])
    print(f"released {tag}: {url}")


if __name__ == "__main__":
    main()
