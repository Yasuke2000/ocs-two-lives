#!/usr/bin/env bash
# Upload Lerfing's prepared overworld to the staging server and arm the ttl-import.txt marker (docs/server.md
# "World import", design/architecture/lerfing-import.md §6.3). Runs any time nobody is online: the server keeps
# running, the upload goes to /data/import (not the world), and the swap itself happens at the next start
# (ttl-portals 0.9.0), so the restart is the normal deploy.
#
#   bash tools/import_world.sh [--dry-run] [--src DIR] [--batch N] [--margin GIB] [--no-marker]
#
# (a) refuses while a human is online (test bots don't count: `server.sh who`);
# (b) checks the local world (DIR/region/r.*.mca = the lines of DIR/sha256.txt) and the free space on /data;
# (c) sends the region files that are missing on the pod or have the wrong size to /data/import/region (tar over
#     kubectl exec, BATCH files per stream: a broken run resumes where it stopped when started again), then checks
#     every file's sha256 on the pod against sha256.txt; a bad file is deleted and sent again (3 rounds at most);
# (d) writes /data/world-ttl/ttl-import.txt = "minecraft:overworld import <count>" and removes /data/ttl-pregen.done,
#     but only when main's pack (what the restart installs) has ttl-portals >= 0.9.0, the Lerfing grid and the
#     anchor table: an older mod ignores the marker, and the import without the anchors would put Tempest, Dwargon
#     and the builds at the old continent's coordinates on Lerfing's map;
# (e) prints the next steps (restart through the normal deploy, the log lines to watch).
# --dry-run does every check, measures the upload speed (data piped into /dev/null on the pod) and prints the plan;
# it uploads nothing, writes no marker and changes nothing on the server.
# Exit: 0 done (or dry run), 2 usage, 3 someone online or the server can't be asked, 4 main not ready (uploaded,
# marker not written), 5 not enough disk, 1 anything else.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
NODE="${TTL_NODE:-root@100.109.28.21}"
NS=ocs-two-lives
KUBECONFIG_TTL="${TTL_KUBECONFIG:-$HOME/.kube/ocs-two-lives.yaml}"
KUBECTL=$(command -v kubectl || echo "/c/Program Files/Docker/Docker/resources/bin/kubectl.exe")
# Same three ways in as tools/server.sh: in-cluster, the namespace key, or SSH to the node.
if [ -n "${TTL_IN_CLUSTER:-}" ]; then
  k() { kubectl -n "$NS" "$@"; }
  rq() { printf '%s' "$1"; }
elif [ -f "$KUBECONFIG_TTL" ]; then
  k() { "$KUBECTL" --kubeconfig "$KUBECONFIG_TTL" -n "$NS" "$@"; }
  rq() { printf '%s' "$1"; }
  TTL_DIRECT=1
else
  k() { ssh -n -o ConnectTimeout=10 -o LogLevel=ERROR "$NODE" "k3s kubectl -n $NS $*"; }
  rq() { printf '%q' "$1"; }
fi
# Git Bash would turn a /data/... argument into a Windows path for kubectl.exe.
export MSYS2_ARG_CONV_EXCL="/data${MSYS2_ARG_CONV_EXCL:+;$MSYS2_ARG_CONV_EXCL}"
rsh() { k exec deploy/mc -- sh -c "$(rq "$1")"; }   # one shell line on the server pod
rin() {                                            # the same, with this script's stdin piped in
  if [ -n "${TTL_IN_CLUSTER:-}${TTL_DIRECT:-}" ]; then k exec -i deploy/mc -- sh -c "$1"
  else ssh -o LogLevel=ERROR "$NODE" "k3s kubectl -n $NS exec -i deploy/mc -- sh -c $(printf '%q' "$1")"; fi
}

