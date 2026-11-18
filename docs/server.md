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
| What | `dh config generation.chunkMode INTERNAL_SERVER` (real chunks, saved to the region files, structures included), `dh config common.threadPreset BALANCED`, then `dh pregen start minecraft:overworld -2088 -616 450` (centre of the canon continent; 450 chunks = 7,200 blocks, the continent is about 14,000 × 10,100 blocks) |
| Pause | `dh pregen stop` as soon as a human joins, at 07:00, before a deploy and before the bot tests, and when `/data` is 85 % full. The daytime settings are put back (`generation.chunkMode FEATURES`, `threading.numberOfThreads 4`, `threading.threadRunTimeRatio 0.75`, as in `pack/config/DistantHorizons.toml`) |
| Resume | DH keeps no pregen state over a stop or a restart: the next start walks the same spiral from the centre and skips the sections it already generated, so stop + start works as pause + resume (the % climbs fast through the done part) |
| Discord (#server-log, the ttl-ops webhook) | started (once a night), paused (why, with progress; no player names), progress once an hour, complete, disk full, crash |
| Safety | a server crash while it runs stops it for the rest of the night; so do 3 runs that end on their own |
| Done | at ≥ 99 % it writes `/data/ttl-pregen.done` (the spec) and stops for good. Delete that file to pregenerate again, e.g. after an overworld reset |

`dh pregen status` answers `Generated radius: <r> / 450 chunks (<n> cps, <p>%), ETA: <t>` while it runs and
`Pregen is not running` otherwise; DH also logs progress in the server console. Knobs are env vars on the ttl-ops
Deployment: `PREGEN_ENABLED` (`0` = ttl-ops leaves DH alone, for a manual pregen), `PREGEN_DIM`, `PREGEN_X`,
`PREGEN_Z`, `PREGEN_RADIUS`, `PREGEN_THREADS`, `PREGEN_MAX_DISK`.

Watch during the first nights: TPS and pod memory (INTERNAL_SERVER loads real chunks in the game's JVM; heap 8G,
limit 12Gi), the size of `world-ttl` on the 30 Gi volume (a fully generated continent is several GB of region
files plus the DH database and BlueMap tiles), and the Longhorn backup size. BlueMap renders the new chunks too.

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

## Canon builds

Our own builds on canon spots (a town square, a gate, a hall: `blueprints/<name>.py`) are placed by
`pack/kubejs/server_scripts/ttl/life/builds.js` from one file each, `design/builds/<name>.toml`
(`_example.toml` documents every field; files starting with `_` are ignored). `python tools/gen_data.py` reads
them, turns `landmark = "<name in canon_regions.json>"` into world x/z (the same `(ref - origin) x width / 2570`
as the landmarks), checks the structure files and the anchor (it fails on an unknown landmark, a missing
structure or an anchor outside the structure) and writes `TtlData.builds` plus the per-column ground data of the
structure files (`generated/builds.js`).

**When.** About 90 s after start, one build at a time with a 5 s gap, after Tempest, Dwargon and the landmarks.
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
columns over water or ice, or within 24 blocks of Tempest, Dwargon, a placed landmark or another build, is out; the
rest are scored by 2 x the mean deviation from the median ground height + half the p10-p90 spread + distance/16 +
20 x the water share, and the anchor goes on the median. (Water is a cost, not a veto: a 120-block box nearly always
crosses a stream or pond, and the terrain fit fills those columns from the bed.) The log line
`[ttl] build <name>: surveyed N spots ... least water P %; best at X Z, D blocks from the canon point ...` says what
was found; when nothing qualifies, the least water seen tells whether to raise `search` or `max_wet`. The canon map
(`canon_map.txt`) does not predict real lakes: Milim's land round the Forgotten Dragon landmark is lakes at sea level.

**Terrain.** Like Tempest and Dwargon: the real terrain is read before placing; under every column that has blocks
the gap down to the terrain is filled (dirt, stone deeper down; sand or red sand over sandstone in a desert; over a
stream or pond from its bed, so no dirt bridges over water), so nothing floats; with `clear_above` everything above the highest block of the column (trees, hills) is cleared; round
the box `margin` columns get a 1:1 earth skirt (grass on top) and a 1:1 cut into hills. Void columns (the Spirit
Corridor) are left alone. Put explicit air into the blueprint wherever the inside must stay open: the placer only
fills under the lowest and clears above the highest block of a column.

**Log lines.** One per build when done, the format `tools/verify_build.py <name> --log` reads:
`[ttl] <name> placed: corner X Y Z, anchor at x y z (version N, <how>, terrain done)` (`terrain FAILED` when a
terrain command failed: not recorded, tried again). `corner` is the structure's 0,0,0 (for slabs: of the first
one). Builds outside the overworld: `verify_build.py <name> --log --dimension <dim>`. Failures:
`[ttl] build <name>: not placed (<why>)`.

