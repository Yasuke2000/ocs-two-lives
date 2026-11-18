#!/bin/bash
# Posts a patch-notes file (docs/patch-notes/<date>.md) to the Discord #patch-notes channel as bot messages.
#   - the file is cut into messages at lines that are exactly `---`; a block over 1900 characters is split further
#     at blank lines and the extra parts get the first line of the block + " (2/3)", " (3/3)", ...
#   - {#name} becomes a clickable channel mention (same convention as tools/discord_setup.sh)
#   - idempotent: when a message of the bot in the channel already has the same first line, it is skipped, so a
#     re-run never double-posts. Messages are only appended (newest at the bottom), never edited or deleted.
# The channel itself is made by tools/discord_setup.sh; run that first.
#
# Run it ON the cluster node: the bot token is read from the Kubernetes secret at runtime only and is never
# printed, logged or written to a file (it is also kept out of the process arguments). The notes are not secret:
# copy the file to the node first, then run the script with its path.
#   ssh -o LogLevel=ERROR root@100.109.28.21 'cat > /tmp/patch-notes.md' < docs/patch-notes/2026-11-18.md
#   ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- /tmp/patch-notes.md' < tools/post_patch_notes.sh
# Without network or token: `bash tools/post_patch_notes.sh <file> --dry-run` prints the messages it would post.
# Needs bash 4, curl and jq (all on the node).
set -u

G=1572376519551090728
API=https://discord.com/api/v10
LIMIT=1900
FILE=${1:-}; DRY=0; [ "${2:-}" = "--dry-run" ] && DRY=1
[ -n "$FILE" ] && [ -f "$FILE" ] || { echo "usage: post_patch_notes.sh <notes file> [--dry-run]" >&2; exit 1; }

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
CODE=0
FAILS=0

# Blocks -> messages (JSON array of strings)
jq -Rs --argjson lim "$LIMIT" '
  gsub("\r";"") | split("\n---\n") | map(sub("^\n+";"") | sub("\n+$";"")) | map(select(length>0))
  | map(
      (split("\n")[0]) as $first
      | (split("\n\n") | reduce .[] as $p ([];
          if length==0 then [$p]
          elif ((.[-1] + "\n\n" + $p)|length) <= $lim then .[-1] += "\n\n" + $p
          else . + [$p] end)) as $parts
      | ($parts|length) as $n
      | [$parts|to_entries[] | if .key==0 then .value else "\($first) (\(.key+1)/\($n))\n\(.value)" end]
    ) | add // []' "$FILE" > "$W/msgs.json" || { echo "cannot parse $FILE" >&2; exit 1; }
COUNT=$(jq length "$W/msgs.json")
[ "$COUNT" -gt 0 ] || { echo "no messages in $FILE" >&2; exit 1; }
for i in $(seq 0 $((COUNT-1))); do
  len=$(jq -r ".[$i]|length" "$W/msgs.json")
  [ "$len" -le 2000 ] || { echo "message $((i+1)) is $len chars (> 2000): add a blank line or a --- to split it" >&2; exit 1; }
done

if [ $DRY = 1 ]; then
  for i in $(seq 0 $((COUNT-1))); do printf '=== message %s/%s (%s chars)\n%s\n' $((i+1)) "$COUNT" "$(jq -r ".[$i]|length" "$W/msgs.json")" "$(jq -r ".[$i]" "$W/msgs.json")"; done
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
CH=$(jq -r '[.[]|select(.type==0 and .name=="patch-notes")][0].id // empty' "$W/channels.json")
[ -n "$CH" ] || { echo "#patch-notes not found: run tools/discord_setup.sh first" >&2; exit 1; }
BOT=$(printf 'header = "Authorization: Bot %s"\n' "$T" | curl -s -K - "$API/users/@me" | jq -r .id)
[ -n "$BOT" ] && [ "$BOT" != null ] || { echo "cannot identify the bot" >&2; exit 1; }
echo "#patch-notes ($CH)"

# First lines of the bot's messages already in the channel (up to 500 newest)
: > "$W/existing.txt"; before=""
for page in 1 2 3 4 5; do
  api GET "/channels/$CH/messages?limit=100${before}"; [ "$CODE" = 200 ] || break
  jq -r --arg b "$BOT" '.[]|select(.author.id==$b)|.content|split("\n")[0]' "$W/out" >> "$W/existing.txt"
  [ "$(jq length "$W/out")" -eq 100 ] || break
  before="&before=$(jq -r '.[-1].id' "$W/out")"
done

render() { # replace {#name} by <#id>
  local t=$1 n id
  while read -r n id; do t=${t//\{#$n\}/<#$id>}; done < <(jq -r '.[]|select(.type==0)|"\(.name) \(.id)"' "$W/channels.json")
  printf '%s' "$t"
}

for i in $(seq 0 $((COUNT-1))); do
  text=$(jq -r ".[$i]" "$W/msgs.json"); first=${text%%$'\n'*}
  if grep -qxF -- "$first" "$W/existing.txt"; then echo "  skip (already posted): $first"; continue; fi
  jq -n --arg c "$(render "$text")" '{content:$c, allowed_mentions:{parse:[]}}' > "$W/body.json"
  api POST "/channels/$CH/messages" "$W/body.json"
  if [ "$CODE" = 200 ]; then echo "  posted ($(jq -r .id "$W/out")): $first"
  else echo "FAILED post: HTTP $CODE $(errtext): $first"; FAILS=$((FAILS+1)); fi
done
echo "done, $FAILS problem(s)"
[ $FAILS = 0 ]