DIM=minecraft:overworld
FOLDER=import                 # the marker's folder: not in world-ttl, so ttl-portals finds it next to it
REMOTE=/data/import
WORLD=/data/world-ttl
MIN_MOD=0.9.0
SRC="${TTL_IMPORT_SRC:-/c/Users/david/AppData/Local/Temp/claude/c--Users-david-Documents-Claims-poc/1537105e-29c1-44a8-bf81-a2b0788a3048/scratchpad/lerfing_world}"
DRY=""; BATCH=25; MARGIN_GIB=2; MARKER=1
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --src) SRC="${2:?--src DIR}"; shift ;;
    --batch) BATCH="${2:?--batch N}"; shift ;;
    --margin) MARGIN_GIB="${2:?--margin GIB}"; shift ;;
    --no-marker) MARKER="" ;;
    -h|--help) sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "usage: import_world.sh [--dry-run] [--src DIR] [--batch N] [--margin GIB] [--no-marker]" >&2; exit 2 ;;
  esac
  shift
done
command -v cygpath >/dev/null && case "$SRC" in [A-Za-z]:*) SRC=$(cygpath -u "$SRC") ;; esac
[ "$(basename "$SRC")" = region ] && SRC=$(dirname "$SRC")   # the region folder itself is fine too
MANIFEST="$SRC/sha256.txt"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

say() { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
die() { code=$1; shift; printf 'REFUSED: %s\n' "$*" >&2; exit "$code"; }
gb() { awk -v b="$1" 'BEGIN { printf "%.2f GB", b / 1e9 }'; }
now_ms() { date +%s%3N; }
[ -n "$DRY" ] && say "DRY RUN: checks and plan only; nothing is uploaded or written on the server."

# (a) ----------------------------------------------------------------------------------------------------------------
step "(a) who is online"
online_check() {
  local who
  who=$(bash "$HERE/server.sh" who 2>/dev/null) || die 3 "cannot ask the server who is online (is it up? tools/server.sh status)"
  [ -z "$who" ] || die 3 "online now: $who. The upload and the restart wait until nobody plays."
}
online_check
say "nobody online (test bots don't count)"
pregen=$(bash "$HERE/server.sh" rcon "dh pregen status" 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | grep -m1 -E "Generated radius|not running" || true)
say "night pregen: ${pregen:-unknown} (a restart stops it; ttl-ops' own deploy pauses it first)"

# (b) ----------------------------------------------------------------------------------------------------------------
step "(b) local world and free space"
[ -d "$SRC/region" ] && [ -f "$MANIFEST" ] || die 1 "no $SRC/region or $MANIFEST (run tools/lerfing/import.py --out first)"
find "$SRC/region" -maxdepth 1 -type f -name 'r.*.mca' -printf '%f %s\n' | sort > "$TMP/local"
tr -d '\r' < "$MANIFEST" | awk 'NF { n = $2; sub(/^\*/, "", n); sub(/^region\//, "", n); print n }' | sort > "$TMP/names"
COUNT=$(wc -l < "$TMP/local" | tr -d ' ')
[ "$(wc -l < "$TMP/names" | tr -d ' ')" = "$COUNT" ] && cut -d' ' -f1 "$TMP/local" | cmp -s - "$TMP/names" \
  || die 1 "the region files in $SRC/region and the names in sha256.txt differ"
TOTAL=$(awk '{ s += $2 } END { print s + 0 }' "$TMP/local")
say "local: $COUNT region files, $(gb "$TOTAL"), sha256.txt lists exactly these"

info=$(rsh "df -P -B1 /data | awk 'NR==2 { print \"df\", \$2, \$3, \$4 }'; echo mod \$(ls /data/mods 2>/dev/null | grep -o 'ttl-portals-[0-9.]*[0-9]' | head -1); echo pending \$(ls $WORLD/ttl-import.txt $WORLD/ttl-import.journal 2>/dev/null)") \
  || die 1 "cannot reach the server pod (tools/server.sh status)"
read -r _ SIZE USED FREE <<<"$(grep '^df ' <<<"$info")"
INSTALLED=$(sed -n 's/^mod *//p' <<<"$info"); PENDING=$(sed -n 's/^pending *//p' <<<"$info")
[ -n "${FREE:-}" ] || die 1 "could not read df /data on the pod"
rsh "[ -d $REMOTE/region ] && find $REMOTE/region -maxdepth 1 -type f -printf '%f %s\n' | sort || true" > "$TMP/remote"
# What has to go: missing on the pod or another size there (an upload cut off mid-file leaves it short).
awk 'FILENAME == ARGV[1] { have[$1] = $2; next } !($1 in have) || have[$1] != $2 { print }' "$TMP/remote" "$TMP/local" > "$TMP/send"
awk 'FILENAME == ARGV[1] { want[$1] = 1; next } !($1 in want) { print $1 }' "$TMP/local" "$TMP/remote" > "$TMP/extra"
SEND_N=$(wc -l < "$TMP/send" | tr -d ' ')
SEND_B=$(awk '{ s += $2 } END { print s + 0 }' "$TMP/send")
OLD_B=$(awk 'FILENAME == ARGV[1] { s[$1] = $2; next } ($1 in s) { t += $2 } END { print t + 0 }' "$TMP/send" "$TMP/remote")   # overwritten
NEED=$(( SEND_B - OLD_B + MARGIN_GIB * 1000000000 ))
AFTER_PCT=$(( (USED + SEND_B - OLD_B) * 100 / SIZE ))
say "server /data: $(gb "$SIZE") total, $(gb "$USED") used, $(gb "$FREE") free ($(( USED * 100 / SIZE )) %)"
say "on the pod already: $(( COUNT - SEND_N )) of $COUNT files at the right size; to send: $SEND_N files, $(gb "$SEND_B")"
say "after the upload: about $AFTER_PCT % used, $(gb $(( FREE - SEND_B + OLD_B ))) free (margin asked: $MARGIN_GIB GB)"
[ -s "$TMP/extra" ] && die 1 "$REMOTE/region holds files that are not in sha256.txt (ttl-portals would refuse the count): $(head -5 "$TMP/extra" | tr '\n' ' ')- delete them by hand first"
if [ "$FREE" -lt "$NEED" ]; then
  say "ttl-backup on the volume (old terrain of earlier resets; the NAS backup keeps it):"
  rsh "du -sh $WORLD/ttl-backup/* 2>/dev/null" | sed 's/^/  /' || true
  die 5 "need $(gb "$NEED") free, have $(gb "$FREE"): merge the Homelab PR that grows mc-data to 60Gi, or delete old ttl-backup folders"
fi
[ "$AFTER_PCT" -lt 85 ] || say "note: at $AFTER_PCT % the night pregen will not start (ttl-ops stops at PREGEN_MAX_DISK 85 %) until mc-data is 60Gi"
[ $(( FREE - SEND_B + OLD_B )) -ge 5000000000 ] || say "note: under 5 GB stays free; the first boot DFU-upgrades and populates every chunk it loads (+20-40 %), grow mc-data first if you can"

# (c) ----------------------------------------------------------------------------------------------------------------
step "(c) upload to $REMOTE/region and sha256 check"
send() {  # sends the files listed in $TMP/send
  local n=0 b=0 i=0 t0 t1 bytes batches
  [ -s "$TMP/send" ] || { say "nothing to send"; return 0; }
  batches=$(( ($(wc -l < "$TMP/send") + BATCH - 1) / BATCH ))
  split -l "$BATCH" "$TMP/send" "$TMP/batch."
  for f in "$TMP"/batch.*; do
    i=$((i + 1)); bytes=$(awk '{ s += $2 } END { print s + 0 }' "$f")
    awk '{ print "region/" $1 }' "$f" > "$f.list"
    t0=$(now_ms)
    tar -C "$SRC" -cf - -T "$f.list" | rin "mkdir -p $REMOTE/region && tar -C $REMOTE -xf - --no-same-owner" \
      || die 1 "batch $i/$batches broke off; run the script again, it resumes"
    t1=$(now_ms); n=$((n + $(wc -l < "$f"))); b=$((b + bytes))
    say "batch $i/$batches: $(wc -l < "$f" | tr -d ' ') files, $(gb "$bytes") in $(( (t1 - t0) / 1000 )) s ($(awk -v b="$bytes" -v ms=$((t1 - t0 + 1)) 'BEGIN { printf "%.1f", b / ms / 1000 }') MB/s); $n files, $(gb "$b") sent"
    rm -f "$f" "$f.list"
  done
}
verify() {  # sha256 on the pod of the files listed in $1; prints the bad names
  awk 'FILENAME == ARGV[1] { f[$1] = 1; next } { n = $2; sub(/^\*/, "", n); sub(/^region\//, "", n) } (n in f) { print $1 "  region/" n }' \
    "$1" <(tr -d '\r' < "$MANIFEST") \
    | rin "cd $REMOTE && sha256sum -c - 2>/dev/null | grep -v ': OK\$' | sed 's#^region/##; s#: .*##' || true"
}
if [ -n "$DRY" ]; then
  # Throughput: 128 MiB from here into /dev/null on the pod (the upload's own path, nothing stored).
  t0=$(now_ms); head -c 134217728 /dev/zero | rin "cat > /dev/null"; t1=$(now_ms)
  rate=$(( 134217728 * 1000 / (t1 - t0 + 1) ))
  say "measured upload speed: $(awk -v r="$rate" 'BEGIN { printf "%.1f", r / 1e6 }') MB/s (128 MiB in $(( (t1 - t0) / 1000 )).$(( (t1 - t0) % 1000 / 100 )) s)"
  say "would send $SEND_N files ($(gb "$SEND_B")) in $(( (SEND_N + BATCH - 1) / BATCH )) batches of $BATCH: about $(( SEND_B / (rate + 1) / 60 )) min at that speed, + the sha256 check on the pod"
  awk 'FILENAME == ARGV[1] { s[$1] = 1; next } !($1 in s)' "$TMP/send" "$TMP/local" > "$TMP/there"
  if [ -s "$TMP/there" ]; then
    t0=$(now_ms); verify "$TMP/there" > "$TMP/bad"; t1=$(now_ms)
    say "sha256 of the $(wc -l < "$TMP/there" | tr -d ' ') files already there: $(wc -l < "$TMP/bad" | tr -d ' ') bad ($(( (t1 - t0) / 1000 )) s)"
  fi
else
  for round in 1 2 3; do
    send
    t0=$(now_ms); verify "$TMP/local" > "$TMP/bad"; t1=$(now_ms)
    [ -s "$TMP/bad" ] || { say "sha256: all $COUNT files match sha256.txt ($(( (t1 - t0) / 1000 )) s)"; break; }
    say "sha256: $(wc -l < "$TMP/bad" | tr -d ' ') files bad or missing (round $round): $(head -5 "$TMP/bad" | tr '\n' ' ')"
    [ "$round" -lt 3 ] || die 1 "files still bad after 3 rounds; nothing armed"
    rsh "cd $REMOTE/region && rm -f $(tr '\n' ' ' < "$TMP/bad")"
    awk 'FILENAME == ARGV[1] { b[$1] = 1; next } ($1 in b)' "$TMP/bad" "$TMP/local" > "$TMP/send"
  done
  tr -d '\r' < "$MANIFEST" | rin "cat > $REMOTE/sha256.txt"
fi

# (d) ----------------------------------------------------------------------------------------------------------------
step "(d) the marker $WORLD/ttl-import.txt"
LINE="$DIM $FOLDER $COUNT"
# What the restart installs is main's pack (PACKWIZ_URL); read it from GitHub through git.
ready=""; why=""
if git -C "$HERE/.." fetch -q origin main 2>/dev/null; then
  mod=$(git -C "$HERE/.." show FETCH_HEAD:pack/mods/ttl-portals.pw.toml 2>/dev/null | grep -o 'ttl-portals-[0-9.]*[0-9]' | head -1 | sed 's/ttl-portals-//' || true)
  grid=$(git -C "$HERE/.." show FETCH_HEAD:pack/config/ttl/canon_regions.json 2>/dev/null | grep -c '"lerfing"' || true)
  anchors=$(git -C "$HERE/.." show FETCH_HEAD:pack/kubejs/server_scripts/ttl/generated/anchors.js 2>/dev/null | grep -c '"tempest"' || true)
  say "main ($(git -C "$HERE/.." rev-parse --short FETCH_HEAD)): ttl-portals ${mod:-?}, Lerfing grid $([ "${grid:-0}" -gt 0 ] && echo yes || echo no), anchor table $([ "${anchors:-0}" -gt 0 ] && echo yes || echo no); the server runs ${INSTALLED:-?}"
  [ "$(printf '%s\n%s\n' "$MIN_MOD" "${mod:-0}" | sort -V | head -1)" = "$MIN_MOD" ] || why="main has ttl-portals ${mod:-?}, the marker needs $MIN_MOD+ (an older mod ignores it)"
  [ "${grid:-0}" -gt 0 ] || why="${why:+$why; }main has no Lerfing grid (canon_regions.json \"lerfing\")"
  [ "${anchors:-0}" -gt 0 ] || why="${why:+$why; }main has no anchor table (generated/anchors.js, WP-L4): Tempest, Dwargon and the builds would land at the old coordinates"
  [ -n "$why" ] || ready=1
else
  why="cannot read main from GitHub (git fetch failed)"
fi
case "$PENDING" in *journal*) die 1 "$WORLD/ttl-import.journal exists: a swap did not finish; read docs/server.md \"World import\" first" ;; esac
if [ -z "$MARKER" ]; then
  say "--no-marker: not written"
