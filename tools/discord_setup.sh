#!/bin/bash
# Builds the OCS Tensura: Two Lives Discord server (idempotent, safe to re-run):
#   - categories and channels in a fixed order, with topics and permissions (read-only / staff-only where needed)
#   - the old default channels (#algemeen, voice "Algemeen") and their categories are removed
#   - every channel starts with ONE pinned "How to use this channel / Hoe gebruik je dit kanaal" message
#     (English, then Dutch), followed by the real content (welcome guide, rules, contribute flow...)
#   - the forum #suggestions (type 15): tags, default reaction and guidelines; its how-to is the guidelines text plus
#     a pinned, locked first post. The roadmap content of #roadmap is posted by tools/post_roadmap.sh, the sync of
#     suggestions to GitHub issues runs in ttl-ops (Homelab repo); docs/server.md "Roadmap and suggestions".
#   - roles are only checked (order: bot above the game roles, modder above Linked), never changed
# Existing channels are reused (renamed / moved / re-permissioned), so their ids, webhooks and the ids the game
# uses (design/data/discord.toml, sdlink) stay valid. New ones are created; ids are printed at the end.
#
# The how-to must be the FIRST message of its channel. When it is not (a channel that already had messages),
# a normal run only warns ("NOT FIRST"); `--wipe` deletes ALL messages of those channels and posts again.
# Use --wipe for the initial rebuild only: it removes chat history. A re-run without --wipe never deletes messages.
#
# The texts live in this file; `--export-docs` prints docs/discord-guides.md from them (no network, no token).
# Run it ON the cluster node: the bot token is read from the Kubernetes secret at runtime only and is never
# printed, logged or written to a file (it is also kept out of the process arguments).
#   ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s' < tools/discord_setup.sh                 # normal run
#   ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- --wipe' < tools/discord_setup.sh       # rebuild, clears messages
#   bash tools/discord_setup.sh --export-docs > docs/discord-guides.md
# Needs bash 4, curl and jq (all on the node). The bot needs Administrator, or Manage Channels + Manage Roles +
# Manage Messages + Manage Threads (+ Pin Messages).
set -u

G=1572376519551090728
BOT=1572393611990147253
MODDER=1572392754799968377           # the staff role ("modder")
API=https://discord.com/api/v10
HEAD='**How to use this channel / Hoe gebruik je dit kanaal**'
REPO=https://github.com/Yasuke2000/ocs-two-lives
PRISM=$REPO/releases/download/prism-instance/OCS-Two-Lives.zip

read_txt() { IFS= read -r -d '' "$1" || true; }

