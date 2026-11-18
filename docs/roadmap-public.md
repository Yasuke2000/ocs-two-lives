# Public roadmap (OCS Tensura: Two Lives)

The player-facing roadmap: what players can test now, what is being built and what is planned, in English and Dutch.
It is posted to Discord `#roadmap` by `tools/post_roadmap.sh` as three bot messages that are **edited in place**
(never posted again). It is derived from `docs/project-status.md` and `design/roadmap.md`: **update it whenever a
feature changes status** (planned → being built → live), then run the script (see `docs/server.md`, "Roadmap and
suggestions").

Rules for this file:

- Only the three blocks after the first `---` line are posted; this header is not. Blocks are separated by lines that
  are exactly `---` (with a blank line before and after). Each block is one Discord message: at most 1,900 characters,
  English first, then Dutch (`bash tools/post_roadmap.sh docs/roadmap-public.md --dry-run` counts them).
- The first line of a block identifies its message. Renaming it is fine: the script then edits the message at the
  same position.
- `{#name}` becomes a clickable channel mention. Refer to the owner as Yasuke. "Live" lists only what a player can
  try on the server today, with how to try it.

Last update: 18/11/2026.

---

## 🟢 Live: test this / Live: test dit
**EN** On the test server now. Try it and tell us in {#suggestions} or with `/bug <text>` in game.
- **Life 1**: one hardcore human life in the Mortal Realm, no Tensura. Start at Wayfarer's Rest; `/ttl life` shows your karma.
- **Death and rebirth**: the Spirit Corridor (Last Wish, Trial, Great Sage). Lost a choice? `/ttl menu`
- **Life 2**: the canon continent: Tempest, Dwargon, Blumund and more. You arrive on Jura's rim; the forest core is deadly for weak souls.
- **Quests**: 304 quests in one connected book.
- **Story**: `/ttl story oath` (light or dark, for your party), chapters up to Charybdis.
- **Parties and nations**: an FTB party (max 5), then `/ttl nation found <name>`.
- **Economy**: coins, player shops, guild jobs with `/ttl guild board`.
- **Bosses**: 20+ canon bosses in their lairs, sometimes in the wild.
- **Arenas (new)**: `/ttl arena list`, then `/ttl arena join <arena>`.
**NL** Nu op de testserver. Probeer het en zeg het ons in {#suggestions} of met `/bug <tekst>` in het spel.
- **Life 1**: één hardcore mensenleven in het Mortal Realm, zonder Tensura. Start in Wayfarer's Rest; `/ttl life` toont je karma.
- **Dood en wedergeboorte**: de Spirit Corridor (Last Wish, Trial, Great Sage). Keuze kwijt? `/ttl menu`
- **Life 2**: het canon continent: Tempest, Dwargon, Blumund en meer. Je komt aan op de rand van Jura; het hart van het woud is dodelijk voor zwakke zielen.
- **Quests**: 304 quests in één verbonden boek.
- **Verhaal**: `/ttl story oath` (licht of donker, voor je party), hoofdstukken tot Charybdis.
- **Party's en naties**: een FTB-party (max 5), dan `/ttl nation found <naam>`.
- **Economie**: munten, spelerswinkels, gildeklussen met `/ttl guild board`.
- **Bosses**: 20+ canon bosses in hun schuilplaats, soms in het wild.
- **Arena's (nieuw)**: `/ttl arena list`, dan `/ttl arena join <arena>`.

---

## 🛠 Being built / In de maak
**EN** What the team is working on now: not on the server yet, or not finished.
- **World Chronicle**: the world changes for everyone as souls move through the story.
- **Fair boss fights**: every party gets its own fight and cooldown, with a queue, instead of one fight for the whole server.
- **Continent edge**: a clear border of the canon continent; outside it the mods play as usual.
- **More canon landmarks, world events and nation roles on Discord** (in review).
- **Story chapters 11 to 13.**
- **Dutch translation** of the pack's own texts, and a **player wiki**.
- **Public web map** (BlueMap): the map runs, the public link is coming.
- **Crossroads of conscience**: hard choices in the wilds (a sick village, hostages, a starving orc band, a monster that wants a name). Help slowly, or take the dark shortcut and pay for it.
**NL** Waar het team nu aan werkt: nog niet op de server, of nog niet af.
- **World Chronicle**: de wereld verandert voor iedereen naarmate zielen verder komen in het verhaal.
- **Eerlijke bossgevechten**: elke party krijgt een eigen gevecht en cooldown, met een wachtrij, in plaats van één gevecht voor de hele server.
- **Rand van het continent**: een duidelijke grens van het canon continent; daarbuiten werken de mods zoals gewoonlijk.
- **Meer canon plekken, wereldevents en natierollen op Discord** (in review).
- **Verhaalhoofdstukken 11 tot 13.**
- **Nederlandse vertaling** van de eigen teksten van de pack, en een **spelerswiki**.
- **Publieke webkaart** (BlueMap): de kaart draait, de publieke link komt eraan.
- **Kruispunten van het geweten**: moeilijke keuzes in de wildernis (een ziek dorp, gijzelaars, een uitgehongerde orkbende, een monster dat een naam wil). Help langzaam, of neem de duistere kortere weg en betaal ervoor.

---

## 🗺️ Planned / Gepland
**EN** Decided, not started yet. The order can change: good ideas in {#suggestions} can move up.
- **Protected canon places**: Tempest, Dwargon and the other canon builds can't be griefed; their residents come back.
- **Tempest grows** in phases as the server progresses.
- **Catch-up** for late joiners, and **raid groups** so light and dark souls can fight one boss together.
- **Radiant quests** and an **Orc Lord invasion** to defend (or join).
- **Politics**: fairer nation wars, taking over or vassalising canon nations.
- **PvP**: a proposal to keep PvP to quests, arenas and declared wars (today it is open everywhere, Life 1 too).
- **Playtest with about 5 players** (Life 1 to Life 2), then the **launch**.
**NL** Beslist, nog niet gestart. De volgorde kan veranderen: goede ideeën in {#suggestions} kunnen voorgaan.
- **Beschermde canon plekken**: Tempest, Dwargon en de andere canon builds kan je niet griefen; hun bewoners komen terug.
- **Tempest groeit** in fases naarmate de server vordert.
- **Inhalen** voor wie later begint, en **raidgroepen** zodat lichte en donkere zielen samen één boss kunnen bevechten.
- **Radiant quests** en een **invasie van de Orc Lord** om te verdedigen (of om mee te doen).
- **Politiek**: eerlijkere oorlogen tussen naties, canon naties overnemen of tot vazal maken.
- **PvP**: een voorstel om PvP te beperken tot quests, arena's en verklaarde oorlogen (nu staat het overal open, ook in Life 1).
- **Playtest met een vijftal spelers** (Life 1 tot Life 2), daarna de **lancering**.