elif [ -z "$ready" ]; then
  say "main is NOT ready for the marker: $why"
  [ -n "$DRY" ] || { say "upload done and verified; run this script again once main is ready (it skips what is there, checks sha256 again, then writes the marker)"; exit 4; }
else
  existing=$(rsh "grep -v '^#' $WORLD/ttl-import.txt 2>/dev/null | grep . || true")
  [ -z "$existing" ] || [ "$existing" = "$LINE" ] || die 1 "$WORLD/ttl-import.txt already says '$existing'"
  if [ -n "$DRY" ]; then
    say "would write '$LINE' to $WORLD/ttl-import.txt and remove /data/ttl-pregen.done"
  else
    online_check   # the upload took a while
    rsh "printf '%s\n' '# tools/import_world.sh $(date '+%d/%m/%Y %H:%M')' '$LINE' > $WORLD/ttl-import.txt.tmp && mv $WORLD/ttl-import.txt.tmp $WORLD/ttl-import.txt && rm -f /data/ttl-pregen.done && cat $WORLD/ttl-import.txt"
    say "marker armed: the next server start swaps the overworld"
  fi
fi

# (e) ----------------------------------------------------------------------------------------------------------------
step "(e) next steps (nobody online)"
cat <<EOF
1. Restart through the normal deploy:  bash tools/server.sh deploy
   (refuses while a human is online; restarts until main's pack is installed). If main has a pack ttl-ops has not
   deployed yet, ttl-ops does this same restart by itself within a minute and runs test-all after it.
2. Watch the start:  bash tools/server.sh follow | grep -E '\[ttl\] (world import|world reset|arrival|tempest|dwargon|landmark|chunks)'
   in this order:
     [ttl] world import: checking $REMOTE for $DIM
     [ttl] world import: source OK: $COUNT region files (...), ... chunks; ... sampled: statuses {...}, DataVersion 2860..2860
     [ttl] world import: $DIM from $FOLDER; old terrain in ttl-backup/<time> (moved); /ttl worldreset $DIM follows once the server has started
   then the placers: [ttl] arrival grounded at 1780 ... -150, tempest placed, dwargon placed, landmarks, builds
   ([ttl] chunks: holding ... lines, no watchdog).
   Stop and read docs/server.md "World import" on: "world import REFUSED" (nothing moved, old world runs, marker
   kept), "world import FAILED and was undone", or a start that stops on "ttl-import.journal exists".
3. First checks (rcon): ttlmap 1720 900 -> "imported chunk"; execute in minecraft:overworld if block -453 73 979
   minecraft:chest (Lerfing's spawn chest: no chunk was regenerated); ttl world expect continent 1720 900 yes.
4. bluemap purge tensura, then bluemap force-update tensura. Pregen stays night-only (ttl-ops, needs < 85 % disk).
5. Rollback if the owner does not want it: docs/server.md "World import", "Rollback".
EOF
