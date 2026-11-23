#!/usr/bin/env bash
# A local copy of the staging server on this PC, for testing a change in minutes before it goes through
# push -> ttl-ops deploy -> test-all on the homelab. Git Bash on Windows (Linux and WSL work too). Needs Java 21,
# Python 3 and packwiz (~/go/bin is searched). docs/server.md "Local testing" explains the loop.
#
# Same as staging: NeoForge + the pack's server-side mods installed by packwiz-installer (what the itzg image runs),
# the world datapack, level world-ttl, hard, 7 simulation chunks, flight on, Aikar flags. Different on purpose:
# bound to 127.0.0.1 (game and RCON), offline mode, no Discord token, a random RCON password in the server
# folder, the ttl-portals jar from mod/ (your build), a fixed seed, a smaller heap and view distance.
# Everything lives in $TTL_LOCAL_DIR (default %LOCALAPPDATA%\ocs-two-lives\local-server), never in git.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PACK=$ROOT/pack
if [ -n "${TTL_LOCAL_DIR:-}" ]; then D=$TTL_LOCAL_DIR
elif [ -n "${LOCALAPPDATA:-}" ]; then D=$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || echo "$LOCALAPPDATA")/ocs-two-lives/local-server
else D=${XDG_DATA_HOME:-$HOME/.local/share}/ocs-two-lives/local-server
fi
SRV=$D/server
CACHE=$D/cache
SNAPS=$D/snapshots
STATE=$D/state
LEVEL=world-ttl
PORT=${TTL_LOCAL_PORT:-25565}
RCON_PORT=${TTL_LOCAL_RCON_PORT:-25575}
MEMORY=${TTL_LOCAL_MEMORY:-6G}
VIEW=${TTL_LOCAL_VIEW:-8}
SEED=${TTL_LOCAL_SEED:-ocs-two-lives-local}
NEOFORGE=$(sed -n 's/^neoforge = "\(.*\)"/\1/p' "$PACK/pack.toml")
BOOTSTRAP_URL=https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar
PW=$(command -v packwiz || ls "$HOME"/go/bin/packwiz{.exe,} 2>/dev/null | head -1 || true)
PY=$(command -v python3 || command -v python)
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) WIN=1 ;; *) WIN= ;; esac
winpath() { if [ -n "$WIN" ]; then cygpath -w "$1"; else printf '%s' "$1"; fi; }

say() { printf '[local] %s\n' "$*" >&2; }
die() { say "$*"; exit 1; }
now() { date +%s; }

# --- one user at a time ----------------------------------------------------------------------------------
# Every command that changes the server or talks to it for long (up, down, restart, sync, test, snapshot, reset, verify)
# holds $STATE/lock for its run: two agents' syncs or test runs on one server overwrite each other's scripts and bots.
# A lock whose process is gone is stale and taken over. `verify` hands its token to the local.sh of its worktree
# (TTL_LOCAL_LOCK_HELD), which then runs under the same lock.
LOCK=$STATE/lock
LOCK_TOKEN=
lock_owner() { cat "$LOCK/owner" 2>/dev/null || true; }
lock_take() {  # what
  mkdir -p "$STATE"
  if [ -n "${TTL_LOCAL_LOCK_HELD:-}" ] && [ "$(cat "$LOCK/token" 2>/dev/null)" = "$TTL_LOCAL_LOCK_HELD" ]; then return 0; fi
  if ! mkdir "$LOCK" 2>/dev/null; then
    local owner pid
    owner=$(lock_owner); pid=${owner%% *}
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      die "the local server is busy: pid $owner. One user at a time: wait for it (tools/local.sh status shows the holder)"
    fi
    say "taking over a stale lock (${owner:-no owner})"
    rm -rf "$LOCK"; mkdir "$LOCK" || die "cannot take $LOCK"
  fi
  LOCK_TOKEN="$$-$RANDOM-$(now)"
  printf '%s\n' "$LOCK_TOKEN" > "$LOCK/token"
  printf '%s %s since %s (%s)\n' "$$" "$1" "$(date '+%d/%m %H:%M')" "$ROOT" > "$LOCK/owner"
  trap lock_release EXIT
}
lock_release() {
  if [ -n "$LOCK_TOKEN" ] && [ "$(cat "$LOCK/token" 2>/dev/null)" = "$LOCK_TOKEN" ]; then rm -rf "$LOCK"; fi
  LOCK_TOKEN=
}

