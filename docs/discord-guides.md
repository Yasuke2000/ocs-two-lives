# Discord guides (OCS Tensura: Two Lives)

The layout of the server and the texts of its guides, in English and Dutch: the start guide, the rules, the
contribute flow and the pinned "How to use this channel / Hoe gebruik je dit kanaal" message that starts
**every** channel (first message, pinned, then the real content). **Source of truth: `tools/discord_setup.sh`**,
which also builds the layout and posts, edits and pins the messages (idempotent; re-run it after changing a text
or the layout). This file is generated:

```sh
bash tools/discord_setup.sh --export-docs > docs/discord-guides.md
ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s' < tools/discord_setup.sh                # applies it (token read from the k8s secret, never printed)
ssh -o LogLevel=ERROR root@100.109.28.21 'bash -s -- --wipe' < tools/discord_setup.sh      # first-time rebuild: also clears the messages of channels where the how-to is not first
```

`#name` below is a clickable channel mention in Discord. Messages are limited to 2000 characters. Existing channels
are reused (renamed, moved, re-permissioned) so their ids, webhooks and the ids in `design/data/discord.toml` and the
sdlink config stay valid; `--wipe` is the only mode that deletes messages. The old default channels (`#algemeen`,
voice "Algemeen", categories "Tekstkanalen" / "Spraakkanalen") are removed. Roles are only checked, not changed: the
bot's role must stay above Life 1 ... Fallen, and `modder` above `Linked`.

## Layout

Category | Channel | Who can write | Topic
---|---|---|---
📌 START | `#welcome` | read-only (the bot posts, members react) | Start here: install with Prism, join, link your Discord with /verify. / Begin hier: installeren met Prism, joinen, je Discord koppelen met /verify.
📌 START | `#rules-and-info` | read-only (the bot posts, members react) | Rules, roles and useful links. / Regels, rollen en handige links.
📌 START | `#announcements` | read-only (the bot posts, members react) | News, updates and maintenance. Read-only. / Nieuws, updates en onderhoud. Alleen-lezen.
📌 START | `#patch-notes` | read-only (the bot posts, members react) | What changed in every update, newest at the bottom. Read-only. / Wat er veranderd is in elke update, nieuwste onderaan. Alleen-lezen.
🎮 MINECRAFT | `#minecraft` | everyone | (maintained by the bot: player count and uptime)
🎮 MINECRAFT | `#story` | read-only (the bot posts, members react) | Deaths, rebirths, Legends and the weekly Hall of Souls (Sundays 20:00). Read-only. / Sterfgevallen, wedergeboortes, Legends en de wekelijkse Hall of Souls (zondag 20:00). Alleen-lezen.
🎮 MINECRAFT | `#leaderboard` | read-only (the bot posts, members react) | Live standings, updated about every 10 minutes (in game: /ttl top). Read-only. / Live klassement, ongeveer elke 10 minuten bijgewerkt (in het spel: /ttl top). Alleen-lezen.
🎮 MINECRAFT | `#screenshots` | everyone | Your best builds and moments. / Je mooiste builds en momenten.
💬 COMMUNITY | `#chat` | everyone | General off-game chat: say hi, find people to play with. The in-game chat is #minecraft. / Algemene babbel buiten het spel: zeg hallo, zoek medespelers. De chat met het spel is #minecraft.
💬 COMMUNITY | `#ideas-and-feedback` | everyone | Ideas and feedback; linked players can report bugs with ?bugreport followed by your text. / Ideeën en feedback; gekoppelde spelers melden bugs met ?bugreport gevolgd door je tekst.
💬 COMMUNITY | voice `Voice` | everyone | 
🛠 DEVELOPMENT | `#contribute` | everyone | How to help: GitHub issues, project board, pull requests. Nothing is merged without Yasuke's approval. / Zo help je mee: GitHub-issues, projectbord, pull requests. Niets gaat live zonder goedkeuring van Yasuke.
🛠 DEVELOPMENT | `#dev-chat` | everyone | For people working on the pack and mod (repo, tools, scripts, PRs). Open to everyone. / Voor wie aan de pack en de mod werkt (repo, tools, scripts, PRs). Open voor iedereen.
🔒 STAFF | `#server-log` | staff only (modder role + bot) | Staff only: server notices (deploys, tests, crashes, up/down, GitHub). / Alleen staff: servermeldingen (deploys, tests, crashes, aan/uit, GitHub).

