# Discord guides (OCS Tensura: Two Lives)

The texts of the server's start guide and of the pinned "How to use this channel / Hoe gebruik je dit kanaal"
message in every channel, in English and Dutch. **Source of truth: `tools/discord_setup.sh`**, which also posts,
edits and pins them (idempotent; re-run it after changing a text). This file is generated:

```sh
bash tools/discord_setup.sh --export-docs > docs/discord-guides.md
ssh root@100.109.28.21 'bash -s' < tools/discord_setup.sh      # applies it (token read from the k8s secret, never printed)
```

`#name` below is a clickable channel mention in Discord. Pinning needs the bot to have *Manage Messages* (or
*Pin Messages*); without it the script still posts and reports `PIN FAILED`. Messages are limited to 2000 characters.

## Channels the script creates

| Channel | Category | Who can write | Topic |
|---|---|---|---|
| `#chat` | Minecraft | everyone | General off-game chat: say hi, find people to play with. The in-game chat is #minecraft. / Algemene babbel buiten het spel: zeg hallo, zoek medespelers. De chat met het spel is #minecraft. |
| `#contribute` | Development | everyone | How to help: GitHub issues, project board, pull requests. Nothing is merged without Yasuke's approval. / Zo help je mee: GitHub-issues, projectbord, pull requests. Niets gaat live zonder goedkeuring van Yasuke. |
| `#dev-chat` | Development | everyone | For people working on the pack and mod (repo, tools, scripts, PRs). Open to everyone. / Voor wie aan de pack en de mod werkt (repo, tools, scripts, PRs). Open voor iedereen. |

`#welcome` topic: Start here: install with Prism, join, link your Discord with /verify. / Begin hier: installeren met Prism, joinen, je Discord koppelen met /verify. `#minecraft`'s topic is maintained by the bot (player count, uptime): leave it.

## #welcome: start guide (four bot messages, edited in place)

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

### 3. English: channels and roles

````
**Channels and roles**
**Info**
- #welcome: this start guide
- #announcements: news, updates and maintenance
**Play**
- #chat: talk about anything, outside the game
- #minecraft: live bridge with the game: what you type here shows up in game, and the other way round
- #story: deaths, rebirths, Legends and the weekly Hall of Souls
- #screenshots: your best builds and moments
- #leaderboard: live standings (in game: `/ttl top`)
**Build with us**
- #ideas-and-feedback: ideas, feedback and `?bugreport <text>` (linked players)
- #contribute: how to help improve the pack
- #dev-chat: talk with the people working on the pack and mod
**Server**
- #logging-and-server-notifactions: automatic notices (deploys, server up/down)

**Roles** (automatic once linked): **Linked**; **Life 1** / **Life 2**; **Wanderer**, **Survivor**, **Hero**, **Legend** (karma tier, once your first life is judged); **Fallen** (the dark path).
**Bot commands:** `/verify <code>`, `/playerlist`, `/status`, `/help`
````

### 4. Dutch: kanalen en rollen

````
**Kanalen en rollen**
**Info**
- #welcome: deze startgids
- #announcements: nieuws, updates en onderhoud
**Spelen**
- #chat: babbelen over alles, buiten het spel
- #minecraft: live koppeling met de game: wat je hier typt zie je in het spel, en omgekeerd
- #story: sterfgevallen, wedergeboortes, Legends en het wekelijkse Hall of Souls
- #screenshots: je mooiste builds en momenten
- #leaderboard: het live klassement (in het spel: `/ttl top`)
**Meebouwen**
- #ideas-and-feedback: ideeën, feedback en `?bugreport <tekst>` (gekoppelde spelers)
- #contribute: hoe je kan helpen om de pack te verbeteren
- #dev-chat: praten met de mensen die aan de pack en de mod werken
**Server**
- #logging-and-server-notifactions: automatische meldingen (deploys, server aan/uit)

**Rollen** (automatisch na het koppelen): **Linked**; **Life 1** / **Life 2**; **Wanderer**, **Survivor**, **Hero**, **Legend** (karma-niveau, zodra je eerste leven beoordeeld is); **Fallen** (het donkere pad).
**Bot-commando's:** `/verify <code>`, `/playerlist`, `/status`, `/help`
````