find_java() {
  local c
  for c in "${TTL_JAVA:-}" "${JAVA_HOME:+$JAVA_HOME/bin/java}" "$HOME"/.gradle/jdks/*21*/bin/java \
           /c/Program\ Files/Eclipse\ Adoptium/jdk-21*/bin/java /c/Program\ Files/Java/jdk-21*/bin/java \
           /usr/lib/jvm/*21*/bin/java "$(command -v java || true)"; do
    [ -n "$c" ] || continue
    [ -x "$c" ] || [ -x "$c.exe" ] || continue
    if "$c" -version 2>&1 | grep -q 'version "21'; then printf '%s' "$c"; return 0; fi
  done
  die "Java 21 not found: set TTL_JAVA=/path/to/java (a gradlew build in mod/ also downloads one to ~/.gradle/jdks)"
}

# --- RCON -------------------------------------------------------------------------------------------------
rcon_password() {
  mkdir -p "$STATE"
  [ -s "$STATE/rcon.password" ] || { od -An -tx1 -N16 /dev/urandom | tr -d ' \n' > "$STATE/rcon.password"; }
  cat "$STATE/rcon.password"
}
rcon_once() { "$PY" -I "$(winpath "$ROOT/tools/rcon.py")" --port "$RCON_PORT" --password-file "$(winpath "$STATE/rcon.password")" "$1"; }
# One connection for a whole test run (tools/rcon.py --serve), on fds 7/8 so the runner's subshells can use it.
# Each command starts TTL_LOCAL_TICKS (2) game ticks after the previous one ended: on staging a command is a kubectl
# exec (~0.17 s, 3 ticks), and tests count on what a script schedules a tick later (the Corridor after a `kill`) being
# done. 2, not 1: a command can run in the middle of a tick (while the main thread waits for a chunk), so only the
# second tick boundary guarantees that a whole tick has passed.
TICKS=${TTL_LOCAL_TICKS:-2}
RCON_OPEN=
rcon_open() {
  coproc RCONP { "$PY" -I "$(winpath "$ROOT/tools/rcon.py")" --serve --ticks "$TICKS" --port "$RCON_PORT" --password-file "$(winpath "$STATE/rcon.password")"; }
  exec 7>&"${RCONP[1]}" 8<&"${RCONP[0]}"
  RCON_OPEN=1
}
rcon() {
  if [ -z "$RCON_OPEN" ]; then rcon_once "$1"; return; fi
  local line
  printf '%s\n' "$1" >&7
  while IFS= read -r line <&8; do
    [ "$line" = '<<<rcon-end>>>' ] && return 0
    printf '%s\n' "$line"
  done
  die "lost the RCON connection (server down? see: tools/local.sh logs)"
}
log_grep() { grep -E "$1" "$SRV/logs/latest.log" || true; }
# The same runner as tools/server.sh (plain, run_test, ingame_test, ingame_test_all).
source "$ROOT/tools/ingame.sh"
source "$ROOT/tools/test_lib.sh"   # run_test with tokens, `@expect` and `@import` (overrides ingame.sh's)

# --- process ---------------------------------------------------------------------------------------------
pid_alive() {
  local p
  p=$(cat "$STATE/server.pid" 2>/dev/null) || return 1
  if [ -n "$WIN" ]; then tasklist //FI "PID eq $p" //NH 2>/dev/null | grep -q java; else kill -0 "$p" 2>/dev/null; fi
}
running() { pid_alive && rcon_once "list" >/dev/null 2>&1; }

wait_ready() {  # until RCON answers and the log says Done, or the process dies
  local t0 deadline=${1:-900}
  t0=$(now)
  while :; do
    if ! pid_alive; then
      tail -40 "$SRV/logs/latest.log" 2>/dev/null >&2 || true
      die "the server stopped while starting (log above; full log: $SRV/logs/latest.log, crash reports: $SRV/crash-reports)"
    fi
    if grep -q 'Done (' "$SRV/logs/latest.log" 2>/dev/null && rcon_once "list" >/dev/null 2>&1; then
      say "ready in $(( $(now) - t0 ))s ($(grep -m1 -o 'Done ([0-9.]*s)' "$SRV/logs/latest.log"))"
      now > "$STATE/ready.at"
      return 0
    fi
    [ $(( $(now) - t0 )) -lt "$deadline" ] || die "not ready after ${deadline}s; see tools/local.sh logs"
    sleep 2
  done
}

