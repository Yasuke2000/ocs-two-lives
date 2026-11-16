---
description: Dump Tensura race, skill, entity and item IDs from the running server into design/dumps/
---

Goal: authoritative ID lists so nothing is ever invented (golden rule 4).

1. Make sure the staging server is up: `tools/server.sh status`.
2. Collect registries over RCON, e.g. `tools/server.sh rcon "kubejs dump_registry minecraft:item"` and the equivalent for `minecraft:entity_type`, plus Tensura's own registries (races, skills — find their registry keys in the server log or with `kubejs dump_registry` on the root registry list first). KubeJS writes dumps under `local/kubejs/` on the server; fetch them with `ssh root@100.109.28.21 "k3s kubectl -n ocs-two-lives exec deploy/mc -- cat /data/local/kubejs/<file>"`.
3. Keep only `tensura:` and `manascore:` entries (plus addon namespaces) and write one sorted file per category to `design/dumps/` (`races.txt`, `skills.txt`, `entities.txt`, `items.txt`), with a header line naming the Tensura version from `pack/mods/tensura-reincarnated.pw.toml`.
4. If a previous dump exists, show the diff — renamed IDs break scripts.
