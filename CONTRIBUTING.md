# Working on OCS Tensura: Two Lives

Everything that makes up the pack is in this repo: mods (`pack/mods/`), every mod config
(`pack/config/`), our scripts (`pack/kubejs/`), our own gameplay numbers (`design/data/`) and the small
Java mod (`mod/`). The test server installs the pack straight from `main`.

## Setup (once)

| Tool | Why | Get it |
|---|---|---|
| Git + a GitHub account with access to this repo | Changes | git-scm.com — ask David to add you as collaborator |
| Python 3.11+ | `tools/*.py` (validation, generators) | python.org |
| packwiz | Mods and the pack index | `go install github.com/packwiz/packwiz@latest` (needs Go) or a release binary |
| gh (GitHub CLI) | Releases, PRs | cli.github.com, then `gh auth login` |
| Prism Launcher | Playing/testing | see [TESTERS.md](TESTERS.md) |
| Java 17+ | Only for the Java mod (`mod/`) | adoptium.net — Gradle downloads JDK 21 itself |

Using Claude Code? Open the repo folder; [CLAUDE.md](CLAUDE.md) and `.claude/` (commands like
`/add-mod`, `/validate`) apply automatically.

## The workflow

1. `git switch -c <short-name>` — one branch per change.
2. Edit (see the table below).
3. `python tools/validate.py` — must say `validation passed` (it also regenerates the pack index and
   checks generated files; commit what it changed).
4. Push and open a pull request; fill in the checklist.
5. After review and merge to `main`, the test server picks it up automatically when nobody is online,
   runs all bot tests and marks the commit ✅ or ❌ ("ttl staging" status on GitHub).
6. Test it in game. Problems? `/bug <what happened>` in game files an issue with all the details.

## What to edit where

| You want to change… | Edit | Then |
|---|---|---|
| Our own balance numbers (skill rarities and caps, trials, …) | `design/data/*.toml` | `python tools/gen_data.py` |
| A mod's settings | `pack/config/<mod>…` — find it in [docs/configs.md](docs/configs.md) | `python tools/config_index.py` if you add/remove a file |
| Two Lives behaviour (life loop, corridor, trials, registry) | `pack/kubejs/server_scripts/ttl/` | read the KubeJS notes in CLAUDE.md first |
| Add or update a mod | `packwiz mr add <slug>` (or `/add-mod` in Claude Code) | check it has a NeoForge 1.21.1 build |
| The Java mod (`ttl-portals`) | `mod/src/` | `python tools/release_mod.py` (maintainers) |
| Server settings (view distance, memory, …) | not in this repo — see [docs/server.md](docs/server.md) | ask David |
| Bot tests | `tests/ingame/*.rcon` | run by the server after each deploy |

## Rules (short version of CLAUDE.md)

- Never invent mod, race, skill, entity or item IDs — look them up (`design/dumps/`, the mod's jar).
- Never hand-edit `pack/mods/*.pw.toml`, `pack/index.toml` or files marked GENERATED.
- Our namespace is `ttl` (items, tags, data keys, dimensions).
- Every unique-skill grant goes through `pack/kubejs/server_scripts/ttl/registry.js`.
- Big decisions go into `design/decisions.md` (append a row, never rewrite history).
- Integrating with Tensura/ManasCore/Great Sage: read [design/manas-integration.md](design/manas-integration.md).

## Where things are

- `design/master-plan.md` — the full design · `design/roadmap.md` — what is done and next
- `design/decisions.md` — why things are the way they are
- `docs/configs.md` — every config file · `docs/server.md` — server settings
- `tools/server.sh` — staging server control (needs homelab SSH; most people don't need it)