start_server() {
  pid_alive && { say "already running (pid $(cat "$STATE/server.pid"))"; return 0; }
  local java args
  java=$(find_java)
  args=libraries/net/neoforged/neoforge/$NEOFORGE/$([ -n "$WIN" ] && echo win_args.txt || echo unix_args.txt)
  [ -f "$SRV/$args" ] || die "NeoForge is not installed; run tools/local.sh up"
  # wait_ready looks for "Done (" in latest.log, so it must be new; keep the last run's log (an import, a crash).
  [ -f "$SRV/logs/latest.log" ] && mv -f "$SRV/logs/latest.log" "$SRV/logs/previous.log"
  say "starting (heap $MEMORY, game 127.0.0.1:$PORT, RCON 127.0.0.1:$RCON_PORT)"
  # No bug-report token: /bug saves to ttl-reports/ instead of opening GitHub issues. -Dttl.local marks the process,
  # -Dttl.localport tells two local servers apart (a second TTL_LOCAL_DIR beside the first: 23/11 a stop of the second
  # found the first's java by the shared marker and killed it).
  (cd "$SRV" && exec env -u TTL_GITHUB_TOKEN -u TTL_REPORT_REPO -u CFG_DISCORD_TOKEN \
     "$java" -Dttl.local=1 "-Dttl.localport=$PORT" @user_jvm_args.txt "@$args" nogui < /dev/null > "$SRV/console.log" 2>&1) &
  local p=$! i
  if [ -n "$WIN" ]; then
    # Git Bash pids are not Windows pids; find java.exe by its marker so tasklist/taskkill can see it.
    p=
    for i in 1 2 3 4 5 6 7 8 9 10; do
      p=$(powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | Where-Object { \$_.CommandLine -like '*-Dttl.localport=$PORT *' } | Select-Object -First 1).ProcessId" 2>/dev/null | tr -d '\r ')
      [ -n "$p" ] && break
      sleep 1
    done
    [ -n "$p" ] || die "java did not start; see $SRV/console.log"
  fi
  echo "$p" > "$STATE/server.pid"
}

stop_server() {
  pid_alive || { say "not running"; rm -f "$STATE/server.pid"; return 0; }
  local p t0
  p=$(cat "$STATE/server.pid"); t0=$(now)
  say "stopping (stop saves every level, then exits)"
  rcon_once "stop" >/dev/null 2>&1 || say "RCON did not take 'stop'; waiting for the process anyway"
  while pid_alive; do
    if [ $(( $(now) - t0 )) -gt 120 ]; then
      say "no clean stop after 120s; killing pid $p"
      if [ -n "$WIN" ]; then taskkill //F //PID "$p" >/dev/null 2>&1 || true; else kill -9 "$p" 2>/dev/null || true; fi
      break
    fi
    sleep 1
  done
  rm -f "$STATE/server.pid" "$STATE/ready.at"
  if grep -q 'All dimensions are saved' "$SRV/logs/latest.log" 2>/dev/null; then say "stopped in $(( $(now) - t0 ))s (all levels saved)"
  else say "stopped in $(( $(now) - t0 ))s, but the log does not say the levels were saved: a snapshot now may be torn"; fi
}

# The start-up placers (Tempest, Dwargon, landmarks, then the canon builds from tick 1800, builds.js START_DELAY) run
# one by one in the background for many minutes on a fresh world; tests that place or expect a build queue behind
# them and fail. Staging's world finished them long ago. Waits until the builds queue is empty.
wait_settled() {
  local deadline=${1:-3600} t0 up left n last=
  t0=$(now)
  up=$(( t0 - $(cat "$STATE/ready.at" 2>/dev/null || echo 0) ))
  if [ "$up" -lt 100 ]; then say "waiting $(( 100 - up ))s for the build queue to start (builds.js START_DELAY)"; sleep $(( 100 - up )); fi
  while :; do
    left=$(rcon_once "ttl build list" | grep -E 'pending|FAILED' || true)
    n=$(grep -c 'pending' <<<"$left" || true)
    [ "$n" -gt 0 ] || break
    [ $(( $(now) - t0 )) -lt "$deadline" ] || { printf '%s\n' "$left" >&2; die "start-up builds still pending after ${deadline}s"; }
    [ "$n" = "$last" ] || say "waiting for $n start-up build(s) to place ($(grep -m1 -o '^[a-z_]*' <<<"$left") ...)"
    last=$n
    sleep 10
  done
  [ $(( $(now) - t0 )) -lt 2 ] || say "start-up placements done in $(( $(now) - t0 ))s"
}

# --- install ---------------------------------------------------------------------------------------------
install_neoforge() {
  ls "$SRV/libraries/net/neoforged/neoforge/$NEOFORGE/"*_args.txt >/dev/null 2>&1 && return 0
  local java jar=$CACHE/neoforge-$NEOFORGE-installer.jar
  java=$(find_java)
  mkdir -p "$CACHE" "$SRV"
  [ -s "$jar" ] || curl -fsSL -o "$jar" "https://maven.neoforged.net/releases/net/neoforged/neoforge/$NEOFORGE/neoforge-$NEOFORGE-installer.jar"
  say "installing NeoForge $NEOFORGE"
  (cd "$SRV" && "$java" -jar "$(winpath "$jar")" --installServer > "$CACHE/neoforge-install.log" 2>&1) \
    || { tail -20 "$CACHE/neoforge-install.log" >&2; die "NeoForge install failed"; }
}