Channels hidden from members: `#server-log` is visible to the `modder` role and the bot only.

## #welcome: start guide (four bot messages after the pinned how-to)

### 1. English: welcome and joining

````
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
````

### 2. Dutch: welkom en meedoen

````
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
````

### 3. English: where to find what

````
**Where to find what**
**📌 START**
- #welcome: this start guide
- #rules-and-info: the rules, the roles and useful links
- #announcements: news, updates and maintenance
- #patch-notes: what changed in every update of the pack and server, newest at the bottom
**🎮 MINECRAFT**
- #minecraft: live bridge with the game: what you type here shows up in game, and the other way round
- #story: deaths, rebirths, Legends and the weekly Hall of Souls
- #leaderboard: live standings (in game: `/ttl top`)
- #screenshots: your best builds and moments
**💬 COMMUNITY**
- #chat: talk about anything, outside the game
- #ideas-and-feedback: ideas, feedback and `?bugreport <text>` (linked players)
- #Voice: voice chat
**🛠 DEVELOPMENT**
- #contribute: how to help improve the pack
- #dev-chat: talk with the people working on the pack and mod
Every channel starts with a pinned "How to use this channel" message. Lost? Read that one first.
````

### 4. Dutch: waar vind je wat

````
**Waar vind je wat**
**📌 START**
- #welcome: deze startgids
- #rules-and-info: de regels, de rollen en handige links
- #announcements: nieuws, updates en onderhoud
- #patch-notes: wat er veranderd is in elke update van de pack en de server, nieuwste onderaan
**🎮 MINECRAFT**
- #minecraft: live koppeling met de game: wat je hier typt zie je in het spel, en omgekeerd
- #story: sterfgevallen, wedergeboortes, Legends en het wekelijkse Hall of Souls
- #leaderboard: het live klassement (in het spel: `/ttl top`)
- #screenshots: je mooiste builds en momenten
**💬 COMMUNITY**
- #chat: babbelen over alles, buiten het spel
- #ideas-and-feedback: ideeën, feedback en `?bugreport <tekst>` (gekoppelde spelers)
- #Voice: voice chat
**🛠 DEVELOPMENT**
- #contribute: hoe je kan helpen om de pack te verbeteren
- #dev-chat: praten met de mensen die aan de pack en de mod werken
Elk kanaal begint met een vastgepind bericht "Hoe gebruik je dit kanaal". Kwijt? Lees dat eerst.
````

## #rules-and-info: rules, roles and links (four bot messages after the pinned how-to)

### Rules (English)

