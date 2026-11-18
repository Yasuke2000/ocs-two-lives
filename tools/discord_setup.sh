#!/bin/bash
# Sets up the OCS Tensura: Two Lives Discord server for new players (idempotent, safe to re-run):
#   - creates #chat, #contribute, #dev-chat when missing and sets their topics (and #welcome's topic)
#   - edits/posts the welcome messages in #welcome (the bot's own messages)
#   - posts and pins ONE "How to use this channel / Hoe gebruik je dit kanaal" message per channel
#     (existing ones are updated in place, never duplicated)
# The texts live in this file; `--export-docs` prints docs/discord-guides.md from them (no network, no token).
#
# Run it ON the cluster node: the bot token is read from the Kubernetes secret at runtime only and is
# never printed, logged or written to a file (it is also kept out of the process arguments).
#   ssh root@100.109.28.21 'bash -s' < tools/discord_setup.sh
#   bash tools/discord_setup.sh --export-docs > docs/discord-guides.md
# Needs bash 4, curl and jq (all on the node). Pinning needs the bot to have Manage Messages (or Pin
# Messages) in the server; without it the posts are still made and the script reports "PIN FAILED".
set -u

G=1572376519551090728
BOT=1572393611990147253
API=https://discord.com/api/v10
HEAD='**How to use this channel / Hoe gebruik je dit kanaal**'
REPO=https://github.com/Yasuke2000/ocs-two-lives
PRISM=$REPO/releases/download/prism-instance/OCS-Two-Lives.zip

read_txt() { IFS= read -r -d '' "$1" || true; }

# ---------------------------------------------------------------------------------------------
# Texts. {#name} becomes a clickable channel mention in Discord (and plain #name in the docs).
# ---------------------------------------------------------------------------------------------

read_txt WELCOME_EN <<'EOF'
**Welcome to OCS Tensura: Two Lives**
A Minecraft modpack server where you live **twice**. First you are an ordinary human in the Mortal Realm: you only live once there, and everything you do counts. When you die, your soul reaches the Spirit Corridor: make your Last Wish, face your Trial and be reborn in the world of *That Time I Got Reincarnated as a Slime*. How you lived shapes who you become.

**How to join**
1. Install **Prism Launcher**, choose Add Instance, Import and paste: <https://github.com/Yasuke2000/ocs-two-lives/releases/download/prism-instance/OCS-Two-Lives.zip>
2. Start the instance. The first launch downloads the mods, so give it a few minutes. The server `molecule-threefold.tun.ply.gg` is already in the list; if not, add it yourself.
3. Join the server. You get a short **code** on screen to link your Discord account (already in game? Type `/discordverify`).
4. Here in Discord, type `/verify <code>` (or DM the code to the bot), then join again. You now have the **Linked** role.
5. Done, have fun! Your Life 1 / Life 2 and karma roles follow automatically.

**Handy commands (in game)**
`/ttl guide` the full guide · `/ttl life` how your life is being judged · `/ttl top` the leaderboard · `/bug <text>` report a problem (it becomes a public GitHub issue)
EOF

read_txt WELCOME_NL <<'EOF'
**Welkom bij OCS Tensura: Two Lives**
Een Minecraft-modpackserver waar je **twee keer** leeft. Eerst als gewone mens in het Mortal Realm: daar leef je maar één keer en alles wat je doet telt. Sterf je, dan komt je ziel in de Spirit Corridor terecht: doe je Last Wish, doorsta je Trial en word herboren in de wereld van *That Time I Got Reincarnated as a Slime*. Hoe je geleefd hebt, bepaalt wie je wordt.

**Zo doe je mee**
1. Installeer **Prism Launcher**, kies Add Instance, Import en plak deze link: <https://github.com/Yasuke2000/ocs-two-lives/releases/download/prism-instance/OCS-Two-Lives.zip>
2. Start de instance. De eerste keer worden de mods gedownload, dat duurt even. De server `molecule-threefold.tun.ply.gg` staat al in de lijst; zo niet, voeg hem zelf toe.
3. Join de server. Je krijgt een korte **code** op je scherm om je Discord-account te koppelen (zit je al in het spel? Typ `/discordverify`).
4. Typ hier in Discord `/verify <code>` (of stuur de code in een privébericht naar de bot) en join opnieuw. Je krijgt nu de rol **Linked**.
5. Klaar, veel plezier! Je rollen Life 1 / Life 2 en karma-niveau volgen vanzelf.

