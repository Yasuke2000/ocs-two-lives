#!/bin/bash
# Keeps the Discord #roadmap channel in sync with docs/roadmap-public.md: exactly ONE bot message per section
# (Live / Being built / Planned), EDITED in place, never posted a second time.
#   - the sections are the blocks after the file's header, separated by lines that are exactly `---`; a block whose
#     first line starts with "# " (the header) is not posted. Each block is one message (max 2000 characters after
#     the channel mentions are filled in; the file keeps itself under 1900). {#name} becomes a clickable channel mention.
#   - no ids are stored: the messages are found again in the channel. They are the bot's messages in #roadmap after the
#     pinned how-to, oldest first. A section edits the message whose first line equals the section's first line; a
#     section whose heading was renamed edits the first message no other section matched (so the order is kept).
#     Only when the channel holds fewer section messages than the file (the first run) are the missing ones posted.
#   - unchanged text: nothing is sent. Extra bot messages (more than the file has sections) are reported, not deleted.
# The channel and its pinned "How to use this channel" message come from tools/discord_setup.sh: run that first, so
# the how-to stays the first message of the channel.
#
# Run it ON the cluster node: the bot token is read from the Kubernetes secret at runtime only and is never printed,
# logged or written to a file (it is also kept out of the process arguments). Copy the file to the node first:
#   ssh -o LogLevel=ERROR root@100.109.28.21 'cat > /tmp/roadmap-public.md' < docs/roadmap-public.md
#   ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- /tmp/roadmap-public.md' < tools/post_roadmap.sh
# Without network or token: `bash tools/post_roadmap.sh docs/roadmap-public.md --dry-run` prints the messages.
# Needs bash 4, curl and jq (all on the node).
set -u

G=1572376519551090728
API=https://discord.com/api/v10
HEAD='**How to use this channel / Hoe gebruik je dit kanaal**'
CHANNEL=roadmap
FILE=${1:-}; DRY=0; [ "${2:-}" = "--dry-run" ] && DRY=1
[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "usage: post_roadmap.sh <docs/roadmap-public.md> [--dry-run]" >&2; exit 1; }

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
CODE=0
FAILS=0

# Blocks -> messages (JSON array of strings); the header block ("# ...") is dropped.
jq -Rs 'gsub("\r";"") | split("\n---\n") | map(sub("^[\n ]+";"") | sub("[\n ]+$";""))
        | map(select(length>0 and (startswith("# ")|not)))' "$FILE" > "$W/msgs.json" \
  || { echo "cannot parse $FILE" >&2; exit 1; }
COUNT=$(jq length "$W/msgs.json")
[ "$COUNT" -gt 0 ] || { echo "no sections in $FILE" >&2; exit 1; }
[ "$(jq '[.[]|split("\n")[0]]|unique|length' "$W/msgs.json")" = "$COUNT" ] \
  || { echo "two sections share the same first line; every section needs its own heading" >&2; exit 1; }

if [ $DRY = 1 ]; then
  for i in $(seq 0 $((COUNT-1))); do
    text=$(jq -r ".[$i]" "$W/msgs.json"); text=$(printf '%s' "$text" | sed -E 's/\{#([a-z0-9-]+)\}/#\1/g')
    printf '=== section %s/%s (%s chars)\n%s\n' $((i+1)) "$COUNT" "$(jq -r ".[$i]|length" "$W/msgs.json")" "$text"
  done
  exit 0
fi

T=$(k3s kubectl -n ocs-two-lives get secret discord-bot -o jsonpath="{.data.token}" | base64 -d)
[ -n "$T" ] || { echo "no token in secret discord-bot" >&2; exit 1; }

# api METHOD PATH [JSON_FILE] -> body in $W/out, HTTP status in $CODE. Waits and retries on 429.
# The token goes to curl through a config on stdin (printf is a builtin), not through argv.
api() {
  local m=$1 p=$2 f=${3:-} n=0 ra
  while :; do
    if [ -n "$f" ]; then
      printf 'header = "Authorization: Bot %s"\n' "$T" | curl -s -K - -o "$W/out" -w '%{http_code}' -X "$m" \
        -H 'Content-Type: application/json' --data-binary @"$f" "$API$p" > "$W/code"
    else
      printf 'header = "Authorization: Bot %s"\n' "$T" | curl -s -K - -o "$W/out" -w '%{http_code}' "$API$p" > "$W/code"
    fi
    CODE=$(cat "$W/code")
    if [ "$CODE" = 429 ] && [ $n -lt 5 ]; then
      ra=$(jq -r '.retry_after // 2' "$W/out" 2>/dev/null); ra=${ra%.*}; sleep $(( ${ra:-2} + 1 )); n=$((n+1)); continue
    fi
    sleep 1; return 0
  done
}
errtext() { jq -r '"\(.code // "") \(.message // .)"' "$W/out" 2>/dev/null | head -c 200; }

