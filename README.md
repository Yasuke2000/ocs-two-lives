# OCS Tensura: Two Lives

Minecraft 1.21.1 NeoForge modpack for the Outcast Society server: live a hardcore human life,
die, and reincarnate into the world of *That Time I Got Reincarnated as a Slime* — shaped by how you lived.

Status: **Phase 0 (prototype)** — not playable yet.

**Testers: volg [TESTERS.md](TESTERS.md)** (stap-voor-stap, Nederlands).

[Player guide in English](docs/wiki/en/index.md) · [Spelersgids in het Nederlands](docs/wiki/nl/index.md)

## Install (Prism Launcher)

Add Instance → Import → paste
`https://github.com/Yasuke2000/ocs-two-lives/releases/download/prism-instance/OCS-Two-Lives.zip`.

The zip (built by `.github/workflows/prism-instance.yml` from `prism/`) sets MC 1.21.1 + NeoForge,
6 GB memory, the server entry, and [packwiz-installer-bootstrap](https://github.com/packwiz/packwiz-installer-bootstrap)
as pre-launch command, so mods sync from `pack/pack.toml` on every launch.

## Repo

- `pack/` — packwiz root (mods, configs, KubeJS scripts)
- `design/` — master plan, decisions, quest YAML, ID dumps
- `tools/` — validation, staging-server control, generators
- `tests/ingame/` — RCON acceptance tests

Development rules: [CLAUDE.md](CLAUDE.md).
