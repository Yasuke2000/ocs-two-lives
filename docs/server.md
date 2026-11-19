# Test server

The staging server runs on Yasuke's homelab (Kubernetes, node3) from the `itzg/minecraft-server` image.
Its settings live in a private infrastructure repo, so they are listed here. To change one, open an
issue with the label `server` or ask Yasuke.

| Setting | Value |
|---|---|
| Address (testers) | `molecule-threefold.tun.ply.gg` (playit.gg tunnel) |
| Minecraft / NeoForge | 1.21.1 / 21.1.266 (pinned in `pack/pack.toml`) |
| World | `world-ttl` (reset 17/11/2026 for Two Lives) |
| Memory | 7 GB heap (pod limit 10 GiB), 2 CPU guaranteed |
| Max players | 15 |
| View / simulation distance | 16 / 8 chunks (Distant Horizons draws further) |
| Difficulty | hard |
| PvP | open everywhere, Life 1 included (owner decision 18/11/2026). Another player can end your only first life; killing players darkens karma (`player_kills` is a Chaos stat in `design/data/karma.toml`). The guide says so. |
| Whitelist | on — send Yasuke your Minecraft name |
| Spawn protection | off |
| Flight | allowed (Tensura flight skills and wings; off kicks players mid-air) |
| Pack | installed from `main` (`pack/pack.toml`) on every restart |

**Deploys:** a merge to `main` is picked up automatically when nobody is online; the bot tests then
run and the commit gets a ✅/❌ "ttl staging" status. Players online are never kicked for a deploy.

**Bug reports:** `/bug <text>` in game. Reports become GitHub issues (labels `bug`, `from-game`,
`triage`) once the server has a token; until then they are saved on the server in `ttl-reports/`.

## Access from a PC without SSH

`tools/server.sh` and the Python tools (`capture.py`, `verify_build.py`, `import_configs.py`, `import_schem.py`, via `tools/cluster.py`)
use `~/.kube/ocs-two-lives.yaml` when it exists: kubectl straight to the K3s API over Tailscale with the
ServiceAccount `ttl-operator`, which can only reach this namespace (pods, exec, logs, restarts). No SSH means no
Tailscale SSH re-checks. Without the file they fall back to SSH to the node. Ask Yasuke for the key; never commit it.

## Local testing

Staging is slow to iterate on: push → ttl-ops deploys only while nobody is online → `test-all` → status on GitHub.
Test on your own PC first, then push. Three tiers, fastest first:

| Step | Command | Time |
| --- | --- | --- |
| Offline checks before a push | `bash tools/check.sh` | validate + the fast unit tier + `node --check` on changed JS |
| Unit tests, quick tier | `bash tools/test_fast.sh` | ~7 s warm (the full suite is ~4 min) |
| Unit tests, everything | `bash tools/test_fast.sh --all` | ~45 s (one process per module) |
| In-game tests on a local server | `bash tools/local.sh up`, then `bash tools/local.sh test <name>` or `test all` | see below |

**Unit tiers.** Almost all of the ~4 minutes is the pure-Python NBT reader parsing the big structures. `test_fast.sh`
and `check.sh` set `TTL_FOOTPRINT_CACHE` (default `~/.cache/ocs-two-lives/footprints`), so `gen_data.read_footprint`
keeps each build's footprint keyed by the structure files' bytes and the reader's code: a changed slab is read again,
an unchanged one comes from the cache. The first run after many structures changed takes ~70 s. Tests marked
`@heavy` (`tests/tiers.py`: the full block-by-block loads of tempest and dwargon in `verify_build`, the lerfing CLI)
skip in the quick tier. `check.sh` runs them as well (`--all`) when blueprints, structure files or the structure
tools changed. `check.sh` also sets `TTL_STRUCTURE_CHECK_CACHE`: `build_structures.py --check` (inside validate.py,
it rebuilds every blueprint, ~3-4 minutes) remembers a pass under the hash of `blueprints/**` and the structure tools
plus the hashes of the files it compared, and is skipped while all of those are unchanged. The plain
`python -I -m unittest discover -s tests`, a plain `python tools/validate.py` and CI are unchanged and cache nothing.

**Opt-in pre-push hook** (one clone; all worktrees share it; skip once with `git push --no-verify`):

```bash
printf '#!/bin/sh\nexec bash tools/check.sh\n' > "$(git rev-parse --git-common-dir)/hooks/pre-push"
```

**Local server** (`tools/local.sh`, Git Bash on Windows; Linux/WSL work too). Needs Java 21 (found in
`~/.gradle/jdks` after a `mod/` build, or set `TTL_JAVA`), Python 3, packwiz and network for the first install.
Everything lives in `%LOCALAPPDATA%\ocs-two-lives\local-server` (`TTL_LOCAL_DIR`), never in git; `local.sh where`
prints it.

