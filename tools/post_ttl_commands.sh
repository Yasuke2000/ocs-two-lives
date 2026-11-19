#!/bin/bash
# Posts the /ttl command reference to the Discord #dev-chat channel and keeps it up to date: re-runnable, never doubles.
#   - the messages come from `python tools/gen_ttl_commands.py --discord` (docs/dev/ttl-commands.md is the same text in
#     one file): a header message and one or more messages per group, separated by lines that are exactly `---`, each at
#     most 2000 characters. Every message ends with the line `-# /ttl command reference <n>/<total>`; that line is how the
#     bot finds its own messages again, so no ids are stored and nobody else's message is ever touched.
#   - the first message is the header ("/ttl command reference, generated from the repo, updated <date>"; {date} is
#     filled in here, today unless TTL_DATE is set). It is pinned.
#   - a re-run edits the bot's reference messages in place, in order (same text: nothing is sent). More messages than
#     before: the extra ones are posted at the bottom. Fewer: the surplus reference messages are deleted. Messages of
#     other people and the bot's other messages (the channel's how-to) are not touched.
# The channel comes from tools/discord_setup.sh (#dev-chat, category DEVELOPMENT): run that first.
#
# Run it ON the cluster node: the bot token is read from the Kubernetes secret at runtime only and is never printed,
# logged or written to a file (it is also kept out of the process arguments). Copy the messages to the node first:
#   python tools/gen_ttl_commands.py --discord | ssh -o LogLevel=ERROR root@100.109.28.21 'cat > /tmp/ttl-commands-discord.md'
#   ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- /tmp/ttl-commands-discord.md' < tools/post_ttl_commands.sh
# Without network or token: `bash tools/post_ttl_commands.sh <file> --dry-run` prints the messages it would post.
# Needs bash 4, curl and jq (all on the node).
set -u

G=1572376519551090728
API=https://discord.com/api/v10
CHANNEL=dev-chat
MARK='-# /ttl command reference '
FILE=${1:-}; DRY=0; [ "${2:-}" = "--dry-run" ] && DRY=1
[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "usage: post_ttl_commands.sh <messages file from gen_ttl_commands.py --discord> [--dry-run]" >&2; exit 1; }
TODAY=${TTL_DATE:-$(date +%d/%m/%Y)}

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
CODE=0
FAILS=0

# Blocks -> messages (JSON array of strings); {date} is filled in.
jq -Rs --arg d "$TODAY" 'gsub("\r";"") | split("\n---\n") | map(sub("^[\n ]+";"") | sub("[\n ]+$";"") | gsub("\\{date\\}";$d))
        | map(select(length>0))' "$FILE" > "$W/msgs.json" || { echo "cannot parse $FILE" >&2; exit 1; }
COUNT=$(jq length "$W/msgs.json")
[ "$COUNT" -gt 1 ] || { echo "no messages in $FILE" >&2; exit 1; }
for i in $(seq 0 $((COUNT-1))); do
  jq -e --arg m "$MARK" --argjson i "$i" --argjson n "$COUNT" '.[$i] | endswith("\n" + $m + "\($i+1)/\($n)")' "$W/msgs.json" >/dev/null \
    || { echo "message $((i+1)) does not end with the marker line '$MARK$((i+1))/$COUNT': regenerate the file with gen_ttl_commands.py --discord" >&2; exit 1; }
  len=$(jq -r ".[$i]|length" "$W/msgs.json")
  [ "$len" -le 2000 ] || { echo "message $((i+1)) is $len chars (> 2000)" >&2; exit 1; }
done