# ---------------------------------------------------------------------------------------------
# Layout. Category lines:  key|name|old name (renamed when found)
# Channel lines:           key|name|old name|type (0 text, 2 voice, 15 forum)|category key|mode
# Modes: rw = everyone writes; ro = members read and react, only the bot posts; rostaff = like ro, but the modder role
# can post as well; staff = modder role + bot only (hidden from members).
# #roadmap sits in START, not COMMUNITY: like #patch-notes it is read-only reference that a new player should find
# first ("what can I test, what is coming"); the place to answer it, the #suggestions forum, is in COMMUNITY.
# ---------------------------------------------------------------------------------------------
CATS=(
  "start|📌 START|📢 Info"
  "minecraft|🎮 MINECRAFT|🎮 Minecraft"
  "community|💬 COMMUNITY|"
  "development|🛠 DEVELOPMENT|🛠 Development"
  "staff|🔒 STAFF|"
)
CHANS=(
  "welcome|welcome||0|start|ro"
  "rules-and-info|rules-and-info||0|start|ro"
  "announcements|announcements||0|start|ro"
  "patch-notes|patch-notes||0|start|ro"
  "roadmap|roadmap||0|start|ro"
  "minecraft|minecraft||0|minecraft|rw"
  "story|story||0|minecraft|ro"
  "leaderboard|leaderboard||0|minecraft|ro"
  "screenshots|screenshots||0|minecraft|rw"
  "chat|chat||0|community|rw"
  "ideas-and-feedback|ideas-and-feedback||0|community|rw"
  "suggestions|suggestions||15|community|rw"
  "voice|Voice||2|community|rw"
  "contribute|contribute||0|development|rw"
  "dev-chat|dev-chat||0|development|rw"
  "dev-server-log|dev-server-log||0|development|rostaff"
  "server-log|server-log|logging-and-server-notifactions|0|staff|staff"
)
# Removed when present (and, for the categories, empty): the Discord defaults.
OBSOLETE_TEXT="algemeen"
OBSOLETE_VOICE="Algemeen"
OBSOLETE_CATS="Tekstkanalen|Spraakkanalen"
# Permission bits: SEND_MESSAGES + create public/private threads + send in threads (denied in read-only channels).
RO_DENY=$(( 2048 + (1<<35) + (1<<36) + (1<<38) ))
# The #suggestions forum: tags as "name|emoji|moderated". Moderated (1) = only staff and the bot can set it: the status
# tags, which ttl-ops sets from the GitHub issue's labels (its suggestions sync matches these names: keep them in step).
# Existing tags keep their ids (matched by name), so tags already on posts survive a re-run.
FORUM_TAGS=(
  "Idea|💡|0"
  "Bug|🐛|0"
  "Balance|⚖️|0"
  "Lore|📜|0"
  "Quality of life|✨|0"
  "Under review|🔍|1"
  "Planned|📅|1"
  "In progress|🛠️|1"
  "Done|✅|1"
  "Declined|❌|1"
)
FORUM_REACTION="👍"                  # default reaction on every post: the up-vote
FORUM_POST='How to use this channel / Hoe gebruik je dit kanaal'   # title of the pinned, locked first post

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
**Where to find what**
**📌 START**
- {#welcome}: this start guide
- {#rules-and-info}: the rules, the roles and useful links
- {#announcements}: news, updates and maintenance
- {#patch-notes}: what changed in every update of the pack and server, newest at the bottom
- {#roadmap}: what you can test now, what is being built and what is planned
**🎮 MINECRAFT**
- {#minecraft}: live bridge with the game: what you type here shows up in game, and the other way round
- {#story}: deaths, rebirths, Legends and the weekly Hall of Souls
- {#leaderboard}: live standings (in game: `/ttl top`)
- {#screenshots}: your best builds and moments
**💬 COMMUNITY**
- {#chat}: talk about anything, outside the game
- {#ideas-and-feedback}: feedback and `?bugreport <text>` (linked players)
- {#suggestions}: one post per idea; each becomes a GitHub issue the team decides on
- {#voice}: voice chat
**🛠 DEVELOPMENT**
- {#contribute}: how to help improve the pack
- {#dev-chat}: talk with the people working on the pack and mod
- {#dev-server-log}: the server's important log lines (errors, start/stop/crashes, world works, deploys), read-only
Every channel starts with a pinned "How to use this channel" message. Lost? Read that one first.
EOF

read_txt MAP_NL <<'EOF'
**Waar vind je wat**
**📌 START**
- {#welcome}: deze startgids
- {#rules-and-info}: de regels, de rollen en handige links
- {#announcements}: nieuws, updates en onderhoud
- {#patch-notes}: wat er veranderd is in elke update van de pack en de server, nieuwste onderaan
- {#roadmap}: wat je nu kan testen, wat in de maak is en wat gepland is
**🎮 MINECRAFT**
- {#minecraft}: live koppeling met de game: wat je hier typt zie je in het spel, en omgekeerd
- {#story}: sterfgevallen, wedergeboortes, Legends en het wekelijkse Hall of Souls
- {#leaderboard}: het live klassement (in het spel: `/ttl top`)
- {#screenshots}: je mooiste builds en momenten
**💬 COMMUNITY**
- {#chat}: babbelen over alles, buiten het spel
- {#ideas-and-feedback}: feedback en `?bugreport <tekst>` (gekoppelde spelers)
- {#suggestions}: één post per idee; elk wordt een GitHub-issue waarover het team beslist
- {#voice}: voice chat
**🛠 DEVELOPMENT**
- {#contribute}: hoe je kan helpen om de pack te verbeteren
- {#dev-chat}: praten met de mensen die aan de pack en de mod werken
- {#dev-server-log}: de belangrijke logregels van de server (fouten, start/stop/crashes, wereldwerken, deploys), alleen-lezen
Elk kanaal begint met een vastgepind bericht "Hoe gebruik je dit kanaal". Kwijt? Lees dat eerst.
EOF

read_txt RULES_EN <<'EOF'
**Server rules**
1. **Be respectful.** No harassment, hate or discrimination, no spam or advertising. English and Dutch are both fine.
2. **No cheating, exploits or duping.** Found an exploit? Report it (`/bug` in game) instead of using it.
3. **PvP is open everywhere, also in Life 1.** Another player can end your only first life, and killing players darkens your karma. That is part of the game; harassing one person over and over is not.
4. **Do not grief or steal.** Do not break or take what is not yours. The server logs blocks, containers, chat, commands and sessions for at most 180 days so staff can roll back damage and handle reports.
5. **Keep private information private.** Do not share personal data (yours or someone else's). `/bug` and `?bugreport` become **public** GitHub issues.
6. **Staff and Yasuke have the final word.** The `modder` role keeps order here. Usually a warning comes first; serious or repeated breaches can lead to a ban. Questions or complaints: ask a staff member or post in {#chat}.
EOF

read_txt RULES_NL <<'EOF'
**Serverregels**
1. **Wees respectvol.** Geen pesterijen, haat of discriminatie, geen spam of reclame. Engels en Nederlands mogen allebei.
2. **Niet valsspelen, geen exploits of dupes.** Exploit gevonden? Meld hem (`/bug` in het spel) in plaats van hem te gebruiken.
3. **PvP staat overal open, ook in Life 1.** Een andere speler kan je enige eerste leven beëindigen, en spelers doden maakt je karma donkerder. Dat hoort bij het spel; één persoon telkens opnieuw lastigvallen niet.
4. **Geen griefing of diefstal.** Breek of neem niets wat niet van jou is. De server logt blokken, containers, chat, commando's en sessies maximaal 180 dagen, zodat staff schade kan terugdraaien en meldingen kan behandelen.
5. **Hou privégegevens privé.** Deel geen persoonsgegevens (van jezelf of van een ander). `/bug` en `?bugreport` worden **publieke** GitHub-issues.
6. **Staff en Yasuke hebben het laatste woord.** De rol `modder` houdt hier de orde. Meestal volgt eerst een waarschuwing; ernstige of herhaalde overtredingen kunnen een ban betekenen. Vragen of klachten: spreek een staflid aan of post in {#chat}.
EOF

read_txt INFO_EN <<'EOF'
**Roles** (automatic once you are linked)
- **Linked**: your Discord is linked to your Minecraft account
- **Life 1** / **Life 2**: which life you are in (Life 1 includes the Spirit Corridor)
- **Wanderer**, **Survivor**, **Hero**, **Legend**: your karma tier, once your first life is judged
- **Fallen**: the dark path, shown next to your tier ("Fallen Hero" = Hero + Fallen)
- **modder**: staff
**Bot commands:** `/verify <code>`, `/playerlist`, `/status`, `/help`
**Useful links**
- Server address: `molecule-threefold.tun.ply.gg`
- Modpack (Prism Launcher instance): <https://github.com/Yasuke2000/ocs-two-lives/releases/download/prism-instance/OCS-Two-Lives.zip>
- GitHub repo: <https://github.com/Yasuke2000/ocs-two-lives>
- Project board (open work): <https://github.com/users/Yasuke2000/projects/1>
- What changed in each update: {#patch-notes}
- How to contribute: {#contribute}
- Map credits: the Tensura continent is *Tensura by Lerfing* (giant trees: Paulzero), <https://www.planetminecraft.com/project/tensura-map/>
EOF

read_txt INFO_NL <<'EOF'
**Rollen** (automatisch zodra je gekoppeld bent)
- **Linked**: je Discord is gekoppeld aan je Minecraft-account
- **Life 1** / **Life 2**: in welk leven je zit (Life 1 omvat de Spirit Corridor)
- **Wanderer**, **Survivor**, **Hero**, **Legend**: je karma-niveau, zodra je eerste leven beoordeeld is
- **Fallen**: het donkere pad, naast je niveau ("Fallen Hero" = Hero + Fallen)
- **modder**: staff
**Bot-commando's:** `/verify <code>`, `/playerlist`, `/status`, `/help`
**Handige links**
- Serveradres: `molecule-threefold.tun.ply.gg`
- Modpack (Prism Launcher-instance): <https://github.com/Yasuke2000/ocs-two-lives/releases/download/prism-instance/OCS-Two-Lives.zip>
- GitHub-repo: <https://github.com/Yasuke2000/ocs-two-lives>
- Projectbord (openstaand werk): <https://github.com/users/Yasuke2000/projects/1>
- Wat er veranderd is per update: {#patch-notes}
- Meehelpen: {#contribute}
- Kaartcredits: het continent van Tensura is *Tensura by Lerfing* (reuzenbomen: Paulzero), <https://www.planetminecraft.com/project/tensura-map/>
EOF

read_txt CONTRIB_EN <<'EOF'
**Want to help? Here is how**
**Where:** the GitHub repo <https://github.com/Yasuke2000/ocs-two-lives> (public). All open work is on the project board: <https://github.com/users/Yasuke2000/projects/1> (Triage, To do, In progress, Done).
**Report or suggest (no coding needed)**
- In game: `/bug <what happened>` (adds your position, life and log lines). In Discord: `?bugreport <text>` in {#ideas-and-feedback}, or a post in {#suggestions} for ideas. All become a **public** GitHub issue, so keep private info out.
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
- In het spel: `/bug <wat er gebeurde>` (voegt je positie, leven en logregels toe). In Discord: `?bugreport <tekst>` in {#ideas-and-feedback}, of een post in {#suggestions} voor ideeën. Alles wordt een **publiek** GitHub-issue, zet er dus geen privégegevens in.
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

# One how-to per channel: "EN" lines first, then "NL" lines. The heading is added in code.
read_txt G_welcome <<'EOF'
**EN** Start here: how to install the pack, join the server and link your Discord account. Read the messages below, top to bottom: the start guide first, then the channel map.
This channel is read-only: questions go in {#chat}.
**NL** Begin hier: hoe je de pack installeert, de server joint en je Discord-account koppelt. Lees de berichten hieronder van boven naar onder: eerst de startgids, dan de kanalenkaart.
Dit kanaal is alleen-lezen: vragen stel je in {#chat}.
EOF

read_txt G_rules_and_info <<'EOF'
**EN** The server rules, an explanation of the roles and the bot commands, and the useful links (server address, modpack, GitHub). Read-only: questions go in {#chat}.
By being here you agree to the rules below.
**NL** De serverregels, uitleg over de rollen en de botcommando's, en de handige links (serveradres, modpack, GitHub). Alleen-lezen: vragen stel je in {#chat}.
Door hier te zijn ga je akkoord met de regels hieronder.
EOF

read_txt G_announcements <<'EOF'
**EN** News about updates, new content and maintenance, posted by the server team and the server itself. Read-only.
Turn on notifications for this channel so you do not miss anything. Want to react? Do it in {#chat}.
**NL** Nieuws over updates, nieuwe content en onderhoud, gepost door het serverteam en de server zelf. Alleen-lezen.
Zet meldingen aan voor dit kanaal, dan mis je niets. Wil je reageren? Doe dat in {#chat}.
EOF

read_txt G_patch_notes <<'EOF'
**EN** Every update of the pack and the server is listed here, newest at the bottom: new content, fixes and changes you will notice in game. Read-only: react to a post if you like it.
Questions go in {#chat}. Found a bug? Type `/bug <what happened>` in game, or post in {#ideas-and-feedback}.
**NL** Elke update van de pack en de server staat hier, nieuwste onderaan: nieuwe content, fixes en veranderingen die je in het spel merkt. Alleen-lezen: reageer met een emoji als je iets leuk vindt.
Vragen stel je in {#chat}. Bug gevonden? Typ `/bug <wat er gebeurde>` in het spel, of post in {#ideas-and-feedback}.
EOF

read_txt G_minecraft <<'EOF'
**EN** Live bridge with the game: what you type here shows up in game chat as `[Discord] name: text`, and game chat shows up here. Your account must be linked first (`/verify <code>`).
Handy: `/playerlist` (who is online), `/status`. Off-game chatter belongs in {#chat}.
**NL** Live koppeling met de game: wat je hier typt verschijnt in de spelchat als `[Discord] naam: tekst`, en de spelchat verschijnt hier. Je account moet eerst gekoppeld zijn (`/verify <code>`).
Handig: `/playerlist` (wie is online), `/status`. Praat over andere dingen in {#chat}.
EOF

read_txt G_story <<'EOF'
**EN** The bot posts here as it happens: first-life deaths, rebirths, Legends, great foes slain and world events. Every Sunday at 20:00 it adds the Hall of Souls, a recap of the week.
Read-only: react to a post, or talk about it in {#chat}.
**NL** De bot post hier wat er gebeurt: sterfgevallen in een eerste leven, wedergeboortes, Legends, verslagen grote vijanden en wereldgebeurtenissen. Elke zondag om 20:00 volgt de Hall of Souls, een weekoverzicht.
Alleen-lezen: reageer op een post, of praat erover in {#chat}.
EOF

read_txt G_screenshots <<'EOF'
**EN** Share your builds, views and funny moments: just attach an image (or paste one). Keep it about the server, and say where it is if it is worth a visit.
**NL** Deel je builds, uitzichten en grappige momenten: voeg gewoon een afbeelding toe (of plak er een). Hou het bij de server, en zeg waar het staat als het een bezoekje waard is.
EOF

read_txt G_leaderboard <<'EOF'
**EN** Live standings: brightest soul, longest first life, Legends, great foes slain and souls per life stage. The bot keeps one message below up to date, about every 10 minutes. Read-only.
In game you get the same with `/ttl top`.
**NL** Live klassement: helderste ziel, langste eerste leven, Legends, verslagen grote vijanden en zielen per levensfase. De bot houdt één bericht hieronder bij, ongeveer elke 10 minuten. Alleen-lezen.
In het spel zie je hetzelfde met `/ttl top`.
EOF

read_txt G_chat <<'EOF'
**EN** Talk about anything outside the game: say hi, find people to play with, ask questions. English or Dutch, both are fine.
Chat with the people in the game itself goes in {#minecraft}, not here. Please read the rules in {#rules-and-info}.
**NL** Babbel hier over alles buiten het spel: zeg hallo, zoek medespelers, stel je vragen. Engels of Nederlands, beide mag.
Chatten met mensen in het spel zelf doe je in {#minecraft}, niet hier. Lees ook de regels in {#rules-and-info}.
EOF

read_txt G_ideas_and_feedback <<'EOF'
**EN** Feedback and quick thoughts here, one topic per message. Found a bug? Linked players type `?bugreport <what happened>`: it becomes a **public** GitHub issue.
An idea you want the team to decide on? Make it a post in {#suggestions}: it is tracked on GitHub and you see its status. Want to build it yourself? See {#contribute}.
**NL** Feedback en snelle gedachten hier, één onderwerp per bericht. Bug gevonden? Gekoppelde spelers typen `?bugreport <wat er gebeurde>`: dat wordt een **publiek** GitHub-issue.
Een idee waarover het team moet beslissen? Maak er een post van in {#suggestions}: het wordt opgevolgd op GitHub en je ziet de status. Zelf aan de slag? Kijk in {#contribute}.
EOF

read_txt G_roadmap <<'EOF'
**EN** What you can test on the server now, what is being built and what is planned. The bot keeps the three messages below up to date: it edits them when plans change, so this channel never fills up. Read-only.
Try the "Live" list in game and tell us what you think in {#suggestions}. What changed in each update is in {#patch-notes}.
**NL** Wat je nu op de server kan testen, wat in de maak is en wat gepland is. De bot houdt de drie berichten hieronder bij: hij past ze aan als de plannen veranderen, dus dit kanaal loopt nooit vol. Alleen-lezen.
Probeer de lijst "Live" in het spel en laat in {#suggestions} weten wat je ervan vindt. Wat er per update veranderd is, staat in {#patch-notes}.
EOF

# The forum's how-to is both its guidelines (shown above the posts) and its pinned, locked first post.
read_txt G_suggestions <<'EOF'
**EN** One suggestion per post: an idea, a bug, a balance change, a lore fix or a quality-of-life wish. Click **New Post**, give it a clear title, explain what and why, and pick a tag (Idea, Bug, Balance, Lore, Quality of life). Search first: if it already exists, 👍 that post and add to it.
Within a few minutes the bot turns your post into a **public** GitHub issue (the title, your text and your Discord name) and replies with the link, so keep private information out. The team decides on GitHub and the status tag follows: Under review, Planned, In progress, Done, or Declined (then the post is closed).
Bugs in game: `/bug <text>` adds your position and logs. What is coming already: {#roadmap}.
**NL** Eén voorstel per post: een idee, een bug, een balansaanpassing, een lore-fix of een quality-of-life-wens. Klik op **New Post**, geef een duidelijke titel, leg uit wat en waarom, en kies een tag (Idea, Bug, Balance, Lore, Quality of life). Zoek eerst: bestaat het al, geef die post dan een 👍 en vul hem aan.
Binnen enkele minuten maakt de bot van je post een **publiek** GitHub-issue (de titel, je tekst en je Discord-naam) en antwoordt met de link, zet er dus geen privégegevens in. Het team beslist op GitHub en de statustag volgt: Under review, Planned, In progress, Done, of Declined (dan wordt de post gesloten).
Bugs in het spel: `/bug <tekst>` voegt je positie en logs toe. Wat er al aankomt: {#roadmap}.
EOF

read_txt G_voice <<'EOF'
**EN** Voice channel for the community: hop in to talk while you play. Be respectful, and mute your mic when you are not talking. The text chat of this channel is for voice-related notes only; other talk goes in {#chat}.
**NL** Spraakkanaal voor de community: spring erin om te babbelen terwijl je speelt. Wees respectvol en zet je micro uit als je niet praat. De tekstchat van dit kanaal is alleen voor opmerkingen over de voice; andere babbel hoort in {#chat}.
EOF

read_txt G_contribute <<'EOF'
**EN** How to help improve the pack: report bugs, suggest ideas, or change things yourself through GitHub. The steps are in the pinned messages in this channel.
Everything reaches `main` (and so the server) only after Yasuke's approval. Questions? Ask in {#dev-chat}.
**NL** Zo help je de pack te verbeteren: bugs melden, ideeën voorstellen of zelf dingen aanpassen via GitHub. De stappen staan in de vastgepinde berichten in dit kanaal.
Alles komt pas op `main` (en dus op de server) na goedkeuring van Yasuke. Vragen? Stel ze in {#dev-chat}.
EOF

read_txt G_dev_chat <<'EOF'
**EN** Open to everyone: talk with the people working on the pack and mod (repo, tools, mods, scripts, pull requests). Ask questions, share what you are building, ask for a review.
Decisions and tasks belong in a GitHub issue, not only here. Setup help: `CONTRIBUTING.md` in the repo, steps in {#contribute}.
**NL** Open voor iedereen: praat mee met de mensen die aan de pack en de mod werken (repo, tools, mods, scripts, pull requests). Stel vragen, deel waar je mee bezig bent, vraag een review.
Beslissingen en taken horen in een GitHub-issue, niet alleen hier. Hulp bij de setup: `CONTRIBUTING.md` in de repo, stappen in {#contribute}.
EOF

read_txt G_dev_server_log <<'EOF'
**EN** A read-only, filtered live feed of the server log, so you can follow the server without cluster access. Only the bot and staff post; discuss in {#dev-chat}.
**Posted:** errors and warnings from `[ttl]`, KubeJS and the mods (known boot noise left out); server start, stop, crashes and watchdog; world works (import, placed, laid, planted); deploy and test results of ttl-ops. Joins and leaves are off.
**Reading it:** one code block per post, lines as `time LABEL text`. `(×N)` = the same line N times within a minute. `… N lines suppressed` = the limit of about 20 posts a minute was hit; `tools/server.sh logs` has the rest.
**Privacy:** IP addresses, ports, e-mails and token-like strings are removed before posting. Never paste secrets here.
**NL** Een alleen-lezen, gefilterde livefeed van de serverlog, zodat je de server kan volgen zonder toegang tot de cluster. Alleen de bot en staff posten; bespreek het in {#dev-chat}.
**Gepost:** fouten en waarschuwingen van `[ttl]`, KubeJS en de mods (bekende opstartruis weggelaten); serverstart, stop, crashes en watchdog; wereldwerken (import, placed, laid, planted); deploy- en testresultaten van ttl-ops. Joins en leaves staan uit.
**Zo lees je het:** één codeblok per post, regels als `tijd LABEL tekst`. `(×N)` = dezelfde regel N keer binnen een minuut. `… N lines suppressed` = de limiet van ongeveer 20 posts per minuut is bereikt; `tools/server.sh logs` heeft de rest.
**Privacy:** IP-adressen, poorten, e-mails en token-achtige tekst worden verwijderd vóór het posten. Plak hier nooit geheimen.
EOF

read_txt G_server_log <<'EOF'
**EN** Staff only (the `modder` role and the bot). Automatic notices from the server: deploys and test results, crashes, lag, server up/down, new GitHub issues and pull requests. Staff can also run read-only `?commands` here (`?list`, `?neoforge tps`, `?ttl staff status`, ...).
Please do not chat here; use {#chat}.
**NL** Alleen voor staff (de rol `modder` en de bot). Automatische meldingen van de server: deploys en testresultaten, crashes, lag, server aan/uit, nieuwe GitHub-issues en pull requests. Staff kan hier ook alleen-lezen `?commando's` uitvoeren (`?list`, `?neoforge tps`, `?ttl staff status`, ...).
Praat hier liever niet; gebruik {#chat}.
EOF

# Topics (max 1024 chars). #minecraft's topic is managed by the bot itself (player count, uptime) and left alone.
TOPIC_welcome='Start here: install with Prism, join, link your Discord with /verify. | Begin hier: installeren met Prism, joinen, je Discord koppelen met /verify.'
TOPIC_rules_and_info='Rules, roles and useful links. | Regels, rollen en handige links.'
TOPIC_announcements='News, updates and maintenance. Read-only. | Nieuws, updates en onderhoud. Alleen-lezen.'
TOPIC_patch_notes='What changed in every update, newest at the bottom. Read-only. | Wat er veranderd is in elke update, nieuwste onderaan. Alleen-lezen.'
TOPIC_story='Deaths, rebirths, Legends and the weekly Hall of Souls (Sundays 20:00). Read-only. | Sterfgevallen, wedergeboortes, Legends en de wekelijkse Hall of Souls (zondag 20:00). Alleen-lezen.'
TOPIC_leaderboard='Live standings, updated about every 10 minutes (in game: /ttl top). Read-only. | Live klassement, ongeveer elke 10 minuten bijgewerkt (in het spel: /ttl top). Alleen-lezen.'
TOPIC_screenshots='Your best builds and moments. | Je mooiste builds en momenten.'
TOPIC_chat='General off-game chat: say hi, find people to play with. The in-game chat is #minecraft. | Algemene babbel buiten het spel: zeg hallo, zoek medespelers. De chat met het spel is #minecraft.'
TOPIC_ideas_and_feedback='Feedback; linked players report bugs with ?bugreport followed by your text. Ideas to decide on: #suggestions. | Feedback; gekoppelde spelers melden bugs met ?bugreport gevolgd door je tekst. Ideeën om over te beslissen: #suggestions.'
TOPIC_roadmap='Live (test this), being built and planned, kept up to date by the bot. Read-only. | Live (test dit), in de maak en gepland, bijgehouden door de bot. Alleen-lezen.'
TOPIC_contribute="How to help: GitHub issues, project board, pull requests. Nothing is merged without Yasuke's approval. | Zo help je mee: GitHub-issues, projectbord, pull requests. Niets gaat live zonder goedkeuring van Yasuke."
TOPIC_dev_chat='For people working on the pack and mod (repo, tools, scripts, PRs). Open to everyone. | Voor wie aan de pack en de mod werkt (repo, tools, scripts, PRs). Open voor iedereen.'
TOPIC_dev_server_log='Read-only, filtered feed of the server log: errors, start/stop/crashes, world works, deploys. No IPs, e-mails or tokens. | Alleen-lezen, gefilterde feed van de serverlog: fouten, start/stop/crashes, wereldwerken, deploys. Geen IPs, e-mails of tokens.'
TOPIC_server_log='Staff only: server notices (deploys, tests, crashes, up/down, GitHub). | Alleen staff: servermeldingen (deploys, tests, crashes, aan/uit, GitHub).'

# Content messages that follow the how-to, per channel: "variable|first line (prefix used to find it again)|pin 1/0|old prefix"
CONTENT_welcome=(
  "WELCOME_EN|**Welcome to OCS Tensura|0|"
  "WELCOME_NL|**Welkom bij OCS Tensura|0|"
  "MAP_EN|**Where to find what|0|**Channels and roles**"
  "MAP_NL|**Waar vind je wat|0|**Kanalen en rollen**"
)
CONTENT_rules_and_info=(
  "RULES_EN|**Server rules|0|"
  "RULES_NL|**Serverregels|0|"
  "INFO_EN|**Roles** (automatic|0|"
  "INFO_NL|**Rollen** (automatisch|0|"
)
CONTENT_contribute=(
  "CONTRIB_EN|**Want to help?|1|"
  "CONTRIB_NL|**Wil je meehelpen?|1|"
)

key() { printf '%s' "${1//-/_}"; }
# Parse the layout into parallel arrays
declare -a CK=() CN=() CA=() CT=() CC=() CM=()      # channels: key name alias type category mode
for line in "${CHANS[@]}"; do
  IFS='|' read -r a b c d e f <<<"$line"
  CK+=("$a"); CN+=("$b"); CA+=("$c"); CT+=("$d"); CC+=("$e"); CM+=("$f")
done
declare -a KK=() KN=() KA=()                         # categories: key name alias
for line in "${CATS[@]}"; do
  IFS='|' read -r a b c <<<"$line"
  KK+=("$a"); KN+=("$b"); KA+=("$c")
done

# ---------------------------------------------------------------------------------------------
# Rendering: {#name} -> <#id> (live) or #name (docs)
# ---------------------------------------------------------------------------------------------
declare -A CID=() CATID=()
render() { # text mode(link|plain)
  local t=$1 i
  for i in "${!CK[@]}"; do
    if [ "$2" = link ] && [ -n "${CID[${CK[$i]}]:-}" ]; then t=${t//\{#${CK[$i]}\}/<#${CID[${CK[$i]}]}>}; else t=${t//\{#${CK[$i]}\}/#${CN[$i]}}; fi
  done
  printf '%s' "$t"
}
guide_text() { local v="G_$(key "$1")"; printf '%s\n%s' "$HEAD" "${!v%$'\n'}"; }
mode_text() {
  case $1 in
    ro) echo "read-only (the bot posts, members react)";;
    rostaff) echo "read-only (the bot and the modder role post, members react)";;
    staff) echo "staff only (modder role + bot)";;
    forum) echo "everyone: new posts and replies (status tags: staff and the bot)";;
    *) echo "everyone";;
  esac
}

# ---------------------------------------------------------------------------------------------
# --export-docs: print docs/discord-guides.md and stop (no token, no network)
# ---------------------------------------------------------------------------------------------
if [ "${1:-}" = "--export-docs" ]; then
  blk() { printf '````\n%s\n````\n\n' "$(render "${1%$'\n'}" plain)"; }
  cat <<EOF
# Discord guides (OCS Tensura: Two Lives)

The layout of the server and the texts of its guides, in English and Dutch: the start guide, the rules, the
contribute flow and the pinned "How to use this channel / Hoe gebruik je dit kanaal" message that starts
**every** channel (first message, pinned, then the real content). **Source of truth: \`tools/discord_setup.sh\`**,
which also builds the layout and posts, edits and pins the messages (idempotent; re-run it after changing a text
or the layout). This file is generated:

\`\`\`sh
bash tools/discord_setup.sh --export-docs > docs/discord-guides.md
ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s' < tools/discord_setup.sh                # applies it (token read from the k8s secret, never printed)
ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- --wipe' < tools/discord_setup.sh      # first-time rebuild: also clears the messages of channels where the how-to is not first
\`\`\`

\`#name\` below is a clickable channel mention in Discord. Messages are limited to 2000 characters. Existing channels
are reused (renamed, moved, re-permissioned) so their ids, webhooks and the ids in \`design/data/discord.toml\` and the
sdlink config stay valid; \`--wipe\` is the only mode that deletes messages. The old default channels (\`#algemeen\`,
voice "Algemeen", categories "Tekstkanalen" / "Spraakkanalen") are removed. Roles are only checked, not changed: the
bot's role must stay above Life 1 ... Fallen, and \`modder\` above \`Linked\`.

## Layout

Category | Channel | Who can write | Topic
---|---|---|---
EOF
  for ci in "${!KK[@]}"; do
    for i in "${!CK[@]}"; do
      [ "${CC[$i]}" = "${KK[$ci]}" ] || continue
      v="TOPIC_$(key "${CK[$i]}")"; tp=${!v:-}; tp=${tp// | / / }
      md=${CM[$i]}
      case ${CT[$i]} in
        2) nm="voice \`${CN[$i]}\`";;
        15) nm="forum \`#${CN[$i]}\`"; md=forum; tp='(guidelines: the pinned how-to below)';;
        *) nm="\`#${CN[$i]}\`";;
      esac
      [ "${CK[$i]}" = minecraft ] && tp='(maintained by the bot: player count and uptime)'
      printf '%s | %s | %s | %s\n' "${KN[$ci]}" "$nm" "$(mode_text "$md")" "$tp"
    done
  done
  cat <<EOF

Channels hidden from members: \`#server-log\` is visible to the \`modder\` role and the bot only.

## #welcome: start guide (four bot messages after the pinned how-to)

### 1. English: welcome and joining

EOF
  blk "$WELCOME_EN"
  printf '### 2. Dutch: welkom en meedoen\n\n'; blk "$WELCOME_NL"
  printf '### 3. English: where to find what\n\n'; blk "$MAP_EN"
  printf '### 4. Dutch: waar vind je wat\n\n'; blk "$MAP_NL"
  printf '## #rules-and-info: rules, roles and links (four bot messages after the pinned how-to)\n\n### Rules (English)\n\n'; blk "$RULES_EN"
  printf '### Regels (Nederlands)\n\n'; blk "$RULES_NL"
  printf '### Roles and links (English)\n\n'; blk "$INFO_EN"
  printf '### Rollen en links (Nederlands)\n\n'; blk "$INFO_NL"
  printf '## #contribute: pinned how-to messages (after the pinned how-to)\n\n### English\n\n'; blk "$CONTRIB_EN"
  printf '### Nederlands\n\n'; blk "$CONTRIB_NL"
  printf '## #patch-notes: one post per update\n\nThe content of #patch-notes is not in this script: every update is a file in `docs/patch-notes/` (English then Dutch, player-facing) that `tools/post_patch_notes.sh <file>` posts as bot messages (idempotent: a message whose first line already exists is skipped).\n\n'
  printf '## #roadmap: three bot messages (Live, Being built, Planned)\n\nThe content of #roadmap is not in this script either: it is `docs/roadmap-public.md` (three sections, English then Dutch), which `tools/post_roadmap.sh <file>` keeps as exactly one bot message per section below the pinned how-to. It edits them in place and never posts them again; the messages are found by their first line (or, after a rename, by their position). Update the file when a feature changes status, then run the script (`docs/server.md`, "Roadmap and suggestions").\n\n'
  printf '## #suggestions: forum tags, reaction and the pinned post\n\nA forum channel: every post is one suggestion. Its guidelines (shown above the posts) and its pinned, locked first post "%s" are the same how-to text (below). Default reaction: %s (the up-vote). Tags (moderated ones can only be set by staff and the bot):\n\nTag | Emoji | Who sets it\n---|---|---\n' "$FORUM_POST" "$FORUM_REACTION"
  for line in "${FORUM_TAGS[@]}"; do
    IFS='|' read -r tn te tm <<<"$line"
    [ "$tm" = 1 ] && tw="staff and the bot (status, follows the GitHub labels)" || tw="the author (type)"
    printf '%s | %s | %s\n' "$tn" "$te" "$tw"
  done
  printf '\nttl-ops (Homelab repo, `apps/ocs-two-lives/manifests/ops.yaml`, `suggestions.sh`) turns every new post into a public GitHub issue with the label `suggestion` plus a type label, replies with the link and sets **Under review**; later it follows the issue'"'"'s `status:*` labels and closing (see `docs/server.md`, "Roadmap and suggestions").\n\n'
  printf '## Pinned how-to per channel\n\nThe first message of every channel, pinned: the heading line, then EN, then NL, in one message.\n\n'
  for i in "${!CK[@]}"; do printf '### #%s\n\n' "${CN[$i]}"; blk "$(guide_text "${CK[$i]}")"; done
  exit 0
fi

WIPE=0; [ "${1:-}" = "--wipe" ] && WIPE=1

# ---------------------------------------------------------------------------------------------
# Discord API plumbing
# ---------------------------------------------------------------------------------------------
T=$(k3s kubectl -n ocs-two-lives get secret discord-bot -o jsonpath="{.data.token}" | base64 -d)
[ -n "$T" ] || { echo "no token in secret discord-bot" >&2; exit 1; }
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
CODE=0
PIN_OK=1
FAILS=0
WARNS=0

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
fail() { echo "FAILED $1: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1)); }
warn() { echo "WARNING $1"; WARNS=$((WARNS+1)); }

load_channels() { api GET "/guilds/$G/channels"; [ "$CODE" = 200 ] || { echo "cannot list channels: HTTP $CODE $(errtext)" >&2; exit 1; }; cp "$W/out" "$W/channels.json"; }

# ow_json MODE -> permission_overwrites array
ow_json() {
  case $1 in
    ro) jq -n --arg g "$G" --arg b "$BOT" --arg d "$RO_DENY" \
          '[{id:$g,type:0,allow:"0",deny:$d},{id:$b,type:1,allow:"3072",deny:"0"}]';;
    rostaff) jq -n --arg g "$G" --arg b "$BOT" --arg m "$MODDER" --arg d "$RO_DENY" \
          '[{id:$g,type:0,allow:"0",deny:$d},{id:$b,type:1,allow:"3072",deny:"0"},{id:$m,type:0,allow:"3072",deny:"0"}]';;
    staff) jq -n --arg g "$G" --arg b "$BOT" --arg m "$MODDER" \
          '[{id:$g,type:0,allow:"0",deny:"1024"},{id:$m,type:0,allow:"68608",deny:"0"},{id:$b,type:1,allow:"68608",deny:"0"}]';;
    *) echo '[]';;
  esac
}

# find_chan TYPE NAME [OLD_NAME] -> id (the new name wins over the old one)
find_chan() {
  jq -r --argjson t "$1" --arg n "$2" --arg a "${3:-}" \
    '[.[]|select(.type==$t and (.name==$n or ($a!="" and .name==$a)))]|sort_by(if .name==$n then 0 else 1 end)|.[0].id // empty' "$W/channels.json"
}

# ensure_obj LABEL ID|"" TYPE DESIRED_JSON(name, parent_id?, topic?, permission_overwrites) -> sets ENSURED_ID
# Creates when ID is empty, otherwise PATCHes only when a desired field differs from the current one.
ENSURED_ID=""
ensure_obj() {
  local label=$1 id=$2 type=$3 want=$4 cur same
  echo "$want" | jq --argjson t "$type" '. + {type:$t}' > "$W/new.json"
  if [ -z "$id" ]; then
    api POST "/guilds/$G/channels" "$W/new.json"
    if [ "$CODE" = 201 ]; then ENSURED_ID=$(jq -r .id "$W/out"); echo "$label: created ($ENSURED_ID)"
    else ENSURED_ID=""; fail "create $label"; fi
    return
  fi
  ENSURED_ID=$id
  same=$(jq -r --arg i "$id" --argjson d "$want" '
    [.[]|select(.id==$i)][0] as $c
    | ($d|to_entries|map(select(.key!="permission_overwrites" and .key!="available_tags"))|all(.[]; ($c[.key] // "") == (.value // ""))) as $plain
    | (($c.permission_overwrites|map({id,type,allow:(.allow|tostring),deny:(.deny|tostring)})|sort_by(.id))
       == ($d.permission_overwrites|map({id,type,allow:(.allow|tostring),deny:(.deny|tostring)})|sort_by(.id))) as $ow
    | (($d.available_tags == null) or ((($c.available_tags // [])|map({name, moderated, emoji_name}))
       == ($d.available_tags|map({name, moderated, emoji_name})))) as $tags
    | ($plain and $ow and $tags)' "$W/channels.json")
  if [ "$same" = true ]; then echo "$label: already as wanted ($id)"; return; fi
  echo "$want" > "$W/patch.json"
  api PATCH "/channels/$id" "$W/patch.json"
  if [ "$CODE" = 200 ]; then echo "$label: updated ($id)"; else fail "update $label"; fi
}

# forum_tags_json FORUM_ID|"" -> the wanted available_tags, with the id of an existing tag of the same name
forum_tags_json() {
  local line n e m
  for line in "${FORUM_TAGS[@]}"; do IFS='|' read -r n e m <<<"$line"; printf '%s\t%s\t%s\n' "$n" "$e" "$m"; done \
    | jq -R -s --arg i "${1:-}" --slurpfile c "$W/channels.json" '
        ([$c[0][]|select(.id==$i)][0].available_tags // []) as $cur
        | split("\n") | map(select(length>0)|split("\t"))
        | map(.[0] as $n | {name:$n, emoji_id:null, emoji_name:.[1], moderated:(.[2]=="1")}
              + ([$cur[]|select(.name==$n)][0] // {} | if .id then {id} else {} end))'
}

# ---------------------------------------------------------------------------------------------
# 1. categories and channels
# ---------------------------------------------------------------------------------------------
load_channels
for ci in "${!KK[@]}"; do
  id=$(find_chan 4 "${KN[$ci]}" "${KA[$ci]}")
  mode=rw; [ "${KK[$ci]}" = staff ] && mode=staff
  want=$(jq -n --arg n "${KN[$ci]}" --argjson ow "$(ow_json $mode)" '{name:$n, permission_overwrites:$ow}')
  ensure_obj "category ${KN[$ci]}" "$id" 4 "$want"
  CATID[${KK[$ci]}]=$ENSURED_ID
done
load_channels

for i in "${!CK[@]}"; do
  key=${CK[$i]}; v="TOPIC_$(key "$key")"; topic=${!v:-}
  id=$(find_chan "${CT[$i]}" "${CN[$i]}" "${CA[$i]}")
  want=$(jq -n --arg n "${CN[$i]}" --arg p "${CATID[${CC[$i]}]:-}" --argjson ow "$(ow_json "${CM[$i]}")" \
    '{name:$n, permission_overwrites:$ow} + (if $p!="" then {parent_id:$p} else {} end)')
  if [ "${CT[$i]}" = 0 ] && [ "$key" != minecraft ]; then want=$(echo "$want" | jq --arg t "$topic" '. + {topic:$t}'); fi
  if [ "${CT[$i]}" = 15 ]; then   # forum: the guidelines are the how-to; tags keep their ids (matched by name)
    want=$(echo "$want" | jq --arg t "$(render "$(guide_text "$key")" link)" --argjson tags "$(forum_tags_json "$id")" \
      --arg r "$FORUM_REACTION" '. + {topic:$t, available_tags:$tags, default_reaction_emoji:{emoji_id:null, emoji_name:$r},
        default_sort_order:0, default_forum_layout:1}')
  fi
  ensure_obj "#${CN[$i]}" "$id" "${CT[$i]}" "$want"
  [ -n "$ENSURED_ID" ] && CID[$key]=$ENSURED_ID
done
load_channels

# Order: categories 0..n, channels numbered in layout order (parents are set above; Discord takes one parent change per call)
jq -n --slurpfile c "$W/channels.json" \
  --argjson cats "$(for ci in "${!KK[@]}"; do echo "${CATID[${KK[$ci]}]:-0}"; done | jq -R . | jq -s .)" \
  --argjson chs "$(for i in "${!CK[@]}"; do echo "${CID[${CK[$i]}]:-0}|${CATID[${CC[$i]}]:-0}"; done | jq -R . | jq -s .)" '
  ($cats|to_entries|map({id:.value,position:.key})) as $cp
  | ($chs|to_entries|map({id:(.value|split("|")[0]),position:.key})) as $hp
  | ($cp+$hp) as $want
  | $want|map(select(. as $w|($c[0]|map(select(.id==$w.id and .position==$w.position))|length)==0))' > "$W/pos.json"
if [ "$(jq length "$W/pos.json")" -gt 0 ]; then
  api PATCH "/guilds/$G/channels" "$W/pos.json"
  if [ "$CODE" = 204 ]; then echo "order: set"; else fail "order"; fi
else echo "order: already as wanted"; fi
load_channels

# ---------------------------------------------------------------------------------------------
# 2. system channel (join messages) and removal of the Discord defaults
# ---------------------------------------------------------------------------------------------
api GET "/guilds/$G"
if [ "$CODE" = 200 ] && [ -n "${CID[chat]:-}" ] && [ "$(jq -r '.system_channel_id // ""' "$W/out")" != "${CID[chat]}" ]; then
  jq -n --arg c "${CID[chat]}" '{system_channel_id:$c}' > "$W/g.json"
  api PATCH "/guilds/$G" "$W/g.json"
  if [ "$CODE" = 200 ]; then echo "system channel: #chat"; else fail "system channel"; fi
fi
for pair in "0|$OBSOLETE_TEXT" "2|$OBSOLETE_VOICE"; do
  t=${pair%%|*}; n=${pair#*|}
  id=$(jq -r --argjson t "$t" --arg n "$n" '[.[]|select(.type==$t and .name==$n)][0].id // empty' "$W/channels.json")
  [ -n "$id" ] || continue
  api DELETE "/channels/$id"; if [ "$CODE" = 200 ]; then echo "removed old channel $n ($id)"; else fail "delete $n"; fi
done
load_channels
for cid in $(jq -r --arg re "^($OBSOLETE_CATS)\$" '. as $all|.[]|select(.type==4 and (.name|test($re)))|.id as $i|select([$all[]|select(.parent_id==$i)]|length==0)|.id' "$W/channels.json"); do
  api DELETE "/channels/$cid"; if [ "$CODE" = 200 ]; then echo "removed old empty category ($cid)"; else fail "delete category $cid"; fi
done
load_channels

# ---------------------------------------------------------------------------------------------
# 3. messages: the pinned how-to FIRST, then the content
# ---------------------------------------------------------------------------------------------
# find_msg CHANNEL PREFIX [LEGACY_PREFIX] -> $W/found.json {id, content, pinned} (empty file when none)
find_msg() {
  local ch=$1 pre=$2 legacy=${3:-$2}
  api GET "/channels/$ch/pins"; [ "$CODE" = 200 ] && jq -c 'if type=="array" then . else (.items // [] | map(.message // .)) end' "$W/out" > "$W/pins.json" || echo '[]' > "$W/pins.json"
  api GET "/channels/$ch/messages?limit=50"; [ "$CODE" = 200 ] && cp "$W/out" "$W/msgs.json" || echo '[]' > "$W/msgs.json"
  jq -s --arg b "$BOT" --arg p "$pre" --arg l "$legacy" \
    '(.[0]|map(.id)) as $pins | (add|unique_by(.id)) | map(select(.author.id==$b and (.content|startswith($p) or startswith($l))))
     | sort_by(.id)|first // empty | {id, content, pinned:((.id as $i|$pins|index($i))!=null)}' "$W/pins.json" "$W/msgs.json" > "$W/found.json"
}

# Removes the "X pinned a message" system lines (type 6) so the how-to stays directly followed by the content.
drop_pin_notice() {
  local ch=$1 id q=${2:-limit=5}
  api GET "/channels/$ch/messages?$q"
  [ "$CODE" = 200 ] || return 0
  for id in $(jq -r '.[]|select(.type==6)|.id' "$W/out"); do api DELETE "/channels/$ch/messages/$id"; done
}

# purge_channel CHANNEL: deletes every message (bulk for the ones under 14 days, one by one for older ones)
purge_channel() {
  local ch=$1 round=0 now ids id ms recent old deleted total=0
  now=$(( $(date +%s) * 1000 ))
  while [ $round -lt 30 ]; do
    round=$((round+1))
    api GET "/channels/$ch/messages?limit=100"
    [ "$CODE" = 200 ] || { fail "list messages for purge"; return; }
    ids=$(jq -r '.[].id' "$W/out"); [ -n "$ids" ] || break
    recent=(); old=()
    for id in $ids; do
      ms=$(( (id >> 22) + 1420070400000 ))
      if [ $(( now - ms )) -lt 1166400000 ]; then recent+=("$id"); else old+=("$id"); fi
    done
    deleted=0
    if [ ${#recent[@]} -ge 2 ]; then
      printf '%s\n' "${recent[@]}" | jq -R . | jq -s '{messages:.}' > "$W/bulk.json"
      api POST "/channels/$ch/messages/bulk-delete" "$W/bulk.json"
      if [ "$CODE" = 204 ]; then deleted=$((deleted + ${#recent[@]})); else fail "bulk delete"; fi
    elif [ ${#recent[@]} -eq 1 ]; then old+=("${recent[0]}"); fi
    for id in "${old[@]}"; do api DELETE "/channels/$ch/messages/$id"; [ "$CODE" = 204 ] && deleted=$((deleted+1)); done
    total=$((total+deleted)); [ $deleted -gt 0 ] || break
  done
  echo "  purged $total message(s)"
}

# ensure_msg LABEL CHANNEL PREFIX TEXT PIN [LEGACY_PREFIX]
# Finds the bot's message in the channel that starts with PREFIX (or LEGACY_PREFIX): edits it when the text differs,
# posts it when missing, pins it when asked and not yet pinned.
ensure_msg() {
  local label=$1 ch=$2 pre=$3 text=$4 pin=$5 legacy=${6:-$3} mid pinned content act len
  find_msg "$ch" "$pre" "$legacy"
  mid=$(jq -r '.id // empty' "$W/found.json")
  len=$(jq -n --arg c "$text" '$c|length'); if [ "$len" -gt 2000 ]; then echo "FAILED $label: text is $len chars (> 2000)"; FAILS=$((FAILS+1)); return; fi
  body "$text"
  if [ -n "$mid" ]; then
    content=$(jq -r .content "$W/found.json"); pinned=$(jq -r .pinned "$W/found.json")
    if [ "$content" = "$text" ]; then act="unchanged ($mid)"; else
      api PATCH "/channels/$ch/messages/$mid" "$W/body.json"
      if [ "$CODE" = 200 ]; then act="edited ($mid)"; else fail "edit $label"; return; fi
    fi
  else
    api POST "/channels/$ch/messages" "$W/body.json"
    if [ "$CODE" = 200 ]; then mid=$(jq -r .id "$W/out"); act="posted ($mid)"; pinned=false
    else fail "post $label"; return; fi
  fi
  if [ "$pin" = 1 ]; then
    if [ "$pinned" = true ]; then act="$act, already pinned"
    elif [ $PIN_OK = 0 ]; then act="$act, PIN SKIPPED (no permission, see earlier error)"
    else
      api PUT "/channels/$ch/pins/$mid"
      if [ "$CODE" = 204 ]; then act="$act, pinned"; drop_pin_notice "$ch"
      else act="$act, PIN FAILED: HTTP $CODE $(errtext)"; [ "$CODE" = 403 ] && PIN_OK=0; FAILS=$((FAILS+1)); fi
    fi
  fi
  echo "  $label: $act"
}

# ensure_forum_post FORUM TEXT: the forum's how-to as its first post, pinned (thread flag 2) and locked (only staff and
# the bot can reply). Found again by title + author; the text is edited in place. A forum has no message stream, so
# "first" means: no other post is older than this one.
ensure_forum_post() {
  local ch=$1 text=$2 tid act="" flags locked arch len older
  # Any failure to list or read the posts stops here: guessing "not found" would post a second how-to.
  api GET "/guilds/$G/threads/active"
  [ "$CODE" = 200 ] && jq --arg p "$ch" '[.threads[]|select(.parent_id==$p)]' "$W/out" > "$W/th1.json" || { fail "list forum posts"; return; }
  api GET "/channels/$ch/threads/archived/public?limit=100"
  [ "$CODE" = 200 ] && jq '.threads // []' "$W/out" > "$W/th2.json" || { fail "list archived forum posts"; return; }
  jq -s 'add|unique_by(.id)' "$W/th1.json" "$W/th2.json" > "$W/threads.json" \
    && jq --arg b "$BOT" --arg n "$FORUM_POST" '[.[]|select(.owner_id==$b and .name==$n)]|sort_by((.id|length), .id)|first // empty' \
      "$W/threads.json" > "$W/post.json" || { fail "find the forum how-to"; return; }
  tid=$(jq -r '.id // empty' "$W/post.json")
  len=$(jq -n --arg c "$text" '$c|length'); if [ "$len" -gt 2000 ]; then echo "FAILED forum how-to: text is $len chars (> 2000)"; FAILS=$((FAILS+1)); return; fi
  if [ -z "$tid" ]; then
    jq -n --arg n "$FORUM_POST" --arg c "$text" '{name:$n, auto_archive_duration:10080, message:{content:$c, allowed_mentions:{parse:[]}}}' > "$W/body.json"
    api POST "/channels/$ch/threads" "$W/body.json"
    if [ "$CODE" = 201 ] || [ "$CODE" = 200 ]; then cp "$W/out" "$W/post.json"; tid=$(jq -r .id "$W/post.json"); act="posted ($tid)"
    else fail "post forum how-to"; return; fi
  else
    arch=$(jq -r '.thread_metadata.archived // false' "$W/post.json")
    api GET "/channels/$tid/messages/$tid"   # a forum post's first message has the thread's id
    if [ "$CODE" = 200 ] && [ "$(jq -r .content "$W/out")" = "$text" ]; then act="unchanged ($tid)"
    else
      if [ "$arch" = true ]; then echo '{"archived":false}' > "$W/patch.json"; api PATCH "/channels/$tid" "$W/patch.json"; fi
      body "$text"; api PATCH "/channels/$tid/messages/$tid" "$W/body.json"
      if [ "$CODE" = 200 ]; then act="edited ($tid)"; else fail "edit forum how-to"; return; fi
    fi
  fi
  api GET "/channels/$tid"; [ "$CODE" = 200 ] && cp "$W/out" "$W/post.json"
  flags=$(jq -r '.flags // 0' "$W/post.json"); locked=$(jq -r '.thread_metadata.locked // false' "$W/post.json")
  arch=$(jq -r '.thread_metadata.archived // false' "$W/post.json")
  if [ $(( flags & 2 )) = 0 ] || [ "$locked" != true ] || [ "$arch" = true ]; then
    jq -n --argjson f $(( flags | 2 )) '{flags:$f, locked:true, archived:false}' > "$W/patch.json"
    api PATCH "/channels/$tid" "$W/patch.json"
    if [ "$CODE" = 200 ]; then act="$act, pinned and locked"; else act="$act, PIN/LOCK FAILED: HTTP $CODE $(errtext)"; FAILS=$((FAILS+1)); fi
  else act="$act, already pinned and locked"; fi
  echo "  how-to post: $act"
  older=$(jq -r --arg t "$tid" '[.[]|select([(.id|length), .id] < [($t|length), $t])]|length' "$W/threads.json")
  [ "$older" = 0 ] || warn "#suggestions: $older post(s) are older than the how-to post (it is pinned, so it still shows first)"
}

for i in "${!CK[@]}"; do
  key=${CK[$i]}; ch=${CID[$key]:-}
  [ -n "$ch" ] || { echo "#${CN[$i]}: not found, skipped"; continue; }
  echo "#${CN[$i]} ($ch)"
  if [ "${CT[$i]}" = 15 ]; then ensure_forum_post "$ch" "$(render "$(guide_text "$key")" link)"; continue; fi
  find_msg "$ch" "$HEAD"; how=$(jq -r '.id // empty' "$W/found.json")
  api GET "/channels/$ch/messages?after=0&limit=1"
  first=""; [ "$CODE" = 200 ] && first=$(jq -r '.[0].id // empty' "$W/out")
  if [ -n "$first" ] && [ "$first" != "$how" ]; then
    if [ $WIPE = 1 ]; then purge_channel "$ch"
    else warn "#${CN[$i]}: the how-to is NOT the first message (older messages exist); re-run with --wipe to clear the channel"; fi
  fi
  # Voice channels cannot pin messages (Discord error 50019): their how-to is simply the first message.
  pinhow=1; [ "${CT[$i]}" = 2 ] && pinhow=0
  ensure_msg "how-to" "$ch" "$HEAD" "$(render "$(guide_text "$key")" link)" $pinhow
  drop_pin_notice "$ch" "after=0&limit=10"   # leftovers from earlier runs: the how-to stays directly followed by the content
  cvar="CONTENT_$(key "$key")"
  declare -p "$cvar" >/dev/null 2>&1 || continue
  cv="$cvar[@]"
  for item in "${!cv}"; do
    [ -n "$item" ] || continue
    IFS='|' read -r tv pre pin legacy <<<"$item"
    ensure_msg "$tv" "$ch" "$pre" "$(render "${!tv%$'\n'}" link)" "$pin" "${legacy:-$pre}"
  done
done

# ---------------------------------------------------------------------------------------------
# 4. roles: check only
# ---------------------------------------------------------------------------------------------
api GET "/guilds/$G/roles"
if [ "$CODE" = 200 ]; then
  jq -r --arg m "$MODDER" '
    ([.[]|select(.name|IN("Life 1","Life 2","Wanderer","Survivor","Hero","Legend","Fallen","Linked"))]) as $game
    | ([.[]|select(.managed and .tags.bot_id!=null)]|map(.position)|max // 0) as $bot
    | ([.[]|select(.id==$m)][0].position // 0) as $mod
    | ([.[]|select(.name=="Linked")][0].position // 0) as $linked
    | (if ($game|length)==0 then "roles: game roles not found" elif $bot > ($game|map(.position)|max) then "roles: bot role is above the game roles (ok)" else "roles: PROBLEM: the bot role must sit above Life 1 ... Fallen" end),
      (if $mod > $linked then "roles: modder is above Linked (ok)" else "roles: PROBLEM: modder must sit above Linked" end)' "$W/out"
fi

echo "ids:"; for i in "${!CK[@]}"; do echo "  ${CK[$i]}=${CID[${CK[$i]}]:-?}"; done
echo "done, $FAILS problem(s), $WARNS warning(s)"