# packwiz-installer (what the itzg image runs for PACKWIZ_URL) installs the server side of the pack. It reads a
# copy of pack/ with a fresh index, served on localhost, so uncommitted edits install without touching the repo.
install_pack() {
  [ -n "$PW" ] || die "packwiz not found (go install github.com/packwiz/packwiz@latest)"
  local java port httpd
  java=$(find_java)
  mkdir -p "$CACHE"
  [ -s "$CACHE/packwiz-installer-bootstrap.jar" ] || curl -fsSL -o "$CACHE/packwiz-installer-bootstrap.jar" "$BOOTSTRAP_URL"
  rm -rf "$D/pack" && mkdir -p "$D/pack"
  tar -C "$PACK" -cf - . | tar -C "$D/pack" -xf -
  (cd "$D/pack" && "$PW" refresh >/dev/null)
  port=$("$PY" -I -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')
  # Not `-m http.server`: its listen backlog of 5 makes Windows refuse packwiz-installer's parallel downloads.
  "$PY" -I -c '
import functools, http.server, sys
class S(http.server.ThreadingHTTPServer):
    request_queue_size = 256
    daemon_threads = True
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=sys.argv[2])
S(("127.0.0.1", int(sys.argv[1])), h).serve_forever()
' "$port" "$(winpath "$D/pack")" > "$CACHE/pack-httpd.log" 2>&1 &
  httpd=$!
  # Python on Windows can take several seconds to bind; packwiz-installer gives up on the first refused connect.
  local i
  for i in $(seq 1 60); do
    curl -fsS -o /dev/null "http://127.0.0.1:$port/pack.toml" 2>/dev/null && break
    kill -0 "$httpd" 2>/dev/null || { cat "$CACHE/pack-httpd.log" >&2; die "the local pack server stopped (port $port)"; }
    sleep 0.5
  done
  curl -fsS -o /dev/null "http://127.0.0.1:$port/pack.toml" \
    || { kill "$httpd" 2>/dev/null; cat "$CACHE/pack-httpd.log" >&2; die "the local pack server did not answer on port $port"; }
  say "installing the pack (packwiz-installer, server side)"
  (cd "$SRV" && "$java" -jar "$(winpath "$CACHE/packwiz-installer-bootstrap.jar")" -g -s server \
     "http://127.0.0.1:$port/pack.toml" > "$CACHE/packwiz-install.log" 2>&1) \
    || { kill "$httpd" 2>/dev/null; tail -30 "$CACHE/packwiz-install.log" >&2; die "packwiz-installer failed"; }
  kill "$httpd" 2>/dev/null || true
  mods_hash > "$STATE/mods.sha"
}
# The mod list and the Minecraft/NeoForge versions; not the index hash, which every packwiz refresh changes.
mods_hash() { { cat "$PACK"/mods/*.pw.toml; sed -n '/^\[versions\]/,$p' "$PACK/pack.toml"; } | sha256sum | cut -d' ' -f1; }

# Your ttl-portals build replaces the released jar (gradle is incremental: seconds when mod/ did not change).
# TTL_LOCAL_MOD=release keeps the pack's released jar.
install_mod() {
  [ "${TTL_LOCAL_MOD:-build}" = release ] && { rm -f "$SRV"/mods/ttl-portals-local.jar; say "ttl-portals: the pack's release jar"; return 0; }
  local jar
  say "building ttl-portals (mod/, gradlew build)"
  (cd "$ROOT/mod" && ./gradlew build -q --console=plain > "$CACHE/gradle.log" 2>&1) \
    || { tail -30 "$CACHE/gradle.log" >&2; die "mod build failed (full log: $CACHE/gradle.log)"; }
  jar=$(ls -t "$ROOT"/mod/build/libs/ttl-portals-*.jar | grep -vE -- '-(sources|javadoc)\.jar$' | head -1)
  rm -f "$SRV"/mods/ttl-portals-*.jar
  cp "$jar" "$SRV/mods/ttl-portals-local.jar"
  mod_hash > "$STATE/mod.sha"
  say "ttl-portals: local build $(basename "$jar")"
}
# The mod's sources by content, not file times: a checkout of another branch or worktree (verify) with older files
# still counts as a change, so the jar on the server is always the build of the sources the checkout has.
mod_hash() {
  (cd "$ROOT/mod" && find src build.gradle gradle.properties settings.gradle -type f 2>/dev/null | LC_ALL=C sort \
     | while IFS= read -r f; do printf '%s ' "$f"; sha256sum < "$f"; done) | sha256sum | cut -d' ' -f1
}

set_prop() {  # key value: in server.properties
  local f=$SRV/server.properties
  touch "$f"
  if grep -q "^$1=" "$f"; then sed -i "s|^$1=.*|$1=$2|" "$f"; else printf '%s=%s\n' "$1" "$2" >> "$f"; fi
}

configure() {
  local java
  java=$(find_java)
  echo "eula=true" > "$SRV/eula.txt"
  set_prop level-name "$LEVEL"
  set_prop level-seed "$SEED"
  set_prop server-ip 127.0.0.1
  set_prop server-port "$PORT"
  set_prop online-mode false
  set_prop enable-rcon true
  set_prop rcon.port "$RCON_PORT"
  set_prop rcon.password "$(rcon_password)"
  set_prop difficulty hard
  set_prop max-players 15
  set_prop view-distance "$VIEW"
  set_prop simulation-distance 7
  set_prop spawn-protection 0
  set_prop allow-flight true
  set_prop white-list false
  set_prop enforce-whitelist false
  set_prop motd "OCS Tensura: Two Lives - local"
  # Staging: MEMORY=8G + USE_AIKAR_FLAGS (itzg's G1 set for heaps under 12 GB). The container's JVM runs in en_US;
  # Windows hands Java the PC's locale (nl_BE prints "1,00"), and replies such as /ttlmap's "canon weight 1.00"
  # format numbers with it, so tests that match them fail here only.
  cat > "$SRV/user_jvm_args.txt" <<EOF
-Duser.language=en
-Duser.country=US
-Xms$MEMORY
-Xmx$MEMORY
-XX:+UseG1GC
-XX:+ParallelRefProcEnabled
-XX:MaxGCPauseMillis=200
-XX:+UnlockExperimentalVMOptions
-XX:+DisableExplicitGC
-XX:+AlwaysPreTouch
-XX:G1NewSizePercent=30
-XX:G1MaxNewSizePercent=40
-XX:G1HeapRegionSize=8M
-XX:G1ReservePercent=20
-XX:G1HeapWastePercent=5
-XX:G1MixedGCCountTarget=4
-XX:InitiatingHeapOccupancyPercent=15
-XX:G1MixedGCLiveThresholdPercent=90
-XX:G1RSetUpdatingPauseTimePercent=5
-XX:SurvivorRatio=32
-XX:+PerfDisableSharedMem
-XX:MaxTenuringThreshold=1
-Dusing.aikars.flags=https://mcflags.emc.gs
-Daikars.new.flags=true
-Dfile.encoding=UTF-8
EOF
  # Staging fills ${CFG_*} from secrets (REPLACE_ENV_VARIABLES); here there is no bot token.
  if [ -f "$SRV/config/simple-discord-link/simple-discord-link.toml" ]; then
    sed -i 's/\${CFG_DISCORD_TOKEN}//; s/\${CFG_DISCORD_CHANNEL}/0/; s/\${CFG_DISCORD_EVENTS}/0/' \
      "$SRV/config/simple-discord-link/simple-discord-link.toml"
  fi
  # BlueMap's web server only on this PC.
  if [ -f "$SRV/config/bluemap/webserver.conf" ] && ! grep -q '^ip:' "$SRV/config/bluemap/webserver.conf"; then
    printf '\n# tools/local.sh: this PC only\nip: "127.0.0.1"\n' >> "$SRV/config/bluemap/webserver.conf"
  fi
  # A second local server beside the first (TTL_LOCAL_PORT/RCON_PORT too) needs its own map port.
  if [ -f "$SRV/config/bluemap/webserver.conf" ] && [ -n "${TTL_LOCAL_MAP_PORT:-}" ]; then
    sed -i "s/^port: .*/port: $TTL_LOCAL_MAP_PORT/" "$SRV/config/bluemap/webserver.conf"
  fi
  # DATAPACKS=/data/datapacks/ttl-overrides on staging: the image copies it into the world before each start.
  mkdir -p "$SRV/$LEVEL/datapacks"
  rm -rf "$SRV/$LEVEL/datapacks/ttl-overrides"
  cp -r "$SRV/datapacks/ttl-overrides" "$SRV/$LEVEL/datapacks/"
}

# --- snapshots -------------------------------------------------------------------------------------------
snapshot_save() {  # name: copy of the stopped world
  local name=${1:-base}
  [ -d "$SRV/$LEVEL" ] || die "no world yet"
  mkdir -p "$SNAPS"
  rm -rf "${SNAPS:?}/$name.tmp"
  cp -r "$SRV/$LEVEL" "$SNAPS/$name.tmp"
  rm -rf "${SNAPS:?}/$name" && mv "$SNAPS/$name.tmp" "$SNAPS/$name"
  say "snapshot '$name' saved ($(du -sh "$SNAPS/$name" | cut -f1))"
}
snapshot_restore() {
  local name=${1:-base}
  [ -d "$SNAPS/$name" ] || die "no snapshot '$name' (have: $(ls "$SNAPS" 2>/dev/null | tr '\n' ' '))"
  rm -rf "${SRV:?}/$LEVEL"
  cp -r "$SNAPS/$name" "$SRV/$LEVEL"
  say "world restored from snapshot '$name'"
}

# --- sync ------------------------------------------------------------------------------------------------
# Copies what changed in pack/ since the last up/sync into the server, and applies it the cheapest way that works.
# $D/pack is the baseline (what the server has from git), so files the mods rewrite on start-up (configs) never
# count as changes.
#   kubejs/server_scripts, kubejs/data, datapacks,
#   config/ttl, config/ftbquests                           -> /reload (scripts, data and quest files; like staging's
#                                                             push-scripts: /kubejs reload server-scripts would keep
#                                                             the commands the old scripts registered)
#   kubejs/startup_scripts, other config                   -> restart (read at start-up only)
#   mods/*.pw.toml, [versions] in pack.toml, mod/ sources  -> full up: packwiz-installer + gradle + restart
#   kubejs/assets, kubejs/client_scripts                   -> copied; nothing to apply on a server
sync_changes() {  # prints "<M|A|D> <path relative to pack/>"
  local line f
  { diff -rq "$PACK/kubejs" "$D/pack/kubejs"; diff -rq "$PACK/config" "$D/pack/config"
    diff -rq "$PACK/datapacks" "$D/pack/datapacks"; } 2>/dev/null | while IFS= read -r line; do
    case "$line" in
      "Files "*" differ") f=${line#Files }; f=${f%% and *}; echo "M ${f#"$PACK"/}" ;;
      "Only in $PACK"*) f=${line#Only in }; f="${f%%: *}/${f#*: }"; echo "A ${f#"$PACK"/}" ;;
      "Only in $D/pack"*) f=${line#Only in }; f="${f%%: *}/${f#*: }"; echo "D ${f#"$D"/pack/}" ;;
    esac
  done
}
mods_changed() {
  [ "$(mods_hash)" != "$(cat "$STATE/mods.sha" 2>/dev/null)" ] && return 0
  [ "${TTL_LOCAL_MOD:-build}" = release ] && return 1
  [ -f "$SRV/mods/ttl-portals-local.jar" ] || return 0
  [ "$(mod_hash)" != "$(cat "$STATE/mod.sha" 2>/dev/null)" ]
}

# Copies the changes into the server and the baseline; sets NEED to none, reload or restart and N to the count.
apply_changes() {
  local op rel
  NEED=none; N=0
  while read -r op rel; do
    N=$((N + 1))
    case "$rel" in
      kubejs/assets/*|kubejs/client_scripts/*) ;;
      kubejs/server_scripts*|kubejs/data*|datapacks*|config/ttl*|config/ftbquests*) [ "$NEED" = restart ] || NEED=reload ;;
      *) NEED=restart ;;
    esac
    if [ "$op" = D ]; then
      # Scripts and data are ours alone; a config the pack drops stays (the mod still needs one).
      case "$rel" in kubejs/*|datapacks/*) rm -rf "${SRV:?}/$rel" ;; esac
      rm -rf "${D:?}/pack/$rel"
      say "  removed $rel"
    else
      mkdir -p "$(dirname "$SRV/$rel")" "$(dirname "$D/pack/$rel")"
      cp -r "$PACK/$rel" "$(dirname "$SRV/$rel")/"
      cp -r "$PACK/$rel" "$(dirname "$D/pack/$rel")/"
      say "  $rel"
    fi
  done < <(sync_changes)
}

# /reload answers at once and reloads in the background; the log says "Reloaded with ..." when it is done.
wait_reloaded() {
  local a i
  read -r a _ <<<"$1"
  for i in $(seq 1 120); do
    tail -n +"$((a + 1))" "$SRV/logs/latest.log" 2>/dev/null | grep -q 'Reloaded with' && return 0
    sleep 0.5
  done
  say "no 'Reloaded with' in the log after 60s"
}

# New lines in the server log and KubeJS's own log since a mark (line counts), filtered to script errors.
log_mark() { echo "$(wc -l < "$SRV/logs/latest.log" 2>/dev/null || echo 0) $(wc -l < "$SRV/logs/kubejs/server.log" 2>/dev/null || echo 0)"; }
new_errors() {
  local a b
  read -r a b <<<"$1"
  # Not every ERROR: a /reload logs mods' own (Curios on optional cataclysm ids), as on staging (AGENTS.md step 4).
  { tail -n +"$((a + 1))" "$SRV/logs/latest.log" 2>/dev/null | grep -E 'ERROR.*KubeJS|\[ttl\].*failed'
    tail -n +"$((b + 1))" "$SRV/logs/kubejs/server.log" 2>/dev/null | grep -E '\[(ERROR|WARN)\]|\[ttl\].*failed'; } | head -20 || true
}

sync_pack() {
  local mark errs
  running || die "the local server is not running (tools/local.sh up)"
  if mods_changed; then
    say "mods, the pack's versions or mod/ changed: full refresh and restart"
    stop_server; do_up; return
  fi
  apply_changes
  [ "$N" -gt 0 ] || { say "nothing changed since the last up/sync"; return 0; }
  rm -rf "$SRV/$LEVEL/datapacks/ttl-overrides" && cp -r "$SRV/datapacks/ttl-overrides" "$SRV/$LEVEL/datapacks/"
  mark=$(log_mark)
  case "$NEED" in
    none)    say "$N change(s); nothing to reload" ;;
    reload)  say "$N change(s); /reload"
             out=$(rcon_once "reload")
             if grep -qE "$FAILED_RE" <<<"$(plain <<<"$out")"; then printf '%s\n' "$out" >&2; die "/reload was refused"; fi
             wait_reloaded "$mark" ;;
    restart) say "$N change(s) need a restart (startup scripts or mod config)"
             stop_server; configure; start_server; wait_ready; return ;;
  esac
  sleep 1
  errs=$(new_errors "$mark")
  if [ -n "$errs" ]; then say "errors after the reload:"; printf '%s\n' "$errs" >&2; return 1; fi
}

# --- commands --------------------------------------------------------------------------------------------
# A warm up/restart only redoes what changed: packwiz-installer when the mod list or versions changed (or on
# TTL_LOCAL_FULL=1), gradle when mod/ changed, otherwise it copies the changed pack files like sync does.
do_up() {
  local t0 first=
  t0=$(now)
  pid_alive && { say "already running; use sync (scripts/data/config) or restart"; return 0; }
  mkdir -p "$SRV" "$STATE"
  [ -d "$SRV/$LEVEL" ] || first=1
  install_neoforge
  if [ -n "${TTL_LOCAL_FULL:-}" ] || [ ! -d "$D/pack" ] || [ "$(mods_hash)" != "$(cat "$STATE/mods.sha" 2>/dev/null)" ]; then
    install_pack
  else
    apply_changes
    say "pack: $N changed file(s) copied (mods unchanged, packwiz-installer skipped)"
  fi
  if [ -n "${TTL_LOCAL_FULL:-}" ] || mods_changed; then install_mod; fi
  configure
  start_server
  wait_ready
  if [ -n "$first" ] && [ ! -d "$SNAPS/base" ]; then
    # Let the start-up placements (mortal spawn, landmarks ~45 s after start) finish, then keep this world.
    say "first boot: waiting for the start-up placements, then saving snapshot 'base'"
    wait_settled 5400
    stop_server; snapshot_save base; start_server; wait_ready
  fi
  say "up in $(( $(now) - t0 ))s"
}

# Tests that cannot run on this PC; they print "skipped (<reason>)". Keep the reasons short and true.
# None so far: every test mutes Discord, /bug saves to ttl-reports/ without a token, BlueMap runs here too.
# Add `<name>) echo "<reason>" ;;` when a test truly needs staging (and say why in docs/server.md).
ingame_skip_reason() {
  case "$1" in
    *) ;;
  esac
}

# verify [<ref>]: the integration gate before a deploy (docs/server.md "Local testing", "The deploy gate"). Checks out the
# exact commit (default: origin/main after a fetch) in a dedicated worktree ($D/verify-src, reused: only changed files are
# rewritten), restarts this server on it with that worktree's own local.sh (pack, mods, the ttl-portals build), runs test all
# and posts the GitHub commit status `local-test-all` on that SHA: success, or failure with the failing tests' names.
# ttl-ops deploys a main commit to staging only when it carries `local-test-all = success` (or `deploy-override`).
# TTL_VERIFY_NO_STATUS=1 runs it without posting. The full output is kept in $D/verify/<sha>.txt.
VERIFY_CONTEXT=local-test-all
post_status() {  # sha state description
  [ -z "${TTL_VERIFY_NO_STATUS:-}" ] || { say "status not posted (TTL_VERIFY_NO_STATUS): $2 $3"; return 0; }
  command -v gh >/dev/null || die "gh (GitHub CLI) not found; the status cannot be posted"
  (cd "$ROOT" && gh api -X POST "repos/{owner}/{repo}/statuses/$1" -f state="$2" -f context="$VERIFY_CONTEXT" \
     -f description="$(printf '%s' "$3" | cut -c1-139)" >/dev/null) || die "posting the $VERIFY_CONTEXT status failed"
  say "status $VERIFY_CONTEXT = $2 on ${1:0:7}: $3"
}
do_verify() {
  local ref=${1:-origin/main} sha vw out log rc fails names t0
  t0=$(now)
  git -C "$ROOT" fetch -q origin || die "git fetch failed"
  sha=$(git -C "$ROOT" rev-parse --verify -q "$ref^{commit}") || die "unknown ref $ref"
  vw=$D/verify-src
  if git -C "$vw" rev-parse --git-dir >/dev/null 2>&1; then
    git -C "$vw" checkout -q -f --detach "$sha" && git -C "$vw" clean -qfd -e mod/build -e mod/.gradle || die "cannot check out $sha in $vw"
  else
    rm -rf "$vw"; git -C "$ROOT" worktree prune
    git -C "$ROOT" worktree add -q --detach "$vw" "$sha" || die "cannot add the worktree $vw"
  fi
  say "verify ${sha:0:7} ($(git -C "$vw" log -1 --format=%s | cut -c1-70)) in $(winpath "$vw")"
  mkdir -p "$D/verify"
  log=$D/verify/$sha.txt
  # The worktree's own local.sh: its pack, its mod/ and its tests, on this server, under this run's lock. A restart, not a
  # /reload: staging's deploy is a restart too, and state that scripts keep in memory (TtlDiscordStory's per-bot line
  # counters) did not survive the reloads of a sync (verify of 4addb5b, `bosses`: "boss lines: expected 1, got 0").
  export TTL_LOCAL_DIR=$D TTL_LOCAL_LOCK_HELD=$LOCK_TOKEN
  if pid_alive; then bash "$vw/tools/local.sh" restart || die "restart at ${sha:0:7} failed; no status posted"
  else bash "$vw/tools/local.sh" up || die "up at ${sha:0:7} failed; no status posted"; fi
  rc=0
  bash "$vw/tools/local.sh" test all 2>&1 | tee "$log" || rc=$?
  [ "$(git -C "$vw" rev-parse HEAD)" = "$sha" ] || die "the verify worktree moved during the run; no status posted"
  if ! grep -qE '^[0-9]+ failing$' "$log"; then
    die "test all did not finish (no 'N failing' line; see $(winpath "$log")); no status posted"
  fi
  fails=$(grep -E '^[0-9]+ failing$' "$log" | tail -1 | cut -d' ' -f1)
  if [ "$rc" -eq 0 ] && [ "$fails" = 0 ]; then
    post_status "$sha" success "test-all green on the local Lerfing server ($(( ($(now) - t0) / 60 )) min)"
  else
    names=$(grep -vE '^[0-9]+ failing$| ok$| skipped' "$log" | grep -E '^[a-z0-9_]+ +' | awk '{print $1}' | paste -sd, - | sed 's/,/, /g')
    post_status "$sha" failure "$fails failing: ${names:-see the local log}"
    return 1
  fi
}

case "${1:-}" in
  up|down|restart|sync|test|snapshot|reset|verify) lock_take "$*" ;;
esac
case "${1:-}" in
  up)       do_up ;;
  down)     stop_server ;;
  restart)  t0=$(now); stop_server; do_up; say "restart in $(( $(now) - t0 ))s" ;;
  status)   if running; then say "running (pid $(cat "$STATE/server.pid")), $(rcon_once list | head -1)"; else say "not running"; fi
            if [ -d "$LOCK" ]; then say "in use: pid $(lock_owner)"; else say "free (no local.sh holds it)"; fi
            say "folder: $(winpath "$D")" ;;
  verify)   do_verify "${2:-}" ;;
  logs)     tail -n "${2:-300}" "$SRV/logs/latest.log" ;;
  follow)   tail -n 50 -f "$SRV/logs/latest.log" ;;
  rcon)     rcon_once "${2:?usage: local.sh rcon \"<command>\"}" ;;
  sync)     t0=$(now); sync_pack; say "sync in $(( $(now) - t0 ))s" ;;
  test)
    running || die "the local server is not running (tools/local.sh up)"
    wait_settled
    rcon_open
    if [ "${2:?usage: local.sh test <name>|all}" = all ]; then
      mkdir -p "$D/test-out"; rm -f "$D/test-out"/*.out
      t0=$(now)
      INGAME_OUT=$D/test-out ingame_test_all && rc=0 || rc=$?
      say "test-all in $(( $(now) - t0 ))s; outputs in $(winpath "$D/test-out")"
      exit $rc
    fi
    ingame_test "$2" ;;
  snapshot) running && stop_server && was=1 || was=; snapshot_save "${2:-base}"; [ -z "$was" ] || { start_server; wait_ready; } ;;
  reset)    t0=$(now); stop_server; snapshot_restore "${2:-base}"; configure; start_server; wait_ready; say "reset in $(( $(now) - t0 ))s" ;;
  where)    winpath "$D"; echo ;;
  *) echo "usage: local.sh up|down|restart|status|logs [n]|follow|rcon \"<cmd>\"|sync|test <name>|all|verify [<ref>]|snapshot [name]|reset [name]|where" >&2; exit 2 ;;
esac
