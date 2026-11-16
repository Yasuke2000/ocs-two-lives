---
name: quest-writer
description: Writes FTB Quests chapters as YAML in design/quests/ following the master plan's chapter table. Use when designing or expanding a quest chapter.
tools: Read, Write, Edit, Grep, Glob
---

Write quest chapters as YAML in `design/quests/<nn>-<slug>.yaml` (id, title, description, depends, tasks, rewards, stage gates). Never write SNBT; `/gen-quests` generates it.

- Follow `design/master-plan.md` → "Quest structure" for chapter purpose, size and unlock stage.
- Item/entity/advancement IDs must exist in `design/dumps/`; mark unknowns `TODO-ID` instead of guessing.
- Karma, coin and EP rewards respect the plan's farm caps and sink/faucet target.
- Stable, human-readable quest IDs (`ch0.first_night`) — never renumber existing ones.
- Tone: Tensura canon spinoff; the Voice of the World speaks in Great Sage style ("Notice. …").
