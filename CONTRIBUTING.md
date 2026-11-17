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

Nothing reaches `main` (and so the server) without David's approval: `main` is protected, every pull
request needs a green `validate` check **and** an approving review from a code owner
([`.github/CODEOWNERS`](.github/CODEOWNERS)).

1. Pick or open an issue (see *Reporting issues* below) so others know what you are doing; assign yourself.
2. `git switch -c <short-name>` — one branch per change (never commit to `main` directly).
3. Edit (see the table below).
4. `python tools/validate.py` — must say `validation passed` (it also regenerates the pack index and
   checks generated files; commit what it changed).
5. Push the branch and open a pull request (`gh pr create --fill` or the GitHub button). Link the issue
   (`Closes #12`), fill in the checklist. GitHub asks David for a review automatically.
6. David reviews: approve, or *request changes* (push more commits to the same branch; they show up in
   the PR). Approved + green `validate` → **Squash and merge**.
7. After the merge the test server picks it up when nobody is online, runs all bot tests and marks the
   commit ✅ or ❌ ("ttl staging" on GitHub; also posted in Discord #logging-and-server-notifactions).
8. Test it in game. Problems? `/bug <what happened>`.

Small, focused PRs get reviewed fastest. Unsure about an idea? Open an *Idea* issue first and talk it
through before building it.

## Reporting issues

| What | How | Lands as |
|---|---|---|
| Something broke while playing | in game: `/bug <what happened>` (adds your position, life, inventory and log) | issue with `bug`, `from-game`, `triage` |
| Bug you found outside the game | GitHub → Issues → New → *Bug* | `bug` |
| Balance (too hard/easy, numbers) | *Balance* form | `balance` |
| Feature, quest or system idea | *Idea* form | `idea` |
| A build to make or improve | *Build request* form (paste reference images) | `build` |
| World doesn't match the lore | *World / lore fix* form (coordinates + source) | `lore` |

New issues are posted to Discord. David triages them (labels, priority, who takes it); take one by
assigning yourself and saying so in the issue.

## What to edit where

| You want to change… | Edit | Then |
|---|---|---|
| Our own balance numbers (skill rarities and caps, trials, …) | `design/data/*.toml` | `python tools/gen_data.py` |
| A mod's settings | `pack/config/<mod>…` — find it in [docs/configs.md](docs/configs.md) | `python tools/config_index.py` if you add/remove a file |
| Two Lives behaviour (life loop, corridor, trials, registry) | `pack/kubejs/server_scripts/ttl/` | read the KubeJS notes in CLAUDE.md first |
| Add or update a mod | `packwiz mr add <slug>` (or `/add-mod` in Claude Code) | check it has a NeoForge 1.21.1 build |
| The Java mod (`ttl-portals`) | `mod/src/` | `python tools/release_mod.py` (maintainers) |
| Server settings (view distance, memory, …) | not in this repo — see [docs/server.md](docs/server.md) | ask David |
| A build (hall, arena, village…) | `blueprints/<name>.py` (Python: `fill`, `box`, `disc`, `pillar`, `around`; arenas share `blueprints/_arena.py`) | `python tools/build_structures.py` → check the [build gallery](docs/previews/README.md); in game `/ttl build <name>`. Arenas and the spawn rebuild themselves after you bump `ARENA_VERSION` (`trial_defs.js`) or `TTL_MORTAL_SPAWN_VERSION` (`mortal_spawn.js`) |
| Bring any build from the world into the repo | build it in game (by hand or WorldEdit), note two opposite corners | `python tools/capture.py <name> <dimension> x1 y1 z1 x2 y2 z2` → `blueprints/<name>.nbt` + structure + previews (no player, no size-48 limit) |
| Place a build without a player | — | `tools/server.sh place <name> <dimension> x y z` |
| Polish a build in game | WorldEdit (ops): `/ttl build <name>`, edit, select its exact box, `//copy`, `//schem save <name>` | `python tools/import_schem.py <name>` → `blueprints/<name>.schem` (wins over the `.py`) + new structure and previews |
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
