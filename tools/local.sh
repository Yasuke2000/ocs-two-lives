#!/usr/bin/env bash
# A local copy of the staging server on this PC, for testing a change in minutes before it goes through
# push -> ttl-ops deploy -> test-all on the homelab. Git Bash on Windows (Linux and WSL work too). Needs Java 21,
# Python 3 and packwiz (~/go/bin is searched). docs/server.md "Local testing" explains the loop.
#
# Same as staging: NeoForge + the pack's server-side mods installed by packwiz-installer (what the itzg image runs),
# the world datapack, level world-ttl, hard, 8 simulation chunks, flight on, Aikar flags. Different on purpose:
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
# Each command starts TTL_LOCAL_TICKS game ticks after the previous one ended: on staging a command is a kubectl exec
# (~0.17 s, 3 ticks), and tests count on what a script schedules a tick later (the Corridor after a `kill`) being done.
TICKS=${TTL_LOCAL_TICKS:-1}
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
  rm -f "$SRV/logs/latest.log"
  say "starting (heap $MEMORY, game 127.0.0.1:$PORT, RCON 127.0.0.1:$RCON_PORT)"
  # No bug-report token: /bug saves to ttl-reports/ instead of opening GitHub issues. -Dttl.local marks the process.
  (cd "$SRV" && exec env -u TTL_GITHUB_TOKEN -u TTL_REPORT_REPO -u CFG_DISCORD_TOKEN \
     "$java" -Dttl.local=1 @user_jvm_args.txt "@$args" nogui < /dev/null > "$SRV/console.log" 2>&1) &
  local p=$! i
  if [ -n "$WIN" ]; then
    # Git Bash pids are not Windows pids; find java.exe by its marker so tasklist/taskkill can see it.
    p=
    for i in 1 2 3 4 5 6 7 8 9 10; do
      p=$(powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | Where-Object { \$_.CommandLine -like '*-Dttl.local=1*' } | Select-Object -First 1).ProcessId" 2>/dev/null | tr -d '\r ')
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
    [ $(( $(now) - t0 )) -lt "$deadline" ] || { printf '%s
' "$left" >&2; die "start-up builds still pending after ${deadline}s"; }
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
  say "ttl-portals: local build $(basename "$jar")"
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
  set_prop simulation-distance 8
  set_prop spawn-protection 0
  set_prop allow-flight true
  set_prop white-list false
  set_prop enforce-whitelist false
  set_prop motd "OCS Tensura: Two Lives - local"
  # Staging: MEMORY=8G + USE_AIKAR_FLAGS (itzg's G1 set for heaps under 12 GB).
  cat > "$SRV/user_jvm_args.txt" <<EOF
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
#   kubejs/server_scripts                                  -> /kubejs reload server_scripts
#   kubejs/data, datapacks, config/ttl, config/ftbquests   -> /reload (data, scripts and quest files)
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
  [ -n "$(find "$ROOT/mod/src" "$ROOT/mod/build.gradle" "$ROOT/mod/gradle.properties" -newer "$SRV/mods/ttl-portals-local.jar" -type f 2>/dev/null | head -1)" ]
}

# Copies the changes into the server and the baseline; sets NEED to none, scripts, reload or restart and N to the count.
apply_changes() {
  local op rel
  NEED=none; N=0
  while read -r op rel; do
    N=$((N + 1))
    case "$rel" in
      kubejs/assets/*|kubejs/client_scripts/*) ;;
      kubejs/server_scripts*) [ "$NEED" = none ] && NEED=scripts ;;
      kubejs/data*|datapacks*|config/ttl*|config/ftbquests*) [ "$NEED" = restart ] || NEED=reload ;;
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

# New lines in the server log and KubeJS's own log since a mark (line counts), filtered to script errors.
log_mark() { echo "$(wc -l < "$SRV/logs/latest.log" 2>/dev/null || echo 0) $(wc -l < "$SRV/logs/kubejs/server.log" 2>/dev/null || echo 0)"; }
new_errors() {
  local a b
  read -r a b <<<"$1"
  { tail -n +"$((a + 1))" "$SRV/logs/latest.log" 2>/dev/null; tail -n +"$((b + 1))" "$SRV/logs/kubejs/server.log" 2>/dev/null; } \
    | grep -E 'ERROR|\[ttl\].*failed' | head -20 || true
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
    scripts) say "$N change(s); kubejs reload server_scripts"; rcon_once "kubejs reload server_scripts" | tail -3 ;;
    reload)  say "$N change(s); /reload"; rcon_once "reload" | tail -3 ;;
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

case "${1:-}" in
  up)       do_up ;;
  down)     stop_server ;;
  restart)  t0=$(now); stop_server; do_up; say "restart in $(( $(now) - t0 ))s" ;;
  status)   if running; then say "running (pid $(cat "$STATE/server.pid")), $(rcon_once list | head -1)"; else say "not running"; fi; say "folder: $(winpath "$D")" ;;
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
  *) echo "usage: local.sh up|down|restart|status|logs [n]|follow|rcon \"<cmd>\"|sync|test <name>|all|snapshot [name]|reset [name]|where" >&2; exit 2 ;;
esac