**Ops** (permission 2): `/ttl build list` (state of every build), `/ttl build where <name>` (spot, worked area, a
tp command), `/ttl build place <name|all>` (builds that are not at their current version yet),
`/ttl build place <name|all> force` (again, at the recorded spot), `/ttl build expect <name> placed` (prints
`ttl: ...` when the placed version is not the TOML's). `/ttl build <blueprint>` (a build at your feet) still works.
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
| `bosses`, `story`, `wild` | Boss cooldowns (`ttl.boss.last.<id>`): cleared by `bosses.rcon` itself; a run that broke off leaves them | `/ttl boss cooldown clear all`; `/ttl boss abort` removes a boss left out; `/ttl boss testparty clear` |
| `bosses`, `karma`, `guild` | Scoreboard entries for bot names (`ttl.b.*`, `ttl.k.*`, `ttl.g.*`, `ttl.bounty`, `ttl.rep.*`) | `scoreboard players reset TtlBot*` is not supported by name pattern: `scoreboard players reset <bot>` per name, or ignore (bots never show) |
| `story`, `party`, `rep`, `nations` | Story event ring (`ttl.story.log`), reputation ring log (`ttl.rep.log`) with bot entries; `ttl.story.parties` / `ttl.party.roster` rows for bot FTB teams | Rings are capped and bot rows never post; `/ttl party poll` and `/ttl nation sync` re-read FTB Teams (bot rows stay keyed by team id, harmless) |
| `party`, `nations` | FTB Teams: a personal team per bot that ever joined (FTB Teams world data); every test party is left by its members at the end, a run that broke off leaves `PrtyTest` / `TtlBotNatParty*` | `ftbteams party leave` as the bot (spawn it again with `/ttlbot spawn <name>`) or remove the bot's team from the FTB Teams data while the server is down |
| `nations` | A nation record (`ttl.nations`) if the run broke off before `dissolve`; 100 bonus renown on NatA/NatB if it broke off before the last lines; a claimed chunk at 100 100 | `/ttl nation test <bot> drop`, `ttl rep bonus <bot> -100`, `ftbchunks unclaim` as the bot |
| `guild`, `guild_npcs` | Today's bounty board is re-rolled (`ttl.guild.board`) and the posted contracts (`iron_order`, `rabbit_cull`, `fz_ender_watch`) are on it | `/ttl guild roll` once more before launch, or let the daily roll replace it |
| `events` | Event director state: `ttl.events.last/next/day` (omen fired, the daily count), World's Favor cooldowns on bots only | `/ttl events end`; the daily count resets at midnight |
| `builds` | `test_hut` in the Spirit Corridor (2500 64 0) | Harmless (players never reach x 2500); delete `design/builds/test_hut.toml` to stop placing it |
| `cast`, `guild_npcs` | The real NPCs (kept on purpose); forceloads are removed at the end of each test | `execute in minecraft:overworld run forceload remove all` only if a run broke off |
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
A world reset (`ttl-reset.txt`) also keeps the old terrain in `world-ttl/ttl-backup/<time>/` on the volume.

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