````
**Server rules**
1. **Be respectful.** No harassment, hate or discrimination, no spam or advertising. English and Dutch are both fine.
2. **No cheating, exploits or duping.** Found an exploit? Report it (`/bug` in game) instead of using it.
3. **PvP is open everywhere, also in Life 1.** Another player can end your only first life, and killing players darkens your karma. That is part of the game; harassing one person over and over is not.
4. **Do not grief or steal.** Do not break or take what is not yours. The server logs blocks, containers, chat, commands and sessions for at most 180 days so staff can roll back damage and handle reports.
5. **Keep private information private.** Do not share personal data (yours or someone else's). `/bug` and `?bugreport` become **public** GitHub issues.
6. **Staff and Yasuke have the final word.** The `modder` role keeps order here. Usually a warning comes first; serious or repeated breaches can lead to a ban. Questions or complaints: ask a staff member or post in #chat.
````

### Regels (Nederlands)

````
**Serverregels**
1. **Wees respectvol.** Geen pesterijen, haat of discriminatie, geen spam of reclame. Engels en Nederlands mogen allebei.
2. **Niet valsspelen, geen exploits of dupes.** Exploit gevonden? Meld hem (`/bug` in het spel) in plaats van hem te gebruiken.
3. **PvP staat overal open, ook in Life 1.** Een andere speler kan je enige eerste leven beëindigen, en spelers doden maakt je karma donkerder. Dat hoort bij het spel; één persoon telkens opnieuw lastigvallen niet.
4. **Geen griefing of diefstal.** Breek of neem niets wat niet van jou is. De server logt blokken, containers, chat, commando's en sessies maximaal 180 dagen, zodat staff schade kan terugdraaien en meldingen kan behandelen.
5. **Hou privégegevens privé.** Deel geen persoonsgegevens (van jezelf of van een ander). `/bug` en `?bugreport` worden **publieke** GitHub-issues.
6. **Staff en Yasuke hebben het laatste woord.** De rol `modder` houdt hier de orde. Meestal volgt eerst een waarschuwing; ernstige of herhaalde overtredingen kunnen een ban betekenen. Vragen of klachten: spreek een staflid aan of post in #chat.
````

### Roles and links (English)

````
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
- What changed in each update: #patch-notes
- How to contribute: #contribute
````

### Rollen en links (Nederlands)

````
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
- Wat er veranderd is per update: #patch-notes
- Meehelpen: #contribute
````

## #contribute: pinned how-to messages (after the pinned how-to)

### English

````
**Want to help? Here is how**
**Where:** the GitHub repo <https://github.com/Yasuke2000/ocs-two-lives> (public). All open work is on the project board: <https://github.com/users/Yasuke2000/projects/1> (Triage, To do, In progress, Done).
**Report or suggest (no coding needed)**
- In game: `/bug <what happened>` (adds your position, life and log lines). In Discord: `?bugreport <text>` in #ideas-and-feedback. Both become a **public** GitHub issue, so keep private info out.
- On GitHub: Issues, New issue, then pick a form: Bug, Idea, Balance, Build request or World / lore fix.
**Change something yourself**
1. Ask Yasuke for collaborator access to the repo.
2. Pick or open an issue and assign yourself, so others know what you are doing.
3. Make a branch (never commit to `main`), edit, and run `python tools/validate.py` until it says `validation passed`.
4. Open a pull request and link the issue (`Closes #12`).
5. **Nothing reaches `main` (and so the server) without Yasuke's approval**: a PR needs a green `validate` check and his review. Small, focused PRs are reviewed fastest.
6. After the merge the test server picks it up and runs the bot tests. Try it in game.
All details: <https://github.com/Yasuke2000/ocs-two-lives/blob/main/CONTRIBUTING.md>. Questions? Ask in #dev-chat.
````

### Nederlands

````
**Wil je meehelpen? Zo werkt het**
**Waar:** de GitHub-repo <https://github.com/Yasuke2000/ocs-two-lives> (publiek). Al het openstaande werk staat op het projectbord: <https://github.com/users/Yasuke2000/projects/1> (Triage, To do, In progress, Done).
**Melden of voorstellen (zonder te programmeren)**
- In het spel: `/bug <wat er gebeurde>` (voegt je positie, leven en logregels toe). In Discord: `?bugreport <tekst>` in #ideas-and-feedback. Beide worden een **publiek** GitHub-issue, zet er dus geen privégegevens in.
- Op GitHub: Issues, New issue, en kies een formulier: Bug, Idea, Balance, Build request of World / lore fix.
**Zelf iets aanpassen**
1. Vraag Yasuke om collaborator-toegang tot de repo.
2. Kies of open een issue en wijs het aan jezelf toe, zodat iedereen weet waar je mee bezig bent.
3. Maak een branch (nooit rechtstreeks op `main`), pas aan en draai `python tools/validate.py` tot er `validation passed` staat.
4. Open een pull request en link het issue (`Closes #12`).
5. **Niets komt op `main` (en dus op de server) zonder goedkeuring van Yasuke**: een PR heeft een groene `validate`-check én zijn review nodig. Kleine, gerichte PR's worden het snelst nagekeken.
6. Na de merge pikt de testserver het op en draait hij de bottests. Test het zelf in het spel.
Alle details: <https://github.com/Yasuke2000/ocs-two-lives/blob/main/CONTRIBUTING.md>. Vragen? Stel ze in #dev-chat.
````

## #patch-notes: one post per update

The content of #patch-notes is not in this script: every update is a file in `docs/patch-notes/` (English then Dutch, player-facing) that `tools/post_patch_notes.sh <file>` posts as bot messages (idempotent: a message whose first line already exists is skipped).

## Pinned how-to per channel

The first message of every channel, pinned: the heading line, then EN, then NL, in one message.

### #welcome

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Start here: how to install the pack, join the server and link your Discord account. Read the messages below, top to bottom: the start guide first, then the channel map.
This channel is read-only: questions go in #chat.
**NL** Begin hier: hoe je de pack installeert, de server joint en je Discord-account koppelt. Lees de berichten hieronder van boven naar onder: eerst de startgids, dan de kanalenkaart.
Dit kanaal is alleen-lezen: vragen stel je in #chat.
````

### #rules-and-info

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** The server rules, an explanation of the roles and the bot commands, and the useful links (server address, modpack, GitHub). Read-only: questions go in #chat.
By being here you agree to the rules below.
**NL** De serverregels, uitleg over de rollen en de botcommando's, en de handige links (serveradres, modpack, GitHub). Alleen-lezen: vragen stel je in #chat.
Door hier te zijn ga je akkoord met de regels hieronder.
````

### #announcements

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** News about updates, new content and maintenance, posted by the server team and the server itself. Read-only.
Turn on notifications for this channel so you do not miss anything. Want to react? Do it in #chat.
**NL** Nieuws over updates, nieuwe content en onderhoud, gepost door het serverteam en de server zelf. Alleen-lezen.
Zet meldingen aan voor dit kanaal, dan mis je niets. Wil je reageren? Doe dat in #chat.
````

### #patch-notes

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Every update of the pack and the server is listed here, newest at the bottom: new content, fixes and changes you will notice in game. Read-only: react to a post if you like it.
Questions go in #chat. Found a bug? Type `/bug <what happened>` in game, or post in #ideas-and-feedback.
**NL** Elke update van de pack en de server staat hier, nieuwste onderaan: nieuwe content, fixes en veranderingen die je in het spel merkt. Alleen-lezen: reageer met een emoji als je iets leuk vindt.
Vragen stel je in #chat. Bug gevonden? Typ `/bug <wat er gebeurde>` in het spel, of post in #ideas-and-feedback.
````

### #minecraft

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Live bridge with the game: what you type here shows up in game chat as `[Discord] name: text`, and game chat shows up here. Your account must be linked first (`/verify <code>`).
Handy: `/playerlist` (who is online), `/status`. Off-game chatter belongs in #chat.
**NL** Live koppeling met de game: wat je hier typt verschijnt in de spelchat als `[Discord] naam: tekst`, en de spelchat verschijnt hier. Je account moet eerst gekoppeld zijn (`/verify <code>`).
Handig: `/playerlist` (wie is online), `/status`. Praat over andere dingen in #chat.
````

### #story

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** The bot posts here as it happens: first-life deaths, rebirths, Legends, great foes slain and world events. Every Sunday at 20:00 it adds the Hall of Souls, a recap of the week.
Read-only: react to a post, or talk about it in #chat.
**NL** De bot post hier wat er gebeurt: sterfgevallen in een eerste leven, wedergeboortes, Legends, verslagen grote vijanden en wereldgebeurtenissen. Elke zondag om 20:00 volgt de Hall of Souls, een weekoverzicht.
Alleen-lezen: reageer op een post, of praat erover in #chat.
````

### #leaderboard

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Live standings: brightest soul, longest first life, Legends, great foes slain and souls per life stage. The bot keeps one message below up to date, about every 10 minutes. Read-only.
In game you get the same with `/ttl top`.
**NL** Live klassement: helderste ziel, langste eerste leven, Legends, verslagen grote vijanden en zielen per levensfase. De bot houdt één bericht hieronder bij, ongeveer elke 10 minuten. Alleen-lezen.
In het spel zie je hetzelfde met `/ttl top`.
````

### #screenshots

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Share your builds, views and funny moments: just attach an image (or paste one). Keep it about the server, and say where it is if it is worth a visit.
**NL** Deel je builds, uitzichten en grappige momenten: voeg gewoon een afbeelding toe (of plak er een). Hou het bij de server, en zeg waar het staat als het een bezoekje waard is.
````

### #chat

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Talk about anything outside the game: say hi, find people to play with, ask questions. English or Dutch, both are fine.
Chat with the people in the game itself goes in #minecraft, not here. Please read the rules in #rules-and-info.
**NL** Babbel hier over alles buiten het spel: zeg hallo, zoek medespelers, stel je vragen. Engels of Nederlands, beide mag.
Chatten met mensen in het spel zelf doe je in #minecraft, niet hier. Lees ook de regels in #rules-and-info.
````

### #ideas-and-feedback

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Post ideas and feedback here, one topic per message. Found a bug? Linked players type `?bugreport <what happened>`: it becomes a **public** GitHub issue.
Good ideas end up as issues on the project board. Want to build them yourself? See #contribute.
**NL** Post hier ideeën en feedback, één onderwerp per bericht. Bug gevonden? Gekoppelde spelers typen `?bugreport <wat er gebeurde>`: dat wordt een **publiek** GitHub-issue.
Goede ideeën worden issues op het projectbord. Zelf aan de slag? Kijk in #contribute.
````

### #Voice

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Voice channel for the community: hop in to talk while you play. Be respectful, and mute your mic when you are not talking. The text chat of this channel is for voice-related notes only; other talk goes in #chat.
**NL** Spraakkanaal voor de community: spring erin om te babbelen terwijl je speelt. Wees respectvol en zet je micro uit als je niet praat. De tekstchat van dit kanaal is alleen voor opmerkingen over de voice; andere babbel hoort in #chat.
````

### #contribute

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** How to help improve the pack: report bugs, suggest ideas, or change things yourself through GitHub. The steps are in the pinned messages in this channel.
Everything reaches `main` (and so the server) only after Yasuke's approval. Questions? Ask in #dev-chat.
**NL** Zo help je de pack te verbeteren: bugs melden, ideeën voorstellen of zelf dingen aanpassen via GitHub. De stappen staan in de vastgepinde berichten in dit kanaal.
Alles komt pas op `main` (en dus op de server) na goedkeuring van Yasuke. Vragen? Stel ze in #dev-chat.
````

### #dev-chat

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Open to everyone: talk with the people working on the pack and mod (repo, tools, mods, scripts, pull requests). Ask questions, share what you are building, ask for a review.
Decisions and tasks belong in a GitHub issue, not only here. Setup help: `CONTRIBUTING.md` in the repo, steps in #contribute.
**NL** Open voor iedereen: praat mee met de mensen die aan de pack en de mod werken (repo, tools, mods, scripts, pull requests). Stel vragen, deel waar je mee bezig bent, vraag een review.
Beslissingen en taken horen in een GitHub-issue, niet alleen hier. Hulp bij de setup: `CONTRIBUTING.md` in de repo, stappen in #contribute.
````

### #server-log

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Staff only (the `modder` role and the bot). Automatic notices from the server: deploys and test results, crashes, lag, server up/down, new GitHub issues and pull requests. Staff can also run read-only `?commands` here (`?list`, `?neoforge tps`, `?ttl staff status`, ...).
Please do not chat here; use #chat.
**NL** Alleen voor staff (de rol `modder` en de bot). Automatische meldingen van de server: deploys en testresultaten, crashes, lag, server aan/uit, nieuwe GitHub-issues en pull requests. Staff kan hier ook alleen-lezen `?commando's` uitvoeren (`?list`, `?neoforge tps`, `?ttl staff status`, ...).
Praat hier liever niet; gebruik #chat.
````