api GET "/guilds/$G/channels"; [ "$CODE" = 200 ] || { echo "cannot list channels: HTTP $CODE $(errtext)" >&2; exit 1; }
cp "$W/out" "$W/channels.json"
CH=$(jq -r --arg n "$CHANNEL" '[.[]|select(.type==0 and .name==$n)][0].id // empty' "$W/channels.json")
[ -n "$CH" ] || { echo "#$CHANNEL not found: run tools/discord_setup.sh first" >&2; exit 1; }
api GET "/users/@me"; BOT=$(jq -r '.id // empty' "$W/out")
[ -n "$BOT" ] || { echo "cannot identify the bot: HTTP $CODE $(errtext)" >&2; exit 1; }
echo "#$CHANNEL ($CH)"

# The bot's messages in the channel (a read-only channel: at most a handful), oldest first.
api GET "/channels/$CH/messages?limit=100"; [ "$CODE" = 200 ] || { echo "cannot read #$CHANNEL: HTTP $CODE $(errtext)" >&2; exit 1; }
jq --arg b "$BOT" '[.[]|select(.author.id==$b)]|sort_by((.id|length), .id)' "$W/out" > "$W/bot.json"
jq -e --arg h "$HEAD" 'any(.[]; .content|startswith($h))' "$W/bot.json" >/dev/null \
  || { echo "the pinned how-to is missing in #$CHANNEL: run tools/discord_setup.sh first (it must be the first message)" >&2; exit 1; }
jq --arg h "$HEAD" '[.[]|select(.content|startswith($h)|not)|{id, content, first:(.content|split("\n")[0])}]' "$W/bot.json" > "$W/mine.json"
mapfile -t LID < <(jq -r '.[].id' "$W/mine.json")
mapfile -t LFIRST < <(jq -r '.[].first' "$W/mine.json")

render() { # replace {#name} by <#id> (text and forum channels)
  local t=$1 n id
  while read -r n id; do t=${t//\{#$n\}/<#$id>}; done < <(jq -r '.[]|select(.type==0 or .type==15)|"\(.name) \(.id)"' "$W/channels.json")
  printf '%s' "$t"
}

# Which existing message each section edits: same first line first, then the first unclaimed one in order.
declare -A CLAIMED=()
declare -a TARGET=()
for i in $(seq 0 $((COUNT-1))); do
  first=$(jq -r ".[$i]|split(\"\n\")[0]" "$W/msgs.json"); TARGET[$i]=""
  for j in "${!LID[@]}"; do
    if [ -z "${CLAIMED[$j]:-}" ] && [ "${LFIRST[$j]}" = "$first" ]; then TARGET[$i]=$j; CLAIMED[$j]=1; break; fi
  done
done
for i in $(seq 0 $((COUNT-1))); do
  [ -z "${TARGET[$i]}" ] || continue
  for j in "${!LID[@]}"; do
    if [ -z "${CLAIMED[$j]:-}" ]; then TARGET[$i]=$j; CLAIMED[$j]=1; break; fi
  done
done

for i in $(seq 0 $((COUNT-1))); do
  text=$(render "$(jq -r ".[$i]" "$W/msgs.json")"); first=${text%%$'\n'*}
  len=$(jq -n --arg c "$text" '$c|length')
  if [ "$len" -gt 2000 ]; then echo "FAILED section $((i+1)): $len chars (> 2000): shorten it in the file"; FAILS=$((FAILS+1)); continue; fi
  jq -n --arg c "$text" '{content:$c, allowed_mentions:{parse:[]}}' > "$W/body.json"
  j=${TARGET[$i]}
  if [ -n "$j" ]; then
    mid=${LID[$j]}
    if [ "$(jq -r --arg i "$mid" '.[]|select(.id==$i)|.content' "$W/mine.json")" = "$text" ]; then
      echo "  unchanged ($mid): $first"; continue
    fi
    api PATCH "/channels/$CH/messages/$mid" "$W/body.json"
    if [ "$CODE" = 200 ]; then echo "  edited ($mid): $first"; else echo "FAILED edit ($mid): HTTP $CODE $(errtext): $first"; FAILS=$((FAILS+1)); fi
  else
    [ "${#LID[@]}" -eq 0 ] || echo "WARNING: section $((i+1)) had no message left to edit; it is posted at the bottom (check the order)"
    api POST "/channels/$CH/messages" "$W/body.json"
    if [ "$CODE" = 200 ]; then echo "  posted ($(jq -r .id "$W/out")): $first"; else echo "FAILED post: HTTP $CODE $(errtext): $first"; FAILS=$((FAILS+1)); fi
  fi
done
extra=$(( ${#LID[@]} - ${#CLAIMED[@]} ))
[ "$extra" -le 0 ] || echo "WARNING: $extra extra bot message(s) in #$CHANNEL that match no section; delete them by hand if they are stale"
echo "done, $FAILS problem(s)"
[ $FAILS = 0 ]
