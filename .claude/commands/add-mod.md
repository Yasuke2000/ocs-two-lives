---
description: Add a mod to the pack after verifying a NeoForge 1.21.1 build exists
argument-hint: <modrinth-slug | cf:curseforge-slug> [phase]
---

Add `$ARGUMENTS` to the pack.

1. Check CLAUDE.md golden rule 6 (never-add list). Stop if it matches.
2. From `pack/`: try `packwiz mr add <slug> -y </dev/null` first; if the slug is CurseForge-only, use `packwiz cf add <slug> -y </dev/null`. stdin is closed on purpose so packwiz cannot silently pick a search result.
3. Read the output: confirm the **Project** name that was added is the mod you meant (a near-miss slug can add a look-alike project). If wrong, `packwiz remove` it and report.
4. List every dependency it pulled in. Check client-only mods have `side = "client"`.
5. Run `python tools/validate.py`.
6. Add a row to `design/decisions.md` only if this was a choice between alternatives.
7. Report: mod, version/jar, source, dependencies added, side.