**Handige commando's (in het spel)**
`/ttl guide` de volledige gids · `/ttl life` hoe je leven beoordeeld wordt · `/ttl top` het klassement · `/bug <tekst>` meld een probleem (wordt een publiek GitHub-issue)
EOF

read_txt MAP_EN <<'EOF'
**Channels and roles**
**Info**
- {#welcome}: this start guide
- {#announcements}: news, updates and maintenance
**Play**
- {#chat}: talk about anything, outside the game
- {#minecraft}: live bridge with the game: what you type here shows up in game, and the other way round
- {#story}: deaths, rebirths, Legends and the weekly Hall of Souls
- {#screenshots}: your best builds and moments
- {#leaderboard}: live standings (in game: `/ttl top`)
**Build with us**
- {#ideas-and-feedback}: ideas, feedback and `?bugreport <text>` (linked players)
- {#contribute}: how to help improve the pack
- {#dev-chat}: talk with the people working on the pack and mod
**Server**
- {#logging-and-server-notifactions}: automatic notices (deploys, server up/down)

**Roles** (automatic once linked): **Linked**; **Life 1** / **Life 2**; **Wanderer**, **Survivor**, **Hero**, **Legend** (karma tier, once your first life is judged); **Fallen** (the dark path).
**Bot commands:** `/verify <code>`, `/playerlist`, `/status`, `/help`
EOF

read_txt MAP_NL <<'EOF'
**Kanalen en rollen**
**Info**
- {#welcome}: deze startgids
- {#announcements}: nieuws, updates en onderhoud
**Spelen**
- {#chat}: babbelen over alles, buiten het spel
- {#minecraft}: live koppeling met de game: wat je hier typt zie je in het spel, en omgekeerd
- {#story}: sterfgevallen, wedergeboortes, Legends en het wekelijkse Hall of Souls
- {#screenshots}: je mooiste builds en momenten
- {#leaderboard}: het live klassement (in het spel: `/ttl top`)
**Meebouwen**
- {#ideas-and-feedback}: ideeën, feedback en `?bugreport <tekst>` (gekoppelde spelers)
- {#contribute}: hoe je kan helpen om de pack te verbeteren
- {#dev-chat}: praten met de mensen die aan de pack en de mod werken
**Server**
- {#logging-and-server-notifactions}: automatische meldingen (deploys, server aan/uit)

**Rollen** (automatisch na het koppelen): **Linked**; **Life 1** / **Life 2**; **Wanderer**, **Survivor**, **Hero**, **Legend** (karma-niveau, zodra je eerste leven beoordeeld is); **Fallen** (het donkere pad).
**Bot-commando's:** `/verify <code>`, `/playerlist`, `/status`, `/help`
EOF

read_txt CONTRIB_EN <<'EOF'
**Want to help? Here is how**
**Where:** the GitHub repo <https://github.com/Yasuke2000/ocs-two-lives> (public). All open work is on the project board: <https://github.com/users/Yasuke2000/projects/1> (Triage, To do, In progress, Done).
**Report or suggest (no coding needed)**
- In game: `/bug <what happened>` (adds your position, life and log lines). In Discord: `?bugreport <text>` in {#ideas-and-feedback}. Both become a **public** GitHub issue, so keep private info out.
- On GitHub: Issues, New issue, then pick a form: Bug, Idea, Balance, Build request or World / lore fix.
**Change something yourself**
1. Ask Yasuke for collaborator access to the repo.
2. Pick or open an issue and assign yourself, so others know what you are doing.
3. Make a branch (never commit to `main`), edit, and run `python tools/validate.py` until it says `validation passed`.
4. Open a pull request and link the issue (`Closes #12`).
5. **Nothing reaches `main` (and so the server) without Yasuke's approval**: a PR needs a green `validate` check and his review. Small, focused PRs are reviewed fastest.
6. After the merge the test server picks it up and runs the bot tests. Try it in game.
All details: <https://github.com/Yasuke2000/ocs-two-lives/blob/main/CONTRIBUTING.md>. Questions? Ask in {#dev-chat}.
EOF

read_txt CONTRIB_NL <<'EOF'
**Wil je meehelpen? Zo werkt het**
**Waar:** de GitHub-repo <https://github.com/Yasuke2000/ocs-two-lives> (publiek). Al het openstaande werk staat op het projectbord: <https://github.com/users/Yasuke2000/projects/1> (Triage, To do, In progress, Done).
**Melden of voorstellen (zonder te programmeren)**
- In het spel: `/bug <wat er gebeurde>` (voegt je positie, leven en logregels toe). In Discord: `?bugreport <tekst>` in {#ideas-and-feedback}. Beide worden een **publiek** GitHub-issue, zet er dus geen privégegevens in.
- Op GitHub: Issues, New issue, en kies een formulier: Bug, Idea, Balance, Build request of World / lore fix.
**Zelf iets aanpassen**
1. Vraag Yasuke om collaborator-toegang tot de repo.
2. Kies of open een issue en wijs het aan jezelf toe, zodat iedereen weet waar je mee bezig bent.
3. Maak een branch (nooit rechtstreeks op `main`), pas aan en draai `python tools/validate.py` tot er `validation passed` staat.
4. Open een pull request en link het issue (`Closes #12`).
5. **Niets komt op `main` (en dus op de server) zonder goedkeuring van Yasuke**: een PR heeft een groene `validate`-check én zijn review nodig. Kleine, gerichte PR's worden het snelst nagekeken.
6. Na de merge pikt de testserver het op en draait hij de bottests. Test het zelf in het spel.
Alle details: <https://github.com/Yasuke2000/ocs-two-lives/blob/main/CONTRIBUTING.md>. Vragen? Stel ze in {#dev-chat}.
EOF

# One guide per channel: "EN" lines first, then "NL" lines. The heading is added in code.
read_txt G_welcome <<'EOF'
**EN** Start here: how to install the pack, join the server and link your Discord account. Read the four messages above, top to bottom.
This channel is read-only: questions go in {#chat}.
**NL** Begin hier: hoe je de pack installeert, de server joint en je Discord-account koppelt. Lees de vier berichten hierboven van boven naar onder.
Dit kanaal is alleen-lezen: vragen stel je in {#chat}.
EOF

read_txt G_announcements <<'EOF'
**EN** News about updates, new content and maintenance. Read-only.
Turn on notifications for this channel so you do not miss anything. Want to react? Do it in {#chat}.
**NL** Nieuws over updates, nieuwe content en onderhoud. Alleen-lezen.
Zet meldingen aan voor dit kanaal, dan mis je niets. Wil je reageren? Doe dat in {#chat}.
EOF

read_txt G_chat <<'EOF'
**EN** Talk about anything outside the game: say hi, find people to play with, ask questions. English or Dutch, both are fine.
Chat with the people in the game itself goes in {#minecraft}, not here.
**NL** Babbel hier over alles buiten het spel: zeg hallo, zoek medespelers, stel je vragen. Engels of Nederlands, beide mag.
Chatten met mensen in het spel zelf doe je in {#minecraft}, niet hier.
EOF

read_txt G_minecraft <<'EOF'
**EN** Live bridge with the game: what you type here shows up in game chat as `[Discord] name: text`, and game chat shows up here. Your account must be linked first (`/verify <code>`).
Handy: `/playerlist` (who is online), `/status`. Off-game chatter belongs in {#chat}.
**NL** Live koppeling met de game: wat je hier typt verschijnt in de spelchat als `[Discord] naam: tekst`, en de spelchat verschijnt hier. Je account moet eerst gekoppeld zijn (`/verify <code>`).
Handig: `/playerlist` (wie is online), `/status`. Praat over andere dingen in {#chat}.
EOF

read_txt G_story <<'EOF'
**EN** The bot posts here as it happens: first-life deaths, rebirths, Legends, great foes slain and world events. Every Sunday at 20:00 it adds the Hall of Souls, a recap of the week.
Read-only: react or talk about it in {#chat}.
**NL** De bot post hier wat er gebeurt: sterfgevallen in een eerste leven, wedergeboortes, Legends, verslagen grote vijanden en wereldgebeurtenissen. Elke zondag om 20:00 volgt de Hall of Souls, een weekoverzicht.
Alleen-lezen: reageer of praat erover in {#chat}.
EOF

read_txt G_screenshots <<'EOF'
**EN** Share your builds, views and funny moments: just attach an image (or paste one). Keep it about the server, and say where it is if it is worth a visit.
**NL** Deel je builds, uitzichten en grappige momenten: voeg gewoon een afbeelding toe (of plak er een). Hou het bij de server, en zeg waar het staat als het een bezoekje waard is.
EOF

read_txt G_leaderboard <<'EOF'
**EN** Live standings: brightest soul, longest first life, Legends, great foes slain and souls per life stage. The bot updates the message above about every 10 minutes. Read-only.
In game you get the same with `/ttl top`.
**NL** Live klassement: helderste ziel, langste eerste leven, Legends, verslagen grote vijanden en zielen per levensfase. De bot past het bericht hierboven ongeveer elke 10 minuten aan. Alleen-lezen.
In het spel zie je hetzelfde met `/ttl top`.
EOF

read_txt G_ideas_and_feedback <<'EOF'
**EN** Post ideas and feedback here, one topic per message. Found a bug? Linked players type `?bugreport <what happened>`: it becomes a **public** GitHub issue.
Good ideas end up as issues on the project board. Want to build them yourself? See {#contribute}.
**NL** Post hier ideeën en feedback, één onderwerp per bericht. Bug gevonden? Gekoppelde spelers typen `?bugreport <wat er gebeurde>`: dat wordt een **publiek** GitHub-issue.
Goede ideeën worden issues op het projectbord. Zelf aan de slag? Kijk in {#contribute}.
EOF

read_txt G_contribute <<'EOF'
**EN** How to help improve the pack: report bugs, suggest ideas, or change things yourself through GitHub. The steps are in the pinned messages below.
Everything reaches `main` (and so the server) only after Yasuke's approval. Questions? Ask in {#dev-chat}.
**NL** Zo help je de pack te verbeteren: bugs melden, ideeën voorstellen of zelf dingen aanpassen via GitHub. De stappen staan in de vastgepinde berichten hieronder.
Alles komt pas op `main` (en dus op de server) na goedkeuring van Yasuke. Vragen? Stel ze in {#dev-chat}.
EOF

read_txt G_dev_chat <<'EOF'
**EN** Open to everyone: talk with the people working on the pack and mod (repo, tools, mods, scripts, pull requests). Ask questions, share what you are building, ask for a review.
Decisions and tasks belong in a GitHub issue, not only here. Setup help: `CONTRIBUTING.md` in the repo, steps in {#contribute}.
**NL** Open voor iedereen: praat mee met de mensen die aan de pack en de mod werken (repo, tools, mods, scripts, pull requests). Stel vragen, deel waar je mee bezig bent, vraag een review.
Beslissingen en taken horen in een GitHub-issue, niet alleen hier. Hulp bij de setup: `CONTRIBUTING.md` in de repo, stappen in {#contribute}.
EOF

read_txt G_logging_and_server_notifactions <<'EOF'
**EN** Automatic notices for the server team: deploys, test results, server up/down. Please do not chat here; use {#chat}.
**NL** Automatische meldingen voor het serverteam: deploys, testresultaten, server aan/uit. Praat hier liever niet; gebruik {#chat}.
EOF

read_txt G_algemeen <<'EOF'
**EN** This is the old default text channel. General talk now lives in {#chat}; the game bridge is {#minecraft}.
**NL** Dit is het oude standaardkanaal. Algemene babbel gebeurt nu in {#chat}; de koppeling met de game is {#minecraft}.
EOF

# Topics (max 1024 chars). #minecraft's topic is managed by the bot itself and left alone.
TOPIC_welcome='Start here: install with Prism, join, link your Discord with /verify. | Begin hier: installeren met Prism, joinen, je Discord koppelen met /verify.'
TOPIC_chat='General off-game chat: say hi, find people to play with. The in-game chat is #minecraft. | Algemene babbel buiten het spel: zeg hallo, zoek medespelers. De chat met het spel is #minecraft.'
TOPIC_contribute="How to help: GitHub issues, project board, pull requests. Nothing is merged without Yasuke's approval. | Zo help je mee: GitHub-issues, projectbord, pull requests. Niets gaat live zonder goedkeuring van Yasuke."
TOPIC_dev_chat='For people working on the pack and mod (repo, tools, scripts, PRs). Open to everyone. | Voor wie aan de pack en de mod werkt (repo, tools, scripts, PRs). Open voor iedereen.'

# channel name -> guide variable suffix (hyphens are not valid in variable names)
GUIDE_CHANNELS="welcome announcements chat minecraft story screenshots leaderboard ideas-and-feedback contribute dev-chat logging-and-server-notifactions algemeen"
key() { printf '%s' "${1//-/_}"; }

# ---------------------------------------------------------------------------------------------
# --export-docs: print docs/discord-guides.md and stop (no token, no network)
# ---------------------------------------------------------------------------------------------
declare -A CID=()
render() { # text mode(link|plain)
  local t=$1 n
  for n in $GUIDE_CHANNELS; do
    if [ "$2" = link ] && [ -n "${CID[$n]:-}" ]; then t=${t//\{#$n\}/<#${CID[$n]}>}; else t=${t//\{#$n\}/#$n}; fi
  done
  printf '%s' "$t"
}
guide_text() { local v="G_$(key "$1")"; printf '%s\n%s' "$HEAD" "${!v%$'\n'}"; }

if [ "${1:-}" = "--export-docs" ]; then
  X_chat=${TOPIC_chat// | / / }; X_contribute=${TOPIC_contribute// | / / }; X_dev_chat=${TOPIC_dev_chat// | / / }; X_welcome=${TOPIC_welcome// | / / }
  blk() { printf '````\n%s\n````\n\n' "$(render "${1%$'\n'}" plain)"; }
  cat <<EOF
# Discord guides (OCS Tensura: Two Lives)

The texts of the server's start guide and of the pinned "How to use this channel / Hoe gebruik je dit kanaal"
message in every channel, in English and Dutch. **Source of truth: \`tools/discord_setup.sh\`**, which also posts,
edits and pins them (idempotent; re-run it after changing a text). This file is generated:

\`\`\`sh
bash tools/discord_setup.sh --export-docs > docs/discord-guides.md
ssh root@100.109.28.21 'bash -s' < tools/discord_setup.sh      # applies it (token read from the k8s secret, never printed)
\`\`\`

\`#name\` below is a clickable channel mention in Discord. Pinning needs the bot to have *Manage Messages* (or
*Pin Messages*); without it the script still posts and reports \`PIN FAILED\`. Messages are limited to 2000 characters.

## Channels the script creates

| Channel | Category | Who can write | Topic |
|---|---|---|---|
| \`#chat\` | Minecraft | everyone | $X_chat |
| \`#contribute\` | Development | everyone | $X_contribute |
| \`#dev-chat\` | Development | everyone | $X_dev_chat |

\`#welcome\` topic: $X_welcome \`#minecraft\`'s topic is maintained by the bot (player count, uptime): leave it.

## #welcome: start guide (four bot messages, edited in place)

### 1. English: welcome and joining

EOF
  blk "$WELCOME_EN"
  printf '### 2. Dutch: welkom en meedoen\n\n'; blk "$WELCOME_NL"
  printf '### 3. English: channels and roles\n\n'; blk "$MAP_EN"
  printf '### 4. Dutch: kanalen en rollen\n\n'; blk "$MAP_NL"
  printf '## #contribute: extra pinned messages\n\n### English\n\n'; blk "$CONTRIB_EN"
  printf '### Nederlands\n\n'; blk "$CONTRIB_NL"
  printf '## Pinned guide per channel\n\nPosted as one message: the heading line, then EN, then NL.\n\n'
  for n in $GUIDE_CHANNELS; do printf '### #%s\n\n' "$n"; blk "$(guide_text "$n")"; done
  exit 0
fi

# ---------------------------------------------------------------------------------------------
# Discord API plumbing
# ---------------------------------------------------------------------------------------------
T=$(k3s kubectl -n ocs-two-lives get secret discord-bot -o jsonpath="{.data.token}" | base64 -d)
[ -n "$T" ] || { echo "no token in secret discord-bot" >&2; exit 1; }
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
CODE=0
PIN_OK=1
FAILS=0

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
body() { jq -n --arg c "$1" '{content:$c, allowed_mentions:{parse:[]}}' > "$W/body.json"; }

api GET "/guilds/$G/channels"
[ "$CODE" = 200 ] || { echo "cannot list channels: HTTP $CODE $(errtext)" >&2; exit 1; }
cp "$W/out" "$W/channels.json"
refresh_ids() {
  local n id
  for n in $GUIDE_CHANNELS; do
    id=$(jq -r --arg n "$n" '[.[]|select(.type==0 and .name==$n)][0].id // empty' "$W/channels.json")
    [ -n "$id" ] && CID[$n]=$id
  done
}
refresh_ids
cat_id() { jq -r --arg n "$1" '[.[]|select(.type==4 and (.name|contains($n)))][0].id // empty' "$W/channels.json"; }

ensure_channel() { # name category-substring
  local name=$1 cat parent v t
  if [ -n "${CID[$name]:-}" ]; then echo "channel #$name exists (${CID[$name]}), skipped"; return; fi
  parent=$(cat_id "$2"); v="TOPIC_$(key "$name")"; t=${!v}
  jq -n --arg n "$name" --arg p "$parent" --arg t "$t" '{name:$n,type:0,topic:$t} + (if $p!="" then {parent_id:$p} else {} end)' > "$W/new.json"
  api POST "/guilds/$G/channels" "$W/new.json"
  if [ "$CODE" = 201 ]; then
    CID[$name]=$(jq -r .id "$W/out"); echo "channel #$name created: ${CID[$name]} (parent ${parent:-none})"
  else
    echo "FAILED to create #$name: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1))
  fi
}

set_topic() { # name
  local name=$1 id=${CID[$1]:-} v="TOPIC_$(key "$1")" cur
  [ -n "$id" ] || return 0
  cur=$(jq -r --arg i "$id" '[.[]|select(.id==$i)][0].topic // ""' "$W/channels.json")
  if [ "$cur" = "${!v}" ]; then echo "topic #$name already set"; return; fi
  jq -n --arg t "${!v}" '{topic:$t}' > "$W/t.json"
  api PATCH "/channels/$id" "$W/t.json"
  if [ "$CODE" = 200 ]; then echo "topic #$name set"; else echo "FAILED topic #$name: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1)); fi
}

# ensure_msg NAME CHANNEL_ID PREFIX TEXT PIN(1|0) [LEGACY_PREFIX]
# Finds the bot's message in the channel (pins first, then the last 50 messages) that starts with PREFIX (or
# LEGACY_PREFIX): edits it when the text differs, posts it when missing, pins it when asked and not yet pinned.
ensure_msg() {
  local label=$1 ch=$2 pre=$3 text=$4 pin=$5 legacy=${6:-$3} mid pinned content act len
  api GET "/channels/$ch/pins"; [ "$CODE" = 200 ] && cp "$W/out" "$W/pins.json" || echo '[]' > "$W/pins.json"
  api GET "/channels/$ch/messages?limit=50"; [ "$CODE" = 200 ] && cp "$W/out" "$W/msgs.json" || echo '[]' > "$W/msgs.json"
  jq -s --arg b "$BOT" --arg p "$pre" --arg l "$legacy" \
    '(.[0]|map(.id)) as $pins | (add|unique_by(.id)) | map(select(.author.id==$b and (.content|startswith($p) or startswith($l))))
     | sort_by(.id)|last // empty | {id, content, pinned:((.id as $i|$pins|index($i))!=null)}' "$W/pins.json" "$W/msgs.json" > "$W/found.json"
  mid=$(jq -r '.id // empty' "$W/found.json")
  body "$text"
  len=$(jq -n --arg c "$text" '$c|length'); if [ "$len" -gt 2000 ]; then echo "FAILED $label: text is $len chars (> 2000)"; FAILS=$((FAILS+1)); return; fi
  if [ -n "$mid" ]; then
    content=$(jq -r .content "$W/found.json"); pinned=$(jq -r .pinned "$W/found.json")
    if [ "$content" = "$text" ]; then act="unchanged ($mid)"; else
      api PATCH "/channels/$ch/messages/$mid" "$W/body.json"
      if [ "$CODE" = 200 ]; then act="edited ($mid)"; else echo "FAILED edit $label: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1)); return; fi
    fi
  else
    api POST "/channels/$ch/messages" "$W/body.json"
    if [ "$CODE" = 200 ]; then mid=$(jq -r .id "$W/out"); act="posted ($mid)"; pinned=false
    else echo "FAILED post $label: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1)); return; fi
  fi
  if [ "$pin" = 1 ]; then
    if [ "$pinned" = true ]; then act="$act, already pinned"
    elif [ $PIN_OK = 0 ]; then act="$act, PIN SKIPPED (no permission, see earlier error)"
    else
      api PUT "/channels/$ch/pins/$mid"
      if [ "$CODE" = 204 ]; then act="$act, pinned"
      else act="$act, PIN FAILED: HTTP $CODE $(errtext)"; [ "$CODE" = 403 ] && PIN_OK=0; FAILS=$((FAILS+1)); fi
    fi
  fi
  echo "$label: $act"
}

# ---------------------------------------------------------------------------------------------
# 1. channels and topics
# ---------------------------------------------------------------------------------------------
ensure_channel chat "Minecraft"
ensure_channel contribute "Development"
ensure_channel dev-chat "Development"
api GET "/guilds/$G/channels"; [ "$CODE" = 200 ] && cp "$W/out" "$W/channels.json"
refresh_ids
for n in welcome chat contribute dev-chat; do set_topic "$n"; done

# ---------------------------------------------------------------------------------------------
# 2. #welcome: the bot's four messages (English/Dutch start guide, English/Dutch channels and roles)
# ---------------------------------------------------------------------------------------------
WC=${CID[welcome]:-}
if [ -n "$WC" ]; then
  ensure_msg "welcome EN start"    "$WC" '**Welcome to OCS Tensura' "$(render "${WELCOME_EN%$'\n'}" link)" 0
  ensure_msg "welcome NL start"    "$WC" '**Welkom bij OCS Tensura' "$(render "${WELCOME_NL%$'\n'}" link)" 0
  ensure_msg "welcome EN channels" "$WC" '**Channels and roles**' "$(render "${MAP_EN%$'\n'}" link)" 0 '**Using the Minecraft bot**'
  ensure_msg "welcome NL channels" "$WC" '**Kanalen en rollen**' "$(render "${MAP_NL%$'\n'}" link)" 0 '**De Minecraft-bot gebruiken**'
fi

# ---------------------------------------------------------------------------------------------
# 3. one pinned guide per channel (+ the contribute how-to)
# ---------------------------------------------------------------------------------------------
for n in $GUIDE_CHANNELS; do
  id=${CID[$n]:-}
  [ -n "$id" ] || { echo "#$n: not found, skipped"; continue; }
  ensure_msg "#$n guide" "$id" "$HEAD" "$(render "$(guide_text "$n")" link)" 1
  if [ "$n" = contribute ]; then
    ensure_msg "#contribute how-to EN" "$id" '**Want to help?' "$(render "${CONTRIB_EN%$'\n'}" link)" 1
    ensure_msg "#contribute how-to NL" "$id" '**Wil je meehelpen?' "$(render "${CONTRIB_NL%$'\n'}" link)" 1
  fi
done

echo "done, $FAILS problem(s)"