if [ $DRY = 1 ]; then
  for i in $(seq 0 $((COUNT-1))); do
    printf '=== message %s/%s (%s chars)\n%s\n' $((i+1)) "$COUNT" "$(jq -r ".[$i]|length" "$W/msgs.json")" "$(jq -r ".[$i]" "$W/msgs.json")"
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
    elif [ "$m" = GET ]; then
      printf 'header = "Authorization: Bot %s"\n' "$T" | curl -s -K - -o "$W/out" -w '%{http_code}' "$API$p" > "$W/code"
    else
      printf 'header = "Authorization: Bot %s"\n' "$T" | curl -s -K - -o "$W/out" -w '%{http_code}' -X "$m" -d '' "$API$p" > "$W/code"
    fi
    CODE=$(cat "$W/code")
    if [ "$CODE" = 429 ] && [ $n -lt 5 ]; then
      ra=$(jq -r '.retry_after // 2' "$W/out" 2>/dev/null); ra=${ra%.*}; sleep $(( ${ra:-2} + 1 )); n=$((n+1)); continue
    fi
    sleep 1; return 0
  done
}
errtext() { jq -r '"\(.code // "") \(.message // .)"' "$W/out" 2>/dev/null | head -c 200; }
fail() { echo "FAILED $1: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1)); }

api GET "/guilds/$G/channels"; [ "$CODE" = 200 ] || { echo "cannot list channels: HTTP $CODE $(errtext)" >&2; exit 1; }
CH=$(jq -r --arg n "$CHANNEL" '[.[]|select(.type==0 and .name==$n)][0].id // empty' "$W/out")
[ -n "$CH" ] || { echo "#$CHANNEL not found: run tools/discord_setup.sh first" >&2; exit 1; }
api GET "/users/@me"; BOT=$(jq -r '.id // empty' "$W/out")
[ -n "$BOT" ] || { echo "cannot identify the bot: HTTP $CODE $(errtext)" >&2; exit 1; }
echo "#$CHANNEL ($CH), $COUNT message(s), dated $TODAY"

# The bot's reference messages in the channel (the newest 500 messages are searched), oldest first.
echo '[]' > "$W/all.json"; before=""
for page in 1 2 3 4 5; do
  api GET "/channels/$CH/messages?limit=100${before}"; [ "$CODE" = 200 ] || { echo "cannot read #$CHANNEL: HTTP $CODE $(errtext)" >&2; exit 1; }
  jq -s 'add' "$W/all.json" "$W/out" > "$W/all2.json" && mv "$W/all2.json" "$W/all.json"
  [ "$(jq length "$W/out")" -eq 100 ] || break
  before="&before=$(jq -r '.[-1].id' "$W/out")"
done
jq --arg b "$BOT" --arg m "$MARK" '[.[]|select(.author.id==$b and (.content|test("\n" + $m + "[0-9]+/[0-9]+$")))
     |{id, content}]|sort_by((.id|length), .id)' "$W/all.json" > "$W/mine.json"
mapfile -t LID < <(jq -r '.[].id' "$W/mine.json")
echo "found ${#LID[@]} earlier reference message(s)"

for i in $(seq 0 $((COUNT-1))); do
  text=$(jq -r ".[$i]" "$W/msgs.json"); first=${text%%$'\n'*}
  jq -n --arg c "$text" '{content:$c, allowed_mentions:{parse:[]}}' > "$W/body.json"
  if [ "$i" -lt "${#LID[@]}" ]; then
    mid=${LID[$i]}
    if [ "$(jq -r --arg i "$mid" '.[]|select(.id==$i)|.content' "$W/mine.json")" = "$text" ]; then
      echo "  $((i+1))/$COUNT unchanged ($mid)"
    else
      api PATCH "/channels/$CH/messages/$mid" "$W/body.json"
      if [ "$CODE" = 200 ]; then echo "  $((i+1))/$COUNT edited ($mid): $first"; else fail "edit $((i+1))/$COUNT ($mid)"; fi
    fi
  else
    api POST "/channels/$CH/messages" "$W/body.json"
    if [ "$CODE" = 200 ]; then mid=$(jq -r .id "$W/out"); LID[$i]=$mid; echo "  $((i+1))/$COUNT posted ($mid): $first"
    else fail "post $((i+1))/$COUNT"; break; fi
  fi
done

# Surplus reference messages of an earlier, longer run.
for j in $(seq "$COUNT" $(( ${#LID[@]} - 1 ))); do
  [ "$j" -lt "${#LID[@]}" ] || break
  api DELETE "/channels/$CH/messages/${LID[$j]}"
  if [ "$CODE" = 204 ]; then echo "  deleted surplus message (${LID[$j]})"; else fail "delete surplus (${LID[$j]})"; fi
done

# Pin the header (first message); drop the "pinned a message" system line so the reference stays in one piece.
HEAD_ID=${LID[0]:-}
if [ -n "$HEAD_ID" ]; then
  api GET "/channels/$CH/pins"
  if [ "$CODE" = 200 ]; then
    if jq -e --arg i "$HEAD_ID" 'if type=="array" then . else (.items // [] | map(.message // .)) end | any(.[]; .id==$i)' "$W/out" >/dev/null; then
      echo "  header already pinned"
    else
      api PUT "/channels/$CH/pins/$HEAD_ID"
      if [ "$CODE" = 204 ]; then
        echo "  header pinned"
        api GET "/channels/$CH/messages?limit=5"
        if [ "$CODE" = 200 ]; then
          for id in $(jq -r '.[]|select(.type==6)|.id' "$W/out"); do api DELETE "/channels/$CH/messages/$id"; done
        fi
      else fail "pin the header ($HEAD_ID)"; fi
    fi
  else fail "read the pins"; fi
fi
echo "done, $FAILS problem(s)"
[ $FAILS = 0 ]
