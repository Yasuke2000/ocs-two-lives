# OCS Tensura: Two Lives

Minecraft 1.21.1 NeoForge modpack for the Outcast Society server: live a hardcore human life,
die, and reincarnate into the world of *That Time I Got Reincarnated as a Slime* — shaped by how you lived.

Status: **Phase 0 (prototype)** — not playable yet.

## Install (Prism Launcher)

1. Create a NeoForge 1.21.1 instance.
2. Add [packwiz-installer-bootstrap](https://github.com/packwiz/packwiz-installer-bootstrap) as a pre-launch command:
   `"$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/Yasuke2000/ocs-two-lives/main/pack/pack.toml`

## Repo

- `pack/` — packwiz root (mods, configs, KubeJS scripts)
- `design/` — master plan, decisions, quest YAML, ID dumps
- `tools/` — validation, staging-server control, generators
- `tests/ingame/` — RCON acceptance tests

Development rules: [CLAUDE.md](CLAUDE.md).
