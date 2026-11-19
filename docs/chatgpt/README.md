# Knowledge pack for ChatGPT: the creative side of OCS Tensura: Two Lives

This folder is everything ChatGPT needs for the **creative** work on the project: drawing a new world map, concept art per place, blueprint designs,
lore and quest text in English and Dutch, and NPC skin art. Read this file first, then the others.

| File | What it holds |
|---|---|
| **README.md** (this file) | The project, the two lives, the world rules, the division of labour, how to contribute, a map of the repo |
| [world.md](world.md) | Canon geography in one place: every canon place, the nations, relative geography, distances, borders, named features, the owner's decisions about the world |
| [builds.md](builds.md) | How to design a build: the blueprint format with a worked example, palettes, size and terrain rules, previews, all existing builds and which look wrong |
| [places/](places/) | One page per canon place (58): lore, what it should look like, the BlueMap audit of today with screenshots |
| [art.md](art.md) | The art style guide, the NPC skin system, what an image deliverable looks like |
| [tasks.md](tasks.md) | The open creative tasks as a checklist, and the (still empty) spec of the world map deliverable |
| [source-map/](source-map/README.md) | Reference renders of the current world (Lerfing's map), with scale and origin |

## 1. What the project is

**OCS Tensura: Two Lives** is a Minecraft 1.21.1 NeoForge modpack for the Outcast Society server, a free, non-commercial fan project
based on *That Time I Got Reincarnated as a Slime* (Tensei Shitara Slime Datta Ken). The owner is **Yasuke**: always call them Yasuke in anything a player or contributor reads.
The pack (mods, configs, KubeJS scripts) is built with packwiz in [`pack/`](../../pack/); one small Java mod (`mod/`, ttl-portals) adds portals, the Mortal End
dragon fight and the rebirth menu. Players talk on Discord; the server runs on Yasuke's homelab. Technical rules for coding agents: [CLAUDE.md](../../CLAUDE.md) and [AGENTS.md](../../AGENTS.md).
Design: [design/master-plan.md](../../design/master-plan.md); the append-only decision log: [design/decisions.md](../../design/decisions.md);
player guide: [English](../wiki/en/index.md), [Nederlands](../wiki/nl/index.md).

## 2. The two lives and the world rules

Every player lives twice.

- **Life 1: the Mortal Realm.** A hardcore human life in its own dimension (`ttl:mortal_realm`, with its own Nether and End), starting at the hamlet **Wayfarer's Rest**.
  One death ends it, even if another player deals the last blow. The finale is the Mortal Dragon. Life 1 has no Tensura creatures, no Tensura structures and no canon places;
  its only builds are Wayfarer's Rest and a few waypoints (ferry, keep, market, mine, shrine, tower).
- **The Spirit Corridor.** After the first death a soul reads its verdict (karma), chooses a Last Wish, may face a Trial of the Soul and reincarnates with the Great Sage.
- **Life 2: the Tensura world.** The reincarnation, shaped by the karma of Life 1: race, skills, reputation. The normal survival world: nations, wars, bosses, quests, a Demon Lord council, the story of the series (the Oath, light or dark).
  Life 2 happens in the overworld of `world-ttl`.

**World rules (owner decisions).**
1. **The continent**: the canon Tensura world, drawn once: Jura and its forest in the middle, the Canaat mountains with Dwargon to the north, Lake Siss and Milim's lands to the east,
   Eurazania and Sarion to the south, the Western Nations and Damargania to the west, the Ice Continent far north, El Dorado far south-west. Every canon place is in [world.md](world.md).
2. **The ocean**: an ocean ring around the continent (deep sea, about 2,000 blocks wide).
3. **Vanilla beyond**: past the ocean the ordinary Minecraft overworld, with vanilla structures; nothing canon.
4. **Life 1 in the Mortal Realm, Life 2 in the Tensura world.** Souls are kept to their own world.
5. **A new world**: the Tensura continent is being **replaced by a new, fully own map** (decision of 19/11/2026). Today's map is *Tensura by Lerfing*, bought by Yasuke and used on the server; it is shown here only as reference renders and screenshots.
   See [world.md](world.md) and [tasks.md](tasks.md).

## 3. Who does what

| ChatGPT: creative | Claude: technical |
|---|---|
| The new world map drawing and its notes | Everything that touches the game: KubeJS scripts, the Java mod, data generators, placement, tests, packwiz, CI, the server |
| Concept art per place | Turning a drawing into a world (import, terrain, rings), placing builds, repairing terrain |
| Blueprint designs (Python blueprints or plan sketches), palettes | Running `build_structures.py` and the other generators, writing build placement data, in-game verification |
| Lore and quest text in EN and NL | Applying text to the quest data, regenerating the quest book, wiring localisation |
| NPC skin art | Putting skins into the pack and the catalogue, regenerating |

**ChatGPT never edits `pack/kubejs/server_scripts/` or `mod/`.** Also never edit generated files: `pack/config/ftbquests/quests/**`, `pack/index.toml`, `pack/mods/*.pw.toml`,
`pack/kubejs/server_scripts/ttl/generated/`, `pack/kubejs/data/ttl/structure/*.nbt`, `docs/previews/*-iso.png` / `*-top.png` and `docs/previews/README.md`, and nothing under `tools/`, `tests/` or `.github/`.
You can read all of it; if something there should change, say so in the pull request and Claude does it.

Hard rules that always apply (from [CLAUDE.md](../../CLAUDE.md)): never invent a mod, entity, item or block id; never commit secrets or personal data; keep the pack's licensing clean (section 6);
fan work stays non-commercial; Yasuke is "Yasuke".

## 4. How to contribute

**One small pull request per item**, one concern each: one place's concept art, one blueprint, one lore page, one quest chapter's text, one NPC skin. Name the branch `chatgpt/<item>` (for example `chatgpt/art-sealed-cave`).
Nothing reaches `main` without Yasuke's approval: `main` is protected, every pull request needs a green `validate` check and a review from the code owner ([CONTRIBUTING.md](../../CONTRIBUTING.md)). Claude reviews the technical side.
A change that only adds files under `docs/` and `design/lore/` does not touch the game.

### File locations and naming

All names are lowercase with underscores, no spaces. `<id>` is a place id exactly as in [`design/data/anchors.toml`](../../design/data/anchors.toml) and [places/](places/) (`tempest`, `sealed_cave`, `ogre_village_ruin`, ...).

| Deliverable | Where | Notes |
|---|---|---|
| Concept art of a place | `docs/art/places/<id>.png` + `docs/art/places/<id>.md` | [art.md](art.md) section 2 |
| Plan sketch of a build | `docs/art/places/<id>-plan.png` | |
| New blueprint | `blueprints/<name>.py` (`<name>` = the build or place id) | [builds.md](builds.md); Claude runs the generator, writes `design/builds/<name>.toml` and commits the structure and previews |
| Lore of a place | `design/lore/<id>.md` (EN) | keep the "Canon / What we built / Sources" shape; mark "our interpretation" |
| Lore, quest and NPC text drafts (EN and NL) | `docs/chatgpt/drafts/chapter_<nn>.md`, `docs/chatgpt/drafts/nl/<source file stem>.md`, `docs/chatgpt/drafts/lore-pass.md` | tables: `key \| EN \| NL`. Claude applies them to the quest data and regenerates ([tasks.md](tasks.md)) |
| NPC skin | `docs/art/npc/hand_<look>_<n>.png` (+ `-preview.png`) | 64 x 64 PNG; [art.md](art.md) section 4 |
| World map drawing and notes | the folder named in the deliverable spec ([tasks.md](tasks.md) section 8, to follow) | |
| Wiki pages (player guide) | `docs/wiki/en/<page>.md` and `docs/wiki/nl/<page>.md`, always both | keep them in step |

Languages: **English** for everything in the repo except the NL texts. **Dutch** is Flemish (Vlaams-Nederlands), informal "je/jij". Dates are written dd/mm/yyyy, as in the decision log.
Be concise; mark canon (with a link to the source) apart from our interpretation. If you are unsure whether a fact is canon, say "unverified" instead of guessing.

## 5. A map of the repo (where things live)

| You want | Look in |
|---|---|
| **Lore** per place and per topic (canon, our interpretation, sources) | [`design/lore/`](../../design/lore/): `<id>.md` per build, [`world.md`](../../design/lore/world.md) (regions), [`tempest.md`](../../design/lore/tempest.md), [`dwargon.md`](../../design/lore/dwargon.md), [`heraldry.md`](../../design/lore/heraldry.md), [`skins.md`](../../design/lore/skins.md), [`lore-pass-2026-11.md`](../../design/lore/lore-pass-2026-11.md) |
| **Data**: every canon place, nations, factions, arrival, bosses, NPCs, story | [`design/data/`](../../design/data/): [`anchors.toml`](../../design/data/anchors.toml) (the 58 places), [`factions.toml`](../../design/data/factions.toml), [`arrival.toml`](../../design/data/arrival.toml), [`landmarks.toml`](../../design/data/landmarks.toml), [`story.toml`](../../design/data/story.toml), [`npcs.toml`](../../design/data/npcs.toml), `bosses.toml`, `sidequests.toml`; and [`pack/config/ttl/canon_regions.json`](../../pack/config/ttl/canon_regions.json), [`canon_map.txt`](../../pack/config/ttl/canon_map.txt) (nations, colours, the continent grid) |
| **Blueprints** (builds as code) | [`blueprints/*.py`](../../blueprints/), shared helpers `blueprints/_*.py`; build placement in [`design/builds/*.toml`](../../design/builds/) (Claude's); the tool is [`tools/blueprint.py`](../../tools/blueprint.py) and [`tools/build_structures.py`](../../tools/build_structures.py) |
| **Previews** | [`docs/previews/`](../previews/README.md): iso and top view of every build, the NPC skin sheet, the heraldry sheet, the region atlas, the Jura check |
| **Quests** | Source: [`design/quests/*.toml`](../../design/quests/) (Life 1 chapters 0, Life 2 chapters 1 to 13, side chapters 20 to 23); notes: [`design/quests.md`](../../design/quests.md); the quest book in the game is generated from these (`pack/config/ftbquests/`, do not edit) |
| **Wiki** (player guide, EN + NL) | [`docs/wiki/en/`](../wiki/en/index.md), [`docs/wiki/nl/`](../wiki/nl/index.md): world map, the rings of Jura, karma, nations, story and Oath, FAQ |
| **Art** | [`docs/art/`](../art/npc-skin-prompts.md) (skin prompts; concept art goes to `docs/art/places/`), [`docs/chatgpt/source-map/`](source-map/README.md) (reference renders of the old world) |
| **Decisions and status** | [`design/decisions.md`](../../design/decisions.md) (dated, append-only), [`docs/HANDOFF.md`](../HANDOFF.md) (work in progress), [`docs/project-status.md`](../project-status.md), [`docs/roadmap-public.md`](../roadmap-public.md) |
| **Architecture docs** | [`design/architecture/`](../../design/architecture/) (the Lerfing import, the world state, the story, the paths); the own-world design is being written there |
| **Credits** | [`CREDITS.md`](../../CREDITS.md) |

## 6. Licensing: what you may and may not add (the repo is public)

- **Never add the old map's files.** *Tensura by Lerfing* was purchased by Yasuke and its licence allows use on servers; it is **not redistributed as world files**. No world files, no region files, no zips, no full-resolution terrain exports go in this repository.
  The reference renders in [source-map/](source-map/README.md) (downsampled JPEG) and the BlueMap screenshots are fine; the BlueMap is public by owner decision. Credit wherever they appear: **Map: Tensura by Lerfing (current, being replaced).**
- **No mod textures or structures.** The Tensura mod and the other mods are All Rights Reserved or restricted: never copy their textures, models or structure files. References only; say where you looked.
- **No tracing or copying** of official art, anime frames, other maps, skins from skin sites or other builds. Everything delivered is original; list references in the note.
- The new world map and all concept art, blueprints and skins made for this project are original work for Yasuke's non-commercial fan project; credit lines go in [`CREDITS.md`](../../CREDITS.md) (Claude adds them).
- Keep the repository small: JPEG or optimised PNG, concept art under 3 MB each, the whole knowledge pack stays under about 20 MB.
- No personal data (real names of players, accounts, emails) and no secrets, ever.

## 7. The first things to read for a task

| Task | Read |
|---|---|
| Draw the new world map | [world.md](world.md), [source-map/](source-map/README.md), [tasks.md](tasks.md) section 1 and 8 |
| Concept art of a place | the place page in [places/](places/), [art.md](art.md), the lore page it links |
| Design or improve a build | [builds.md](builds.md), the place page, [`design/lore/<id>.md`](../../design/lore/) |
| Lore, quests, NL | [tasks.md](tasks.md) sections 4 to 6, [world.md](world.md), the files named there |
| NPC skins | [art.md](art.md) section 4, [`docs/art/npc-skin-prompts.md`](../art/npc-skin-prompts.md) |