## #contribute: extra pinned messages

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

## Pinned guide per channel

Posted as one message: the heading line, then EN, then NL.

### #welcome

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Start here: how to install the pack, join the server and link your Discord account. Read the four messages above, top to bottom.
This channel is read-only: questions go in #chat.
**NL** Begin hier: hoe je de pack installeert, de server joint en je Discord-account koppelt. Lees de vier berichten hierboven van boven naar onder.
Dit kanaal is alleen-lezen: vragen stel je in #chat.
````

### #announcements

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** News about updates, new content and maintenance. Read-only.
Turn on notifications for this channel so you do not miss anything. Want to react? Do it in #chat.
**NL** Nieuws over updates, nieuwe content en onderhoud. Alleen-lezen.
Zet meldingen aan voor dit kanaal, dan mis je niets. Wil je reageren? Doe dat in #chat.
````

### #chat

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Talk about anything outside the game: say hi, find people to play with, ask questions. English or Dutch, both are fine.
Chat with the people in the game itself goes in #minecraft, not here.
**NL** Babbel hier over alles buiten het spel: zeg hallo, zoek medespelers, stel je vragen. Engels of Nederlands, beide mag.
Chatten met mensen in het spel zelf doe je in #minecraft, niet hier.
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
Read-only: react or talk about it in #chat.
**NL** De bot post hier wat er gebeurt: sterfgevallen in een eerste leven, wedergeboortes, Legends, verslagen grote vijanden en wereldgebeurtenissen. Elke zondag om 20:00 volgt de Hall of Souls, een weekoverzicht.
Alleen-lezen: reageer of praat erover in #chat.
````

### #screenshots

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Share your builds, views and funny moments: just attach an image (or paste one). Keep it about the server, and say where it is if it is worth a visit.
**NL** Deel je builds, uitzichten en grappige momenten: voeg gewoon een afbeelding toe (of plak er een). Hou het bij de server, en zeg waar het staat als het een bezoekje waard is.
````

### #leaderboard

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Live standings: brightest soul, longest first life, Legends, great foes slain and souls per life stage. The bot updates the message above about every 10 minutes. Read-only.
In game you get the same with `/ttl top`.
**NL** Live klassement: helderste ziel, langste eerste leven, Legends, verslagen grote vijanden en zielen per levensfase. De bot past het bericht hierboven ongeveer elke 10 minuten aan. Alleen-lezen.
In het spel zie je hetzelfde met `/ttl top`.
````

### #ideas-and-feedback

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Post ideas and feedback here, one topic per message. Found a bug? Linked players type `?bugreport <what happened>`: it becomes a **public** GitHub issue.
Good ideas end up as issues on the project board. Want to build them yourself? See #contribute.
**NL** Post hier ideeën en feedback, één onderwerp per bericht. Bug gevonden? Gekoppelde spelers typen `?bugreport <wat er gebeurde>`: dat wordt een **publiek** GitHub-issue.
Goede ideeën worden issues op het projectbord. Zelf aan de slag? Kijk in #contribute.
````

### #contribute

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** How to help improve the pack: report bugs, suggest ideas, or change things yourself through GitHub. The steps are in the pinned messages below.
Everything reaches `main` (and so the server) only after Yasuke's approval. Questions? Ask in #dev-chat.
**NL** Zo help je de pack te verbeteren: bugs melden, ideeën voorstellen of zelf dingen aanpassen via GitHub. De stappen staan in de vastgepinde berichten hieronder.
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

### #logging-and-server-notifactions

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** Automatic notices for the server team: deploys, test results, server up/down. Please do not chat here; use #chat.
**NL** Automatische meldingen voor het serverteam: deploys, testresultaten, server aan/uit. Praat hier liever niet; gebruik #chat.
````

### #algemeen

````
**How to use this channel / Hoe gebruik je dit kanaal**
**EN** This is the old default text channel. General talk now lives in #chat; the game bridge is #minecraft.
**NL** Dit is het oude standaardkanaal. Algemene babbel gebeurt nu in #chat; de koppeling met de game is #minecraft.
````

