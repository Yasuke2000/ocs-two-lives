# AGENTS.md — OCS Tensura: Two Lives

Instructions for any coding agent (Codex, ChatGPT, Claude, …) working in this repo. The project rules are
the same for every agent: **read `CLAUDE.md` first** (pinned versions, golden rules, data schema, KubeJS
conventions, test server, testing protocol). This file adds what a newcomer agent needs to pick up work, and
`docs/HANDOFF.md` holds the current state of the work in progress.

## What this is

A Minecraft 1.21.1 NeoForge modpack (packwiz, `pack/`) plus one Java mod (`mod/`, ttl-portals) and KubeJS
scripts (`pack/kubejs/`). Every player lives twice: a hardcore human Life 1 in `ttl:mortal_realm`, then a
reincarnation into the Tensura world (Life 2) shaped by Life 1 karma. Owner: **Yasuke** (always call them
Yasuke in anything players or contributors read). Players talk on Discord; the server runs on Yasuke's homelab.

## Map of the repo

| Path | What |
| --- | --- |
| `design/master-plan.md`, `design/decisions.md` | Design and the append-only decision log (add a row per real decision) |
| `design/architecture/*.md` | Architecture docs with work packages (sprint3-4.md, story-characters.md) |
| `design/data/*.toml` | Data for scripts → `python tools/gen_data.py` → `pack/kubejs/server_scripts/ttl/generated/data.js` |
| `design/quests/*.toml` | Quest chapters → `python tools/gen_quests.py` → FTB Quests SNBT |
| `design/builds/*.toml`, `blueprints/*.py` | Canon builds: blueprint → `python tools/build_structures.py <name>` → `pack/kubejs/data/ttl/structure/*.nbt`; placed in game by `life/builds.js` |
| `design/lore/*.md` | Lore + reference sources per place (always research references; mark "our interpretation") |
| `pack/kubejs/server_scripts/ttl/` | Game logic (life/, karma/, registry.js, bosses/, rep/, economy/, events/, discord/, …) |
| `pack/config/ttl/canon_regions.json`, `canon_map.txt` | The canon continent of the Tensura world (worldgen in `mod/`) |
| `mod/` | ttl-portals Java mod; release only with `python tools/release_mod.py` (bumps patch) |
| `tests/ingame/*.rcon` | In-game bot tests; `tests/*.py` offline unit tests |
| `tools/` | validate.py, server.sh (staging), local.sh (local server), check.sh, test_fast.sh, gen_*.py, verify_build.py, … |

## Hard rules (summary — CLAUDE.md is authoritative)

- Never commit secrets (Discord bot token, webhooks, GitHub tokens, RCON password). They live only in k8s
  secrets on the cluster (`discord`, `discord-bot`, `discord-announce`, `bug-reports`, `ttl-ops`). Never print them.
- Never invent mod/entity/item/skill ids — verify them in the jars or `design/dumps/`.
- Never hand-edit generated files or `.pw.toml`; use packwiz and the generators.
- **Before making builds, NPCs or content yourself, check whether a mod already has it** (every jar's
  `data/*/structure`, Tensura's character entities, Easy NPC presets) and **always use references**.
- KubeJS/Rhino gotchas: `var` inside functions; Rhino can't see `getUUID()`/`getStringUUID()` on players
  (use `TtlLife.uuid(player)`); KubeJS `entity.getType()` is only the id string (use `entity.isMonster()`);
  overloaded Java methods may need `obj['method(java.lang.String)'](…)`.
- No commits with a `Co-Authored-By` trailer. Plain messages. Patch versions for normal releases.
- Do not add LuckPerms (breaks the `/ttlbot` test players) or Chunky (crashes with Distant Horizons on every start).
- Life 2 arrival and the Jura rings: weak souls must not reach Tempest easily — don't "fix" the deadly magicule
  core around Tempest (owner decision); Life 1 and corridor souls are protected by `life/mortal_immunity.js`.

## How to work

1. `git pull`, read `docs/HANDOFF.md` (current state + next steps), pick the next open step.
2. Work on a branch or worktree; keep `main` deployable — `main` auto-deploys to the server via ttl-ops when
   nobody is online, then runs all in-game tests and posts the result to Discord #server-log.
3. Test locally first, then push (docs/server.md "Local testing"): `bash tools/check.sh` (validate, the fast unit
   tier, `node --check` on changed JS; the full `python -I -m unittest discover -s tests` still works and takes ~4
   min). For in-game changes: `bash tools/local.sh up`, then `bash tools/local.sh sync` after each edit and
   `bash tools/local.sh test <name>` (or `test all`) until it passes. Only then push.
4. After a deploy: `bash tools/server.sh test-all` must say "0 failing"; `bash tools/server.sh logs 2000 | grep -E "ERROR.*KubeJS|\[ttl\].*failed"` clean.
5. Update `docs/HANDOFF.md` when you stop: what you did, what is verified, what is next. When something lands on
   `main`, also update `docs/project-status.md` (metrics, what is built, in progress).

Server access (`tools/server.sh`) needs SSH to the homelab node over Tailscale or the kubeconfig in
`~/.kube/ocs-two-lives.yaml`; without that, work offline (validate + unit tests) and on a local server
(`tools/local.sh`, no access needed), and leave the staging checks for someone with access, listed in `docs/HANDOFF.md`.

Public roadmap: when a feature changes status for players (planned → being built → live on the server), update
`docs/roadmap-public.md` (EN + NL; "Live" says how to try it) and post it with `tools/post_roadmap.sh` (it edits
the three `#roadmap` messages in place; `docs/server.md`, "Roadmap and suggestions").