| Command | What |
| --- | --- |
| `up` | Installs NeoForge from `pack/pack.toml`, the pack's server side with packwiz-installer (what the itzg image does for `PACKWIZ_URL`, from a refreshed copy of your working tree, so uncommitted edits count), your `mod/` build of ttl-portals in place of the released jar, the `ttl-overrides` datapack into the world; starts and waits for RCON. The first boot waits until the start-up placements are done (`ttl build list` has nothing pending, ~15 min on a fresh world) and saves the world as snapshot `base`. Later `up`s only redo what changed (packwiz-installer when the mod list or versions changed, gradle when `mod/` changed; `TTL_LOCAL_FULL=1` forces both) |
| `sync` | Copies what changed in `pack/` since the last up/sync into the running server and applies it: `kubejs/server_scripts`, `kubejs/data`, `datapacks`, `config/ttl`, `config/ftbquests` → `/reload` (waits for "Reloaded with"; like `server.sh push-scripts`, so commands re-register); startup scripts or other config → restart; mods or `mod/` → full `up`. Prints new KubeJS/`[ttl]` errors and exits 1 on them |
| `test <name>` / `test all` | The same `tests/ingame/*.rcon` through the same runner as `tools/server.sh` (`tools/ingame.sh`), on one RCON connection (`tools/rcon.py --serve`), each command 2 game ticks after the previous one (`TTL_LOCAL_TICKS`; staging's kubectl exec takes ~3). Waits first while start-up builds are still pending. `test all` keeps each output in `test-out/` |
| `down`, `restart`, `status`, `logs [n]`, `follow`, `rcon "<cmd>"` | As in `server.sh`; the log of the run before the last start is `logs/previous.log` |
| `snapshot [name]`, `reset [name]` | Save the stopped world / put it back (default `base`). `stop` says whether the log has "All dimensions are saved" |

Same as staging: NeoForge version, server-side mods and configs, datapack, `world-ttl`, hard, simulation distance 8,
flight on, no whitelist, spawn protection 0, Aikar flags. Different on purpose: game and RCON bound to 127.0.0.1,
offline mode (join from the Prism instance at `localhost`), a random RCON password in `state/`, no Discord token
(Simple Discord Link stays offline; tests mute Discord anyway), no GitHub token (`/bug` saves to `ttl-reports/`),
BlueMap's web server on 127.0.0.1:8100, a fixed seed (`TTL_LOCAL_SEED`), heap 6 GB (`TTL_LOCAL_MEMORY`) and view
distance 8 (`TTL_LOCAL_VIEW`). Plan on ~8 GB of RAM for the Java process. Tests a local server cannot run are
listed in `ingame_skip_reason` in `local.sh` and print `skipped (<reason>)`; none are listed yet.

**Timings** (Yasuke's PC: 16 threads, 32 GB RAM; 19/11/2026, branch `local-up-wait`):

| Step | Time |
| --- | --- |
| `up`, cold (NeoForge + packwiz-installer + gradle + first boot) | 384 s, then ~15 min of start-up placements before snapshot `base` |
| `up`/`restart`, warm (nothing to reinstall) | 48-63 s (stop 6-9 s, start to "ready" ~43 s) |
| `snapshot base` (stop, copy 565 MB, start) | 62 s |
| `sync` of one server script (copy + `/reload` + error check) | ~4 s |
| `test <name>` | 16 s (`arrival`) to 40 s (`guide`) |
| `test all` (71 tests) | 1385 s (23 min), 70 ok; staging's run from a PC is ~27 min |

**Why the harness waits.** Two things staging gives for free: (1) every staging command is a `kubectl exec` (~0.17 s, 3
ticks), so work a script schedules a tick later (the Corridor after `kill`, the trials) is done before the next
command; locally a command takes ~1 ms, so `rcon.py --serve --ticks 2` waits 2 game ticks (one is not enough: a command
can run in the middle of a tick). (2) Staging's world placed its canon builds long ago; a fresh local world places
them one by one for ~15 min after start, and tests that place or expect a build (`build_repair`, `builds`,
`duel_liability`) queue behind them. `rcon.py` never sends a packet before the previous one is answered: Minecraft's
RCON reads one TCP chunk per request and drops the connection when two packets arrive together.

Known local difference: `guild_npcs` forceloads a box at staging's Blumund (corner -1086 65 -224); the local fixed seed
places Blumund at -1024 70 -120, so Fuze's stand is outside the box and the Fuze steps fail. The test needs the box
moved with the build (or read from `ttl build where blumund`).

A local pass is not the staging pass: after the merge, ttl-ops still deploys and runs `test-all` on staging (the
real map, real players' data, Discord). Use the local server to get there green the first time.

## Checking placed builds and landmarks

**Does a build transfer well?** `python tools/verify_build.py <name> --log` (or `tools/server.sh verify <name>`)
finds the placement line the script logged (`[ttl] tempest placed: corner X Y Z`, `[ttl] dwargon placed: corner …`,
`mortal spawn placed at y …`), forceloads the box, runs `/ttlcapture` over it, downloads the capture and compares
it block by block with `pack/kubejs/data/ttl/structure/<name>*.nbt` (slabs `<name>_0..n` stacked along z).
Give the corner yourself with `verify_build.py <name> <dimension> <x> <y> <z>`. It only counts positions the
structure defines (explicit air included) and treats what the game changes on its own as a match: fence, wall,
pane and redstone connections, stair shapes, power, leaf distance, waterlogging, snowy grass, crop growth, fluid
levels, grass/dirt and air variants. It prints the match %, mismatches per slab and the top mismatching block
pairs with world coordinates, and exits 1 below `--min` (default 98 %). It does not change the world (it removes
its capture file and only the forceloads it added). The comparison is unit-tested offline:
`python -I -m unittest discover -s tests`.

**Canon landmarks** (`design/data/landmarks.toml`, `life/landmarks.js`): Tensura's own structures (goblin,
lizardmen, orc and dwarf villages, a burnt tower, a giant ancient tree) placed with `/place structure` at
canon_regions.json landmarks, once, about 45 s after start (one at a time) and again after an overworld reset.
Log lines: `[ttl] landmark <name> placed: <structure> at X Y Z (…, box …)` or `could not be placed`.
Ops: `/ttl landmark list`, `/ttl landmark where <name>` (with a tp command), `/ttl landmark place <name|all>`
(places again; the old copy stays). Change a landmark or bump its `version` in the TOML, then
`python tools/gen_data.py`.
Finding places: `/locate place <id>` (op, vanilla `/locate` style, tab-completes every anchor id plus placed builds and landmarks without an anchor; recorded placement first, else the anchor) and `/ttl where <id>` for players (direction and rounded distance only; `life/locate.js`).

## Permissions

LuckPerms was removed on 18/11/2026: it breaks the /ttlbot test players; staff commands use vanilla op level 2.

## Web map (BlueMap)

BlueMap 5.7 (server-side only) renders two maps and serves them on port **8100**. Config: `pack/config/bluemap/`
(`core.conf`, `webserver.conf`, `webapp.conf`, `plugin.conf`, `storages/file.conf`; the two files in `maps/` are
generated).

| Map | Dimension | Area | Markers |
|---|---|---|---|
| `tensura` (Life 2) | `minecraft:overworld` of `world-ttl` | canon continent + 1,000 blocks of sea (x -10,088..5,912, z -6,680..5,448) | 22 region labels (shown when zoomed out), 43 canon landmarks |
| `mortal_realm` (Life 1) | `ttl:mortal_realm` | 3,000-block square around Wayfarer's Rest | Wayfarer's Rest |

**Credit.** The `tensura` map renders *Tensura by Lerfing* (giant trees by Paulzero); see `CREDITS.md`. Owner
decision 19/11/2026: the map **stays public after the import** although Lerfing's licence is still unknown; asking
Lerfing (and Paulzero) for permission is still Yasuke's TODO in `CREDITS.md`.

The Spirit Corridor, Mortal Nether and Mortal End are not mapped. `python tools/gen_map.py` rewrites the two map
files from `canon_regions.json` and `canon_map.txt` (`--check` tells if they are stale); the knobs (world name, sea
padding, Mortal radius, marker distances) are constants at the top of the script. Tempest and the Dwargon gate are
pinned at their built positions (0, 0) and (435, -1000) in `BUILT_AT`; the reference-map pixels would put them
about 100 and 490 blocks away. Live markers (nation claims, wars, events) are not written: they need BlueMap's
MarkerAPI from a script and are unverified.

**Before it works (owner decisions):**
1. `accept-download` in `core.conf` is **true** (owner, 18/11/2026): BlueMap downloads the Minecraft client jar
   (Mojang EULA) for vanilla textures.
2. The map is **public** (owner, 18/11/2026) at **https://map.daviddelporte.com**, no login. It shows terrain and
   builds (bases included, on an open-PvP server) but not player positions (`plugin.conf`:
   `live-player-markers: false`; keep it off). Route: Cloudflare → the homelab's cloudflared tunnel → Service
   `mc-bluemap` (ClusterIP, port 80 → 8100 on the mc pod) in namespace `ocs-two-lives`; the namespace's
   NetworkPolicy admits port 8100 only from the cloudflared namespace. Service and policy are in the Homelab repo
   (`apps/ocs-two-lives/manifests/server.yaml`, `network-policies.yaml`). The tunnel is managed in Cloudflare, not
   in git, so Yasuke adds once (Homelab `docs/cloudflared-tunnel.md`): a proxied CNAME `map` →
   `<tunnel id>.cfargotunnel.com`, and a tunnel ingress rule `map.daviddelporte.com` →
   `http://mc-bluemap.ocs-two-lives.svc.cluster.local:80` **before** the `*.daviddelporte.com` wildcard (without
   it the host lands on the wildcard's app, not the map). The mc container does not declare `containerPort: 8100`
   yet: that would change the pod template and restart the server; it is only informational and comes with the
   next change that restarts the server anyway.

**Load:** one render thread at low priority (`render-thread-count: 1`), inside the game's JVM (7 GB heap, pod limit
10 GiB): watch `neoforge tps` and the pod memory during the first full render, which can take hours and a few GB
of tiles in `/data/bluemap/web/maps` for a fully explored continent. Render only while few people are online if
TPS drops (`bluemap stop` / `bluemap start`, `bluemap freeze <map>`); `bluemap` alone shows the state.
Tiles of chunks Distant Horizons or pregeneration created count as explored; `min-inhabited-time` in a map file
would skip them, at the price of leaving unvisited canon terrain out.

Not verified without the server: the `render-mask` box keys and marker `min-distance`/`max-distance` units, that
`world: "world-ttl"` plus the dimension ids `minecraft:overworld` and `ttl:mortal_realm` resolve on NeoForge, and
that custom-block textures of Tensura render. Look at `tools/server.sh logs | grep -i bluemap` after the first start.

## Night pregeneration (Distant Horizons)

The Tensura continent is pregenerated **at night** (owner decision 18/11/2026) by ttl-ops (Homelab repo,
`apps/ocs-two-lives/manifests/ops.yaml`, function `night_pregen`), with Distant Horizons' own generator.
**Chunky stays banned**: DH 3.3.3 crashes every server start with it (`design/decisions.md`, 18/11/2026).

| | |
|---|---|
| When | 23:00–07:00 Europe/Brussels (summer time computed in the script), once nobody has been online for 5 minutes (test bots don't count: the same "humans online" check as deploys, `tools/server.sh who`) |
| What | `dh config generation.chunkMode INTERNAL_SERVER` (real chunks, saved to the region files, structures included), `dh config common.threadPreset BALANCED`, then `dh pregen start minecraft:overworld 64 256 520`: the centre of Lerfing's imported tiles (x −8064..8192, z −6016..6528); 520 chunks = 8,320 blocks covers every tile (populate and DH LODs of the pre-made terrain) and the generated ocean ring north and south; the vanilla lands beyond are never pregenerated. Was `-2088 -616 450` on the generated continent |
| Pause | `dh pregen stop` as soon as a human joins, at 07:00, before a deploy and before the bot tests, and when `/data` is 85 % full. The daytime settings are put back (`generation.chunkMode FEATURES`, `threading.numberOfThreads 4`, `threading.threadRunTimeRatio 0.75`, as in `pack/config/DistantHorizons.toml`) |
| Resume | DH keeps no pregen state over a stop or a restart: the next start walks the same spiral from the centre and skips the sections it already generated, so stop + start works as pause + resume (the % climbs fast through the done part) |
| Discord (#server-log, the ttl-ops webhook) | started (once a night), paused (why, with progress; no player names), progress once an hour, complete, disk full, crash |
| Safety | a server crash while it runs stops it for the rest of the night; so do 3 runs that end on their own |
| Done | at ≥ 99 % it writes `/data/ttl-pregen.done` (the spec) and stops for good. Delete that file to pregenerate again, e.g. after an overworld reset |

`dh pregen status` answers `Generated radius: <r> / 520 chunks (<n> cps, <p>%), ETA: <t>` while it runs and
`Pregen is not running` otherwise; DH also logs progress in the server console. Knobs are env vars on the ttl-ops
Deployment: `PREGEN_ENABLED` (`0` = ttl-ops leaves DH alone, for a manual pregen), `PREGEN_DIM`, `PREGEN_X`,
`PREGEN_Z`, `PREGEN_RADIUS`, `PREGEN_THREADS`, `PREGEN_MAX_DISK`.

Watch during the first nights: TPS and pod memory (INTERNAL_SERVER loads real chunks in the game's JVM; heap 8G,
limit 12Gi), the size of `world-ttl` on the volume (60 Gi with the Homelab PR for Lerfing's map; the populated import is
8–9.5 GB of region files, plus the DH database and BlueMap tiles), and the Longhorn backup size. BlueMap renders the new chunks too.

Not verified on the server yet: that `common.threadPreset` (a client-side entry in DH 3.3.3) can be set on a
dedicated server, that the status line keeps that wording and a `.` decimal on the server's locale, and how fast it
goes. Command syntax, the config key names and the status/stop messages are taken from the DH 3.3.3 jar.

## Life 2 arrival and the Jura rings

**Life 2 arrival and the Jura rings** (`design/data/arrival.toml`, `life/arrival.js`, J `zones` in
`canon_regions.json`): Jura's biomes form rings (safe rim along the border, dark-forest middle, ancient-forest core
around Tempest) because Tensura gives dark_forest +1,500 and ancient_forest +19,500 area magicule. Souls are reborn
on the rim, on the road to the Dwargon gate; that point is also the world spawn (and so the respawn point of a Life 2
soul). The log says `[ttl] arrival grounded at X Y Z` about 20 s after the first start with it. Ops: `/ttl arrival`
(where it is), `/ttlmap <x> <z>` and `/ttlregion <player>` (name the ring and the patch shift). Only chunks that are
not generated yet follow the rings; after changing them on a live world use a world reset of the overworld.
Magicule poison is refused for everyone who is not in Life 2 (`life/mortal_immunity.js`).

## Site biomes

Every canon build and landmark of the Tensura overworld has a **site** (`sites` in
`pack/config/ttl/canon_regions.json`, mod classes `CanonSites` and `CanonSiteTerrain`): a centre, a radius and a fade,
a biome list and a terrain intent, so the ground and the biome round a build fit its style and lore (Dwargon on a
plain, Laura in jungle, the Frost Palace on a snowfield). Owner decision of 19/11/2026 (`design/decisions.md`).

- **Biomes.** Inside a site's biome edge (half-way through the fade, wobbled per site so it is an organic blob, not a
  circle) its own list replaces the nation palette for land and peaks; a `flat` site also replaces water, shores and
  cave biomes less than 16 blocks below its ground. A site without `biomes` keeps the nation's (Tempest and Rigurd's village keep
  Jura's rings: the deadly core is an owner decision). The first listed site wins where two overlap.
- **Terrain.** `keep`: biomes only (Jia's mountain, Raja's lake, the lizardmen's marsh). `flat`: the ground is levelled
  to `ground` (y of the first air block; >= 64 so the sea does not flood it) over the radius and blended back to the
  natural terrain over the fade; the aquifers see the same surface, and the column under it is pulled solid (raised
  ground never floats; noise caves under the middle fill up, carver caves and ores stay).
  `lowland`, `hills`, `mountain`: climate presets (erosion 0.5; erosion -0.1; continentalness 0.75, erosion -0.9,
  ridges 0.62) that make vanilla build that landform; `erosion`, `continents`, `ridges` in a site override them.
- **Outside every site nothing changes**, to the bit (the CanonGrid self-check proves it), so a site only moves the
  land round its build.
- **Only new chunks.** Like the palettes, sites shape chunks that are not generated yet. `/fillbiome` could repaint the
  biome of an old area, but a mountain stays a mountain: terrain shape only changes when the chunks regenerate. The
  overworld is reset after this change instead (players had built nothing; runbook in `docs/HANDOFF.md`).
- **Deploy order.** `noise_settings/overworld.json` and `density_function/overworld/ridges.json` name
  `ttl:canon_sites` and the canon_map channel `ridges`, which only ttl-portals 0.8.3+ knows: an older mod cannot load
  the overworld. Release the mod (`tools/release_mod.py`) on the branch **before** these files reach `main`.
- **A new build.** `tests/test_canon_sites.py` fails until the build has a site with its name, centred on the build's
  x/z, with a radius that covers its box + margin (`flat`) or box + margin + search (other terrains). Pick the biome
  and terrain from the build's lore file and say why in `why`.
- **Check.** `/ttlmap <x> <z>` lists the sites that reach a column (name, terrain, distance, weight) and prints the
  surface height and the biome the generator would make there, without generating the chunk: right after a deploy,
  `/ttlmap 435 -1000` must say `site 'dwargon' (flat y72)`, `surface y72` and `minecraft:plains`. Self-check:
  `java -cp "mod/build/classes/java/main;<gson.jar>" com.yasuke.ttl.world.CanonGrid pack/config/ttl/canon_map.txt
  pack/config/ttl/canon_regions.json 271 -624` (after `gradlew build`; `:` instead of `;` on Linux) ends with
  `canon self-check passed`.
- **BlueMap after a terrain change.** Whole map (after a reset): `bluemap purge tensura`, then `bluemap force-update
  tensura`. One changed area: `bluemap force-update tensura <x> <z> <radius>` (radius in blocks; for a site, its
  radius + fade + 100). `bluemap` shows the queue; render only while few people are online.

## World import (Lerfing's map, `ttl-import.txt`)

Lerfing's Tensura map becomes the overworld (`design/architecture/lerfing-import.md`, owner decisions of 19/11/2026).
ttl-portals 0.9.0 swaps it in at server start from a marker, the way `ttl-reset.txt` resets a dimension.

**The marker.** `/data/world-ttl/ttl-import.txt`, one line (`#` lines are comments):

```
minecraft:overworld import 800
```

`<dimension id> <folder> [<region file count>]`. The folder holds `region/` (and `entities/`, `poi/` if the prepared
world has them). A relative folder is looked up in the world folder first, then next to it (`import` = `/data/import`);
an absolute path is taken as is. The count is optional, but give it: the import is refused unless exactly that many
`r.<x>.<z>.mca` files are there (800 for Lerfing's inner tiles), which catches an incomplete upload.

**Checks before anything moves** (any failure = `[ttl] world import REFUSED ...`, nothing moved, the marker stays,
the old world starts as it was): the marker parses; the source exists, has a `region/` folder and is not the world, a
part of it, or inside `ttl-backup`; the region files are named `r.<x>.<z>.mca`, each at least the 8 KiB header, every
header entry points inside its file; in every file the first and last chunk are decompressed and read: the `Status`
must be one Minecraft 1.21.1 knows (an unknown one such as 1.18's `liquid_carvers` loads as EMPTY and the chunk would
be **regenerated over Lerfing's terrain**; `tools/lerfing/import.py` renames it to `minecraft:carvers`), the
`DataVersion` not newer than the game's (3955), and `xPos`/`zPos` inside the file's region. The log then says
`[ttl] world import: source OK: 800 region files (6.59 GB), 796544 chunks; 1600 sampled: statuses {...}, DataVersion 2860..2860`.

**The swap.** A journal `/data/world-ttl/ttl-import.journal` is written; the old overworld (`region`, `entities`,
`poi`, `data/DistantHorizons*`) moves to `world-ttl/ttl-backup/<time>/minecraft/overworld/` (nothing is deleted); the
source's `region` (+ `entities`/`poi`) moves into the world folder. On the same volume these are renames (seconds,
no extra disk); from another volume it is a copy, verified file by file (count and sizes), and the source is kept.
The marker moves into the backup folder, the journal is deleted, and the log says
`[ttl] world import: minecraft:overworld from import; old terrain in ttl-backup/<time> (moved)`. Once the server has
started, `/ttl worldreset minecraft:overworld` runs, so the scripts re-place Tempest, Dwargon, the landmarks, the
builds and the arrival, and move players on login, as after a reset. A `ttl-reset.txt` that also names the overworld
skips it (warning in the log); other dimensions in it are reset as usual.

**When it goes wrong.**

| Log / symptom | State | What to do |
| --- | --- | --- |
| `world import REFUSED, nothing was moved ...: <reason>` | old world running, marker kept | fix the reason (upload, count, run the import tool again), restart |
| `world import FAILED and was undone, the old world starts` | every step undone in reverse order, marker kept | read the reason (disk full, permissions), fix, restart |
| server stops at start: `ttl-import.journal exists: a world import did not finish` | the JVM died mid-swap or the undo itself failed; the server refuses to start on a half-swapped world | from a debug pod on the volume: read the journal (source, backup, dimension), put `region`/`entities`/`poi` and `DistantHorizons*` back from `ttl-backup/<time>/minecraft/overworld/` (or finish the swap by hand), delete the journal, scale to 1 |
| import done but wrong (the owner does not want it) | old world in `ttl-backup/<time>/` | **Rollback** below |

**Runbook: the fast path** (lead). It runs any time nobody is online: no night, no scale to 0. Owner rule: the
import is pre-made terrain, and only the **pregen** waits for the night. The full plan is in the design doc §6.3.

0. **Main is ready.** ttl-portals 0.9.0 is released (`python tools/release_mod.py --bump minor` → `mod-v0.9.0`).
   `main` carries it together with the Lerfing grid, `sea_level` 65, the noise settings without `ttl:canon_sites`
   and the anchor table (`generated/anchors.js`, WP-L4), so the placers put Tempest, Dwargon and the builds at
   Lerfing's coordinates. `tools/import_world.sh` reads `main` from GitHub and writes no marker until all of this is
   there, because the restart installs `main` and an older mod ignores the marker. ttl-ops deploys `main` by itself
   when nobody is online.
1. **Offline** (once): `python -I tools/lerfing/import.py "<zip>" --out <dir>`, then `... --out <dir> --verify`.
   `<dir>/report.json` must show 796,544 chunks, only `minecraft:carvers` and no Nether/End biomes. `<dir>/sha256.txt`
   lists the 800 files.
2. **Disk.** On 19/11/2026 the 30 Gi volume had 22.05 GB used and 9.46 GB free. The upload fits and leaves about
   2.9 GB (90 % used). That is enough to look at the map, but the night pregen stays off above 85 %, and the first
   boot grows every chunk it loads (DFU upgrade and populate: +20–40 %). Before the import, merge the Homelab PR
   that grows `mc-data` to 60 Gi (`df -h /data` in the pod then shows the new size), or delete old
   `ttl-backup/<time>/` folders (8.0 GB on 19/11; the NAS backup keeps them).
3. **Upload and arm.** Run `bash tools/import_world.sh --dry-run` first: it checks, plans and measures the speed,
   and writes nothing. Then run `bash tools/import_world.sh`:
   - it refuses while a human is online, and checks the free space;
   - it sends the region files to `/data/import/region` with tar over `kubectl exec`, in batches of 25; after a break,
     run it again and it sends only what is missing or short;
   - it checks every file's sha256 on the pod and sends bad files again;
   - it writes `/data/world-ttl/ttl-import.txt` = `minecraft:overworld import 800` and removes `/data/ttl-pregen.done`.

   Measured on 19/11/2026: 8.3 MB/s from Yasuke's PC, so about 13–14 minutes for 6.59 GB, plus about a minute of
   sha256. The server keeps running meanwhile, because the upload does not go into the world. `--no-marker` uploads
   and checks only. Exit 4 means uploaded and verified, but `main` is not ready (step 0): run it again later; it
   skips the upload.
4. **Restart through the normal deploy:** `bash tools/server.sh deploy`. It refuses while a human is online and
   restarts until `main`'s pack is installed. When `main` has a pack that ttl-ops has not deployed yet, ttl-ops makes
   the same restart within a minute and runs `test-all` after it. The safety net is the old terrain, which the
   marker moves into `ttl-backup`, and the nightly Longhorn snapshot. A manual snapshot (Yasuke, Longhorn UI) is
   optional.
5. **Watch the start:** `bash tools/server.sh follow | grep -E '\[ttl\] (world import|world reset|arrival|tempest|dwargon|landmark|chunks)'`.
   The lines come in this order:
   - `[ttl] world import: checking /data/import for minecraft:overworld`
   - `[ttl] world import: source OK: 800 region files (6.59 GB), 796544 chunks; ...`
   - `[ttl] world import: minecraft:overworld from import; old terrain in ttl-backup/<time> (moved); /ttl worldreset minecraft:overworld follows once the server has started`
   - the placers: `[ttl] arrival grounded at 1660 ... -100`, `tempest placed`, `dwargon placed`, the landmarks and
     builds, `[ttl] chunks: holding ...`, and no watchdog.

   On `REFUSED`, `FAILED and was undone`, or a start that stops on `ttl-import.journal exists`, see the table above.
6. **First checks.**
   - `ttlmap 1720 900` says `imported chunk: stored biome ...` (Tempest's placer loads that chunk).
   - `execute in minecraft:overworld if block -453 73 979 minecraft:chest` succeeds: Lerfing's spawn chest is still
     there, so no proto chunk was regenerated.
   - `/ttl world expect continent 1720 900 yes` and `... 9000 0 no` pass.
   - `ls /data/world-ttl/data/DistantHorizons.sqlite*` shows only a fresh, small file.
7. `bluemap purge tensura`, then `bluemap force-update tensura` (while few people are online). Then `/ttl build list`,
   `/ttl landmark list` and `verify_build.py`; `MSYS2_ARG_CONV_EXCL=/data bash tools/server.sh test-all` must give
   0 failing.
8. **Play at once; pregen at night.** The imported terrain is there from the first second. A chunk is DFU-upgraded and
   populated (ores, plants, light) the first time a player loads it, so fresh ground can hitch briefly. The night
   pregen (ttl-ops, 23:00–07:00, nobody online, under 85 % disk) populates the rest of the imported tiles, builds the
   DH LODs and generates the ocean ring north and south (`64 256 520`, see "Night pregeneration"). It never runs
   during the day (owner rule).
9. Delete `ttl-backup/<time>/` from the volume only after the owner has looked at the map (the NAS backup keeps it).
   Delete `/data/import/` once it is empty: the swap moves `region` out, and `sha256.txt` stays.

**Rollback** (the owner does not want the import). The marker kept the old overworld whole in
`world-ttl/ttl-backup/<time>/minecraft/overworld/` (`region`, `entities`, `poi`, `DistantHorizons.sqlite*`) and moved
itself to `ttl-backup/<time>/ttl-import.txt`, so the newest folder that holds that file is the import's. The way back
uses the same marker. It needs nobody online, but no scale to 0 and no debug pod:

1. **Data first.** On `main`, revert the Lerfing data (grid, `sea_level`, anchors and quests: the `lerfing-import`
   merge) but **keep ttl-portals 0.9.0**, because the marker needs it. Let ttl-ops deploy it, or run
   `tools/server.sh deploy`. For a moment the server runs the old data on Lerfing's terrain; whatever the placers do
   there goes away with that terrain in step 3. Do not write the rollback marker before this deploy: raw GitHub can
   lag, and if a restart installed the Lerfing pack again, the old terrain would come back with Lerfing's anchors.
2. **Move the old terrain out of the backup.** The marker refuses a source inside `ttl-backup`. The server never
   reads `ttl-backup`, so the move is safe while it runs, and on the same volume it is a rename that needs no extra
   disk:
   ```
   kubectl ... exec deploy/mc -- sh -c 'B=/data/world-ttl/ttl-backup/<time>/minecraft/overworld; mkdir /data/rollback &&
     mv $B/region $B/entities $B/poi /data/rollback/ && ls /data/rollback/region | wc -l'
   ```
3. **Arm and restart.** Write `echo "minecraft:overworld rollback <that count>" > /data/world-ttl/ttl-import.txt`
   (same `kubectl exec`), then run `bash tools/server.sh deploy`. The log says `world import: minecraft:overworld
   from rollback; old terrain in ttl-backup/<new time> (moved)`. Lerfing's map is now the backup and the old world is
   back. `/ttl worldreset` places the builds of the reverted data again, on the spots where they already stand, and
   moves players to spawn when they log in.
4. The old DH database stays in the first backup folder. It can only go back while the server is stopped: from a
   debug pod, move `DistantHorizons.sqlite*` into `world-ttl/data/`. Otherwise DH rebuilds its LODs at the next night
   pregen. Then `bluemap purge tensura` and `bluemap force-update tensura`.
5. To roll back the whole volume instead (this loses everything since the snapshot), restore the pre-import Longhorn
   snapshot or backup: see "Backups and restore" below.

**Outside the import.** Nothing of ours generates inside the imported area: its chunks exist, and Minecraft never
regenerates an existing chunk. Beyond it the generator makes the canon ring: `canon_map.txt` is Lerfing's land mask,
and the signed distance from it makes deep ocean at the seam (the self-check asserts continentalness < −0.455 along
all four edges of `lerfing.inner`), held for `ring` blocks from the land's bounding box and blended into vanilla over
`blend` (2000 / 800 in `canon_regions.json`). `sea_level` is 65 in `noise_settings/overworld.json` (was 63), so the
generated sea's top water block is y 64 like Lerfing's: no one-block water step along the seam. The per-build `sites`
are gone from the Lerfing grid (the mod treats a missing `sites` key as none), and the noise settings no longer wrap
`final_density` in `ttl:canon_sites` (the type stays registered, so an older pack still loads with 0.9.0).
`/ttlmap <x> <z>` inside `lerfing.inner` reports the grid letter and the **stored** biome of the loaded chunk
(`imported, not loaded` otherwise) instead of the generator's opinion; outside it works as before. `/ttlregion
<player>` on the import names Jura's ring from the stored biome (`tensura:ancient_forest` core, `minecraft:dark_forest`
dark band, anything else the safe rim).

**Self-checks** (after `gradlew build`; JDK 21; `:` instead of `;` on Linux):
`java -cp mod/build/classes/java/main com.yasuke.ttl.world.WorldImport` (synthetic region files: marker parsing,
every refusal, a full swap, the undo after an injected failure, a failed undo keeping the journal, the cross-volume
copy, a non-overworld dimension) ends with `world import self-check passed`. `java -cp
"mod/build/classes/java/main;<gson.jar>" com.yasuke.ttl.world.CanonGrid pack/config/ttl/canon_map.txt
pack/config/ttl/canon_regions.json 1660 -100 design/data/anchors.toml` understands both formats: with a `lerfing`
block it checks the import box against the grid, the deep-ocean seam, no sites, Jura's radius rings round Tempest, the
arrival in the safe outer ring, and every landmark `at` and anchor on the continent (land, lake, river or coastal
water); without one it runs the old site and depth-rim checks.

## Canon builds

Our own builds on canon spots (a town square, a gate, a hall: `blueprints/<name>.py`) are placed by
`pack/kubejs/server_scripts/ttl/life/builds.js` from one file each, `design/builds/<name>.toml`
(`_example.toml` documents every field; files starting with `_` are ignored). `python tools/gen_data.py` reads
them, turns `landmark = "<name in canon_regions.json>"` into world x/z (the same `(ref - origin) x width / 2570`
as the landmarks), checks the structure files and the anchor (it fails on an unknown landmark, a missing
structure or an anchor outside the structure) and writes `TtlData.builds` plus the per-column ground data of the
structure files (`generated/builds.js`).

**When.** About 90 s after start, one build at a time with a 5 s gap, after Tempest, Dwargon and the landmarks.
**Chunks.** Every placer (Tempest, Dwargon, the arrival, landmarks, builds) holds its area with chunk tickets
(`life/chunk_hold.js`, `TtlChunks`), not `forceload add`: the chunks load and generate in the background and the
placer starts once every one of them is FULL (at most 10 minutes; otherwise it is not placed and counts as a failed
start). `forceload add` loads (on a fresh world: generates) every chunk synchronously in that one tick: 121 new chunks
took 8.9 s on staging, and a landmark area holds 200-625, so a reset boot ran 10-20 s ticks until the watchdog killed
the server (decisions.md, 19/11/2026). `/ttl chunks hold <x0> <z0> <x1> <z1>` tries it on an overworld rectangle
(the log says when it is ready).
A build is placed once: `ttl.build.<name>.version` in the server's persistentData holds the placed `version`.
- **Version.** Bump `version` in the TOML and regenerate: the next start places the new version over the old one
  at the same corner (blocks of the old version that the new one does not overwrite stay). Changing x/z, `ground`,
  `y`, `dimension` or `anchor` instead surveys a new spot and leaves the old copy where it was.
- **World reset.** `life/world_reset.js` calls `TtlBuilds.reset(server, ids)` (the same signal as
  `TtlLandmarks.reset`): every build whose `dimension` is among the reset ones loses its record and is placed again
  on the new terrain, with a new survey.
- **Failure.** A build that cannot be placed (no dry spot, heightmaps missing, a command error) logs an error and is
  tried again on the next start, 3 starts in a row at most; `/ttl build place <name>` tries again at once.

**Where.** `ground = "fixed"`: x/z at world `y`. `ground = "survey"` (default): the flattest dry spot within
`search` blocks of x/z. Candidates lie on a grid (4 to 16 blocks apart); every column of the build is sampled
(heightmaps, trees and plants skipped); a spot with any lava or void, more than `max_wet` (default 10 %) of its
columns over water or ice, or within 24 blocks (on top of its own `margin`) of Tempest, Dwargon, a placed landmark or
another build, is out; the
rest are scored by 2 x the mean deviation from the median ground height + half the p10-p90 spread + distance/16 +
20 x the water share, and the anchor goes on the median. (Water is a cost, not a veto: a 120-block box nearly always
crosses a stream or pond, and the terrain fit fills those columns from the bed.) The log line
`[ttl] build <name>: surveyed N spots ... least water P %; best at X Z, D blocks from the canon point ...` says what
was found; when nothing qualifies, the least water seen tells whether to raise `search` or `max_wet`. A placed landmark
counts with the bounding box `life/landmarks.js` recorded for its structure (`/ttl landmark where <name>` shows it; the
square of its `reach` round its spot when the start could not be registered). `beside = "<landmark>"` (Treyni's shrine
beside the grove's tree) drops the 24 blocks for that one landmark: only the build's own terrain `margin` stays off its
box, so the build lands right next to it. Setting or changing `beside` surveys a new spot, like changing x/z. The canon map
(`canon_map.txt`) does not predict real lakes: Milim's land round the Forgotten Dragon landmark is lakes at sea level.

**Terrain.** Like Tempest and Dwargon: the real terrain is read before placing; under every column that has blocks
the gap down to the terrain is filled (dirt, stone deeper down; sand or red sand over sandstone in a desert; over a
stream or pond from its bed, so no dirt bridges over water), so nothing floats; with `clear_above` everything above the highest block of the column (trees, hills) is cleared; round
the box `margin` columns get a 1:1 earth skirt (grass on top) and a 1:1 cut into hills. Void columns (the Spirit
Corridor) are left alone. Put explicit air into the blueprint wherever the inside must stay open: the placer only
fills under the lowest and clears above the highest block of a column.

**Terrain repair** (`life/repair.js`, shared by `builds.js`, `tempest.js` and `dwargon.js`). The fit above works from
heightmaps read before the build went in, so it misses what lies under an overhang, a closed cave roof, and the old
terrain in box columns the blueprint leaves undefined (after the 19/11 reset all of it was repaired by hand). After
the fit and before the second slab pass the repair reads the real blocks and fixes, deterministically:
- *Foundation*: under every box column the build defines (from its lowest defined block, explicit air included:
  `bottom` in the footprint), every air, water, lava, fire or plant cell in the `repair_depth` blocks below becomes
  ground (dirt in the 3 cells under the build, stone deeper, deepslate under y 0): caves, sinkholes, a ravine running
  under the edge. A gap that runs on below the depth is closed down to the depth when there is ground below it; a
  column with nothing solid under it (a void dimension, a floating island) is left alone; nothing is placed at or
  above the build's lowest block.
- *Undefined columns* (the blueprint holds no block there): the ground layer is continued at the ground height (the
  block under the anchor), with the nearest defined column's grass, path or sand at that height (else the site's top
  block) and the same fill below: no ditches. Bare rock at that height is covered; nothing above it is touched.
- *Ring* of `repair_margin` columns (square): the surface is raised to `max(1:1 skirt, min(ground height, closing))`,
  where the closing (max then min over a 9 x 9 window, box columns counted at the ground height) is used only where it
  lies 3 or more above the surface: pits, crevices, slits and ravine edges up to ~8 wide fill to their rim with grass
  on top, gentle dips, hills, wide valleys and lakes keep their shape. A gap within 3 blocks under the surface (a cave
  mouth, an overhang, the lip of a ravine) is filled to its floor. Water in the ring that touches the box (through ring
  water) is filled up to its surface, so a bank holds the water beyond the ring; other water is kept, and
  `repair_keep_water = true` (Raja, on its lake) keeps every water block. Lava is filled up to its surface below the
  ground height; lava above it and fire become air.
- *Cost*: the planner reads blocks only inside the area the placer already forceloaded (it never forceloads or loads a
  chunk itself; the area grows to `max(margin, repair_margin) + 2`), every cell in the first 8 under the build and
  every other cell deeper (~30 reads per box column at depth 48). Planning and the merged `fill` commands (boxes of at
  most 32768 blocks) run 15 ms per tick at most (200 commands), so a 120 x 120 build takes some seconds of ticks, not
  one long tick. Log: `[ttl] build <name>: repaired N foundation, M skirt, K lava (F fills, T ticks, ms; depth, ring;
  D gaps run deeper, U columns not loaded)` (cells; K counts lava and fire; `build tempest` / `build dwargon` for the
  settlements). The counts are kept in `ttl.build.<name>.repair` (`ttl.tempest.repair`, `ttl.dwargon.repair`).
- *Knobs* (TOML, `gen_data` checks them): `repair = false` turns it off (Walpurgis Hall and the Spirit Dwelling, in
  their own dimensions, are placed 1:1), `repair_depth` (default 48, 1..96), `repair_margin` (default 8, 0..16),
  `repair_keep_water` (default false). Tempest and Dwargon always repair, depth 48, over their footprint margin;
  Dwargon's empty box columns with a talus value count as ring, the others as plain ground at the road level.
  Jigsaw landmarks (`landmarks.js`) are not repaired.
- *Tests*: `tests/build_repair.js` (offline, synthetic worlds: cave and lava under the box, a ravine under the edge,
  overhang, pit, lava pool and fire, undefined columns, water touching the box, a kept-water site, void, depth),
  `tests/ingame/build_repair.rcon` (digs a cave, a slit, a lava pool, a water pocket, a cave mouth and a pit under and
  round `test_hut` on a patch of ground in the Spirit Corridor, places it again with force, checks the blocks with
  `/ttl build expect test_hut cell <x> <y> <z> <solid|air|water|lava|fire|soft|block id>` and
  `/ttl build expect test_hut repaired <foundation> <skirt> <lava>`, then removes the patch).
- *Not repaired*: an existing copy (the repair runs when a build is placed: a world reset, a version bump or
  `/ttl build place <name> force`), and a gap 1 cell high deeper than 8 under the build.

**Dry builds.** `place template` keeps the water of the old terrain: a stair, slab or wall set on a flooded cell comes out waterlogged and feeds a puddle for good. A build cut below the water table sets `dry = true` in its TOML (Amrita) and the placer drains the box (`fill ... air replace minecraft:water`) before the first pass. It cannot repair an old copy (its waterlogged blocks keep their water): `verify_build.py` shows them as `air -> water` inside the build; set those blocks again with `waterlogged=false` and drain the box by hand.

**Log lines.** One per build when done, the format `tools/verify_build.py <name> --log` reads:
`[ttl] <name> placed: corner X Y Z, anchor at x y z (version N, <how>, terrain done)` (`terrain FAILED` when a
terrain command failed: not recorded, tried again). `corner` is the structure's 0,0,0 (for slabs: of the first
one). Builds outside the overworld: `verify_build.py <name> --log --dimension <dim>`. Failures:
`[ttl] build <name>: not placed (<why>)`.

**Ops** (permission 2): `/ttl build list` (state of every build), `/ttl build where <name>` (spot, worked area, a
tp command), `/ttl build place <name|all>` (builds that are not at their current version yet),
`/ttl build place <name|all> force` (again, at the recorded spot), `/ttl build expect <name> placed` (prints
`ttl: ...` when the placed version is not the TOML's), `/ttl build expect <name> repaired <f> <s> <l>` and
`/ttl build expect <name> cell <x> <y> <z> <kind>` (terrain repair, above). `/ttl build <blueprint>` (a build at your feet) still works.
A player who walks into a placed build for the first time (per version) sees its `title`. Test:
`tools/server.sh test builds` (`test_hut`, a 5x5 hut in the Spirit Corridor; delete `design/builds/test_hut.toml`
and `blueprints/test_hut.py` when the placer is trusted).

## Before launch: what the tests leave behind

`tools/server.sh test-all` runs every `tests/ingame/*.rcon` against the live world; the bots are removed at the end,
but a few server-wide facts are changed by the tests and stay. None of it is visible to players except the era,
and all of it is harmless for a test world; go through this list once on the world that players start on.
Tests never post to Discord: `server.sh test|test-all` sets `/ttl discord mute on` for the run (and `off` after it),
and `TtlDiscord.post` also drops every line while a test bot is online. `/ttl discord mute status` tells which.
Era changes themselves announce nothing while the test ceiling (`registry legendcap`) is in force or when run `silent`.

| Left behind by | What | Undo |
|---|---|---|
| `legendary`, `absorb` | The era: both tests save the era state first (`/ttl era testmark`), advance it silently (`era next silent`) and put it back at the end (`era testrestore`); a run that broke off leaves the era advanced and the mark (`ttl.era.testmark`) behind | `/ttl era testrestore`, or `/ttl era reset` (back to era 1, silent, clears titles, archive, the slot ledger and the mark); `/ttl era set <n> silent` corrects the number alone |
| `legendary`, `absorb` | `ttl.reg.testcaps` (Legendary ceiling for tests) if a run broke off before `legendcap reset` | `/ttl registry legendcap reset` |
| `legendary`, `absorb`, `registry*`, `events` | Registry history (`/ttl registry history <skill>`), names and last-seen entries for bot UUIDs; the holder records themselves are freed by `ttl reset <bot>` | `/ttl reconcile <player>` for a stale holder; the history ring is capped and bots do not count anywhere |
| `bosses`, `story`, `wild` | Boss cooldowns (defeat stamps `ttl.boss.lastkill` (player and server mirror), arena gaps `ttl.boss.arena`, the arena queue `ttl.boss.queue`): cleared by `bosses.rcon` itself; a run that broke off leaves them | `/ttl boss cooldown clear all`; `/ttl boss abort` removes a boss left out; `/ttl boss testparty clear` |
| `bosses`, `karma`, `guild` | Scoreboard entries for bot names (`ttl.b.*`, `ttl.k.*`, `ttl.g.*`, `ttl.bounty`, `ttl.rep.*`) | `scoreboard players reset TtlBot*` is not supported by name pattern: `scoreboard players reset <bot>` per name, or ignore (bots never show) |
| `story`, `party`, `rep`, `nations` | Story event ring (`ttl.story.log`), reputation ring log (`ttl.rep.log`) with bot entries; `ttl.story.parties` / `ttl.party.roster` rows for bot FTB teams | Rings are capped and bot rows never post; `/ttl party poll` and `/ttl nation sync` re-read FTB Teams (bot rows stay keyed by team id, harmless) |
| `party`, `nations` | FTB Teams: a personal team per bot that ever joined (FTB Teams world data); every test party is left by its members at the end, a run that broke off leaves `PrtyTest` / `TtlBotNatParty*` | `ftbteams party leave` as the bot (spawn it again with `/ttlbot spawn <name>`) or remove the bot's team from the FTB Teams data while the server is down |
| `nations` | A nation record (`ttl.nations`) if the run broke off before `dissolve`; 100 bonus renown on NatA/NatB if it broke off before the last lines; a claimed chunk at 100 100 | `/ttl nation test <bot> drop`, `ttl rep bonus <bot> -100`, `ftbchunks unclaim` as the bot |
| `guild`, `guild_npcs` | Today's bounty board is re-rolled (`ttl.guild.board`) and the posted contracts (`iron_order`, `rabbit_cull`, `fz_ender_watch`) are on it | `/ttl guild roll` once more before launch, or let the daily roll replace it |
| `events` | Event director state: `ttl.events.last/next/day` (omen fired, the daily count), World's Favor cooldowns on bots only | `/ttl events end`; the daily count resets at midnight |
| `builds` | `test_hut` in the Spirit Corridor (2500 64 0) | Harmless (players never reach x 2500); delete `design/builds/test_hut.toml` to stop placing it |
| `cast`, `guild_npcs` | The real NPCs (kept on purpose); forceloads are removed at the end of each test | `execute in minecraft:overworld run forceload remove all` only if a run broke off |
| `arenas2` | Arena test placements, test mode and challenge cooldowns are cleared by `ttl arena reset` at the end; a run that broke off leaves the two arenas at the test spot (overworld x 20000-20256, z 19997-20077, glass at y 200) and the Elemental Colossus cooldown | `/ttl arena reset`, `/ttl boss cooldown clear elemental_colossus`, `fill` the glass with air |
| `spirit_domain`, `arenas`, `trial_*` | Forceloaded chunks around the arenas (removed by the tests) | `forceload remove all` in that dimension if a run broke off |
| every test | Player files of the bots (`world-ttl/playerdata/`, `usercache.json`, `ttl.*` persistentData with test hooks such as `ttl.absorb.epfake`) | Harmless; delete the TtlBot* entries while the server is down if the world must be pristine |
| every test | `ttl.discord.muted` stays on when `server.sh test` is killed half way | `/ttl discord mute off` |

Checklist before the players' first login (all as ops, in this order, nobody online):
1. `bash tools/server.sh test-all` is green (0 failing) on the final pack, then wait for the ttl-ops run to finish.
2. `/ttl era reset`, `/ttl registry legendcap reset`, `/ttl boss abort`, `/ttl boss cooldown clear all`, `/ttl boss testparty clear`,
   `/ttl events end`, `/ttl absorb war clear`, `/ttl guild roll`, `/ttl discord mute off`, `/ttl party poll`, `/ttl nation sync`.
3. `/ttlbot list` says none; `/list` says nobody; `/ttl registry` lists no holder; `/ttl nation top` is empty; `/ttl era` says era 1.
4. `tools/server.sh logs 2000 | grep -E "ERROR.*KubeJS|\[ttl\].*failed"` is empty.
5. Decide whether the stale bot files (playerdata, FTB personal teams, scoreboard rows) go: only by hand, with the server down.

## Backups and restore

The world volume (`mc-data`, Longhorn) is in Longhorn's `default` recurring-job group: a snapshot every night
at 03:00 (7 kept), a backup to the NAS (`nfs://10.0.20.14:/volume1/media/longhorn-backups`) at 04:30 Mon–Sat
(7 kept) and every Sunday at 04:00 (4 kept). Minecraft autosaves every 5 minutes, so a backup is at most a few
minutes behind. ttl-ops posts in Discord when the newest completed backup is older than 2 days.
A world reset (`ttl-reset.txt`) or a world import (`ttl-import.txt`, "World import" above) also keeps the old
terrain in `world-ttl/ttl-backup/<time>/` on the volume.

Restore (Yasuke, Longhorn UI → Backup):
1. Pick the backup of `pvc-d09ea911-…` → **Restore** to a new volume (e.g. `mc-data-restore`), wait until
   it is healthy.
2. Nobody online; scale the server down by pausing ArgoCD auto-sync for `ocs-two-lives` and
   `kubectl -n ocs-two-lives scale deploy/mc --replicas=0`.
3. Either copy the needed folders from the restored volume into `mc-data` with a helper pod that mounts both,
   or create a PV/PVC for the restored volume and point the Deployment's `mc-data` claim at it.
4. Scale back to 1, re-enable auto-sync, check `tools/server.sh logs`.
Only part of the world broken (one dimension)? Restore just that folder (`world-ttl/dimensions/<ns>/<id>` or
the overworld's `region`) from the restored volume; everything else stays.

## Data we keep

The server is a friend group, but it is in the EU, so players get the usual rights: to see, correct and delete what we
hold about them. The players' own summary is the guide page "Privacy: what we keep" (`design/data/guide.toml`,
`/ttl guide`). Yasuke is the contact and decides on requests. The legal basis is legitimate interest (running and
protecting the server); the Discord link is something a player chooses to do.

| Data | Where | Why | How long |
|---|---|---|---|
| World, player files, statistics, Two Lives progress (life, karma, tier, titles, registry) | `world-ttl` on the `mc-data` volume | The game itself | While the world lives. Deleted data leaves the Longhorn backups after about 4 weeks (7 nightly + 4 Sunday backups, see *Backups*) |
| `/bug` reports: text, name, dimension, position, health, held item, `/ttl inspect` state, last 30 `[ttl]` and 15 `ERROR` log lines | `/data/ttl-reports/<time>-<name>.md` (`BugReports.java`), and a GitHub issue in the repo set in `TTL_REPORT_REPO` when the token exists | Fixing the bug | Server files: 180 days at most (purge below). GitHub issues: until the player asks; the repo `Yasuke2000/ocs-two-lives` is public, so an issue filed there can be read by anyone |
| Activity log (CervLogger: blocks, buckets, containers, entity kills, explosions, signs, interactions, **chat, commands, sessions**) | `database.db` (SQLite) of CervLogger | Rollback of griefing, moderation | 180 days at most (purge below). CervLogger only purges by age: it cannot delete one player's rows |
| Linked account: Minecraft UUID ↔ Discord ID (Simple Discord Link), the `Linked` and Life/tier roles, the nickname | sdlink's account store on the server; roles in Discord | Joining via Discord and the roles | While the player is a member. Unlinking removes it |
| Chat and story posts in Discord (bridge, weekly Hall of Souls with race, tier, deaths, `#leaderboard`) | Discord (its own retention) | The community | Discord's rules; staff can delete a post |
| Minecraft's own logs (`logs/`: names, join addresses) | `/data/logs/` | Crash analysis | Minecraft's rotation; we do not purge them ourselves |

No bank, payment or identity data is collected. Bug reports and the activity log can show where a player built and
when they played; they are never shared outside staff, except the GitHub issue described above.

### Purging old data (Yasuke / ttl-ops)

KubeJS cannot delete files, so the purge is a shell snippet. Run it weekly (a ttl-ops job inside the cluster uses
`kubectl` directly; from a PC use `k3s kubectl` on the node or `tools/server.sh`'s kubeconfig):

```sh
#!/bin/sh
# purge-old-data.sh: bug reports and the activity log older than 180 days.
set -eu
NS=ocs-two-lives
# 1. Preview what goes (drop -delete); the reports are written once, so the file time is the report time.
kubectl -n "$NS" exec deploy/mc -- find /data/ttl-reports -type f -name '*.md' -mtime +180 -print
# 2. Delete them.
kubectl -n "$NS" exec deploy/mc -- find /data/ttl-reports -type f -name '*.md' -mtime +180 -delete
# 3. CervLogger's own purge (same command as /cl purge t:180d in game).
kubectl -n "$NS" exec deploy/mc -- rcon-cli "cl purge t:180d"
```

Not yet verified on the server: that `cl purge` accepts the RCON console as its source (try it once with
`tools/server.sh rcon "cl purge t:180d"` while nobody is online; the purge runs in a background thread and
reports in the log), and that `find` is present in the image (it is in the itzg Ubuntu base). Until the job is
scheduled, the "180 days" in the guide is a promise nobody enforces: schedule it.

### Removal requests

1. **Bug reports:** delete the files that carry the player's name (`ls /data/ttl-reports | grep -i <name>`) and the
   GitHub issues titled `[bug] <name>: …` (`gh issue delete <n>`, or edit the issue to remove the table).
2. **Discord link:** remove the account in sdlink and the `Linked`, Life and tier roles; the player can leave
   the Discord server to end the link. (The sdlink command for this has not been checked here.)
3. **Activity log:** no per-player delete exists; it ages out at 180 days, or Yasuke deletes the rows by hand in the SQLite file.
4. **Game data:** only when the player leaves for good: `/ttl reset <player>` and a player-file delete while the
   server is stopped; backups roll off in about 4 weeks. Builds stay with the world.

## Discord bot

The bot is the server-side mod **Simple Discord Link** (`sdlink` 3.4.5 + CraterLib, config
`pack/config/simple-discord-link/simple-discord-link.toml`). It runs inside the Minecraft server, so there is
no separate bot service. What it does in `#minecraft`. The server's layout (categories, channels, permissions, the
pinned "How to use this channel" message in every channel, the start guide and the rules) is built by
`tools/discord_setup.sh`; the texts are in [discord-guides.md](discord-guides.md). The game's channel ids are in
`design/data/discord.toml` and the sdlink config (`CFG_DISCORD_CHANNEL` = `#minecraft`, `CFG_DISCORD_EVENTS` =
`#story`); the setup script reuses those channels, so a rebuild keeps the ids.

| Feature | How |
|---|---|
| Chat bridge | game chat → `#minecraft`; Discord messages show in game as `[Discord] name: text` |
| Game events | joins, leaves, deaths and advancements (these two follow the `showDeathMessages` / `announceAdvancements` gamerules), server online / offline |
| Story events | `pack/kubejs/server_scripts/ttl/discord.js`: Life 1 death ("X died in their first life"), rebirth ("X was reborn as a Slime"), Legend verdicts, kills of `major` bosses from `design/data/karma.toml`; awakenings and the weekly Hall of Souls (`ttl/discord/`, see *Game features*) — all in `#story` |
| Status | bot status "N/15 souls in the world", channel topic, slash commands `/playerlist`, `/status`, `/help` |
| Account linking (optional) | in game `/discordverify` gives a code; in Discord `/verify <code>` (or DM the code to the bot) |

Test bots (`TtlBot…`) never reach Discord. A Life 1 death shows twice on purpose: the normal death line
(what killed you) and the story line. Scripts post with `TtlDiscord.post(server, text)`; without the mod or a
token every post is silently dropped.

### Creating the bot (once)

The token is the bot's password. It never goes into git, an issue, a PR or a Discord channel: whoever creates
the bot sends it to Yasuke privately, and Yasuke puts it into the Kubernetes secret. Leaked? Reset it (step 3)
and update the secret.

1. <https://discord.com/developers/applications> → **New Application**. Name it e.g. "Voice of the World"
   (no "Discord" in the name, Discord refuses that for bots).
2. **Installation**: untick *User Install*, keep *Guild Install*, *Install Link* = None.
3. **Bot**: **Reset Token** → copy the token (shown once). Untick **Public Bot**. Under *Privileged Gateway
   Intents* enable **MESSAGE CONTENT INTENT** (reading chat) and **SERVER MEMBERS INTENT** (account linking).
4. **OAuth2 → URL Generator**: scopes **bot** and **applications.commands**; bot permissions **View Channels**,
   **Send Messages**, **Send Messages in Threads**, **Embed Links**, **Attach Files**, **Read Message History**,
   **Add Reactions**, **Use External Emojis**, **Manage Channels** (only for the automatic channel topic) and
   **Manage Webhooks** (only needed if webhook mode is turned on later; it is off). Open the generated URL,
   pick our Discord server, **Authorize**. (sdlink also prints a ready-made invite link at the top of the server
   log once it has a token.)
5. In Discord create the text channel **#minecraft** and make sure the bot's role can see it, send messages and
   manage it (topic).
6. Discord **User Settings → Advanced → Developer Mode** on; right-click **#minecraft → Copy Channel ID**.

### Putting it on the server (Yasuke)

The config ships placeholders that the itzg image fills in from the environment on every start, after the
packwiz install (`REPLACE_ENV_VARIABLES`); sdlink then encrypts the token in the server's copy.

| Placeholder | Env var | Comes from |
|---|---|---|
| `botConfig.botToken` | `CFG_DISCORD_TOKEN` | secret `discord-bot`, key `token` (exists; the bot is the application "MInecraft server") |
| `channelsAndWebhooks.channels.chatChannelID` | `CFG_DISCORD_CHANNEL` | the `#minecraft` channel ID (step 6), a plain value in the Deployment; not secret |

The secret also holds `application-id`; sdlink does not need it. (The secret named `discord` is the ttl-ops
webhook, unrelated.) Env for the `mc` container in the Homelab repo (`apps/ocs-two-lives/`):

```yaml
- name: REPLACE_ENV_VARIABLES
  value: "TRUE"
- name: REPLACE_ENV_PATHS          # only scan the configs, not the whole world folder
  value: /data/config
- name: CFG_DISCORD_TOKEN
  valueFrom: { secretKeyRef: { name: discord-bot, key: token } }
- name: CFG_DISCORD_CHANNEL
  value: "<#minecraft channel ID>" # "0" until #minecraft exists: the bot logs in but posts nowhere
```

Check: `tools/server.sh logs | grep -i -E "sdlink|discord"` shows the bot logging in, and "The server is
online." appears in `#minecraft`.

**The placeholders are used up on the first start**: sdlink rewrites the server's copy (encrypted token,
channel ID filled in), so a later change of either env var does nothing on its own. After changing the token
or the channel ID, or when the server started with sdlink before the env existed ("Failed to connect to
discord" in the log), delete the server's copy and restart; packwiz puts the template back and the image
fills it in again:

```sh
k3s kubectl -n ocs-two-lives exec deploy/mc -- rm /data/config/simple-discord-link/simple-discord-link.toml
tools/server.sh restart
```

### Options (config PR, no secret needed)

- Separate channel for events: put its ID in `channelsAndWebhooks.channels.eventsChannelID` (`"0"` = `#minecraft`).
- In-game `/discord` invite command: set `botConfig.invite.inviteLink`.
- Linking required for everyone (Discord-based whitelist): `accessControl.enabled = true`. Everyone, staff
  included, must then `/discordverify` before they can play; test that the `TtlBot` test players still join.
- Run Minecraft commands from Discord: `[minecraftCommands]`, on with a short allow-list (see below).

**Config changes need the reset above**: the server keeps its own rewritten copy of the sdlink config, so a
merged change to `simple-discord-link.toml` (e.g. the `?command` permissions) only applies after deleting that
copy and restarting.

### Game features (`ttl/discord/*.js`, ids in `design/data/discord.toml`)

| Feature | What it does | How |
|---|---|---|
| Life and karma roles | A linked member has exactly one of **Life 1** (Life 1 and the Spirit Corridor) / **Life 2**, plus, once Life 1 is judged, **Wanderer / Survivor / Hero / Legend**. The dark path adds **Fallen** next to the tier role ("Fallen Hero" = Hero + Fallen). | `roles.js`: on login, Life 1 death, rebirth and every 5 min for everyone online. Minecraft UUID → Discord id from sdlink's account store (`DatabaseManager` / `SDLinkAccount.getDiscordID`), roles through sdlink's JDA (`BotController.INSTANCE.getJDA()` → guild `addRoleToMember` / `removeRoleFromMember`). Only roles in `[roles]` are touched. |
| Hall of Souls | Weekly recap in `#story`, Sunday 20:00 Brussels: rebirths (race, tier), Life 1 deaths (days, verdict), Legends, great foes slain, awakenings, brightest soul of the week. Never posts twice (the posted date is kept). | `hall.js`, recorded in server persistentData `ttl.hall.week`, posted as an sdlink CUSTOM message. |
| Leaderboard | One message in `#leaderboard` that the bot edits: brightest soul ever, longest first life, Legends, great foes slain, most chosen races, souls now in Life 1 / Corridor / Life 2. In game: `/ttl top`. | `hall.js`: all-time records in `ttl.hall.records`, message id in `ttl.hall.lbmsg` (deleted → posted again); edited every 10 min and soon after a story event. |
| World events | `#story` hears when someone awakens as a **True Demon Lord** or **True Hero**, or starts the **Harvest Festival** (the Great Sage's World Voice events). | `awaken.js` polls Tensura's existence storage (`TensuraStorages.getExistenceFrom`) like the Great Sage does. Naming is not relayed (nothing to poll). |
| `?bugreport <text>` | Linked members, in `#ideas-and-feedback`: becomes a GitHub issue through the in-game `/bug` (prefixed "from Discord, @name"). Online → filed at once; offline → filed when they next join. | `report.js`; sdlink runs the command under the linked Minecraft name (`chat.useLinkedNames = true`). |
| Staff `?commands` | `modder` role, in `#ideas-and-feedback` or `#server-log`: `?list`, `?neoforge tps`, `?ttl inspect <player>`, `?ttl spawn`, `?ttl staff status`, `?ttl staff registry`, `?ttl recap preview`, `?ttl discordroles <player> [dry]`, plus the member commands. Read-only on purpose: sdlink has no confirm step. | `[minecraftCommands.permissions]` in the sdlink config. |

Setup notes:

- **modder role ID**: sdlink only accepts numeric role IDs. Replace the placeholder `role = "1"` in
  `[[minecraftCommands.permissions]]` with the `modder` role ID (Developer Mode → right-click the role → Copy
  Role ID), then reset the server's config copy as above.
- **Role order** (Server Settings → Roles): the bot's role above Life 1 … Fallen (or Discord refuses the change),
  and `modder` above `Linked` (sdlink uses the member's highest role that has a command list).
- The bot needs View Channel + Send Messages in `#leaderboard` and `#ideas-and-feedback`, and Manage Roles.
- sdlink replies to a `?command` with the first message the command sends; commands with several output lines
  (e.g. `neoforge tps`) show only the first.
- Ops in game: `/ttl recap preview | now`, `/ttl discordroles <player> [dry | expect <keys>]`, `/ttl staff status | registry`.
  Test: `tests/ingame/discord.rcon`.

### The `/ttl` command reference (`#dev-chat`)

[`docs/dev/ttl-commands.md`](dev/ttl-commands.md) lists every `/ttl` command (and `/locate place`) by system with what it
does, what it is for (**PLAYER**, staff, test bot) and its arguments. The command tree and the op level come from the
KubeJS registration source; the descriptions are in `docs/dev/ttl-commands.toml`. After adding or changing a command:

```sh
python tools/gen_ttl_commands.py                  # rewrites docs/dev/ttl-commands.md; lists what the toml still lacks
python tools/gen_ttl_commands.py --check          # exit 1 when the md is stale or the toml and the source disagree
python tools/gen_ttl_commands.py --compare-help help.txt   # against a pasted `/help ttl` of the live server
```

The Discord copy is one pinned header plus a few messages per group in `#dev-chat`. The script finds its own messages by
their last line, edits them in place and never doubles them (more messages than before: the extras go at the bottom;
fewer: the surplus is deleted):

```sh
python tools/gen_ttl_commands.py --discord | ssh -o LogLevel=ERROR root@100.109.28.21 'cat > /tmp/ttl-commands-discord.md'
ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- /tmp/ttl-commands-discord.md' < tools/post_ttl_commands.sh
```

## Roadmap and suggestions

Two Discord channels show players what is going on and let them propose things; the team decides on GitHub and
Yasuke has the final word.

**`#roadmap`** (📌 START, read-only): three bot messages, **Live: test this** (with how to try each feature in game),
**Being built** and **Planned**, in English and Dutch. The source is [`roadmap-public.md`](roadmap-public.md), derived
from `docs/project-status.md` and `design/roadmap.md`. Whenever a feature changes status for players, edit the file
and post it (the script edits the three messages in place and never posts them again; it finds them by their first
line, or by position after a heading was renamed):

```sh
bash tools/post_roadmap.sh docs/roadmap-public.md --dry-run      # offline: prints the three messages and their length
ssh -o LogLevel=ERROR root@100.109.28.21 'cat > /tmp/roadmap-public.md' < docs/roadmap-public.md
ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- /tmp/roadmap-public.md' < tools/post_roadmap.sh
```

**`#suggestions`** (💬 COMMUNITY, a forum): one post per suggestion, with a type tag (Idea, Bug, Balance, Lore,
Quality of life) and 👍 as the default reaction (the vote). The status tags (Under review, Planned, In progress, Done,
Declined) are moderated: only staff and the bot set them. Layout, tags and the pinned how-to come from
`tools/discord_setup.sh` (`docs/discord-guides.md`). Within about 5 minutes **ttl-ops** turns every new post into a
**public** GitHub issue (title = post title; body = the first message, the author's Discord display name and a link to
the post; labels `suggestion` + the type label), replies with the link and sets **Under review**.

### How the team decides (labels on the issue)

The issue's labels and its open/closed state drive Discord, not the board columns (the cluster's tokens have no
access to the project board). New suggestions also show up in `#server-log` (new-issue notice) and, with auto-add
on, in the board's Triage column. Triage them like any issue, then set **one** status label:

| On the GitHub issue | The post on Discord |
| --- | --- |
| nothing yet (new) | **Under review** + a reply with the issue link |
| label `status:planned`: we want it (board: To do; add it to "Planned" in `roadmap-public.md` if players will notice) | **Planned** + reply |
| label `status:in-progress`: someone builds it (assign them; board: In progress; roadmap "Being built") | **In progress** + reply |
| label `status:done` or **close as completed** (a PR with `Closes #n` does this when merged) | **Done** + reply pointing to `#patch-notes` |
| label `status:declined` and **close as "not planned"** (or as duplicate), with a short comment saying why | **Declined** + reply with the link; a closed one is **archived** |
| reopened, or the status labels removed | **Under review** again |

Several status labels: declined wins over done, done over in progress, in progress over planned. A status tag
changed by hand on Discord is put back to the issue's status on the next pass, so change the label instead. When a
suggestion goes live, also move it to "Live" in `roadmap-public.md` and write the patch notes.

**Project board:** the issue forms add their issues to the board (`projects: ["Yasuke2000/1"]`), but that only
works for issues made in the web form, and the cluster's fine-grained tokens cannot add items to a user project.
So the board must add them itself: **Yasuke**, in the board's settings → Workflows → **Auto-add to project**, pick
the repo `ocs-two-lives` with the filter `is:issue label:suggestion` (or `is:issue` for every issue) and enable it.
The "Item closed" workflow (→ Done) keeps the board in step with closing.

### Operations

The sync is `sync_suggestions` in ttl-ops' `loop.sh`, running `suggestions.sh` from the same ConfigMap (Homelab repo,
`apps/ocs-two-lives/manifests/ops.yaml`) every `SUGGEST_EVERY` seconds (300); `SUGGEST_ENABLED: "0"` switches it off.
Tokens: secret `discord-bot` (key `token`) and `bug-reports` (key `token`, a fine-grained token with issues + labels on
this repo), mounted as files and read only by `suggestions.sh`. It keeps no state of its own: the post ↔ issue link
is the marker `<!-- ttl-suggestion thread=<post id> -->` in the issue body (found through the `suggestion` label, the
bot's link reply is the fallback), and what was announced is the post's status tag. Missing labels are created.
Limits per pass: at most 10 new issues (`SUGGEST_MAX_NEW`), 1 s between Discord writes (429 waits for `retry_after`),
2 s between GitHub writes; a GitHub rate limit ends the pass. It writes to `#server-log` only on errors (the same
errors at most once per 6 hours). Pinned posts (the how-to) are skipped. The bot needs Manage Threads (tags, pin,
archive) on top of the rights in "Discord bot".

```sh
# a pass by hand that writes nothing (with the kubeconfig: tools/cluster.py or kubectl --kubeconfig ~/.kube/ocs-two-lives.yaml)
kubectl -n ocs-two-lives exec deploy/ttl-ops -- env SUGGEST_DRY_RUN=1 bash /scripts/suggestions.sh
# one post only (tests): SUGGEST_ONLY_THREAD=<post id>
```

Privacy: a suggestion is public on GitHub with the author's Discord display name (the forum's guidelines say so). A
removal request is handled like the others in "Data we keep": delete the issue and the post.
