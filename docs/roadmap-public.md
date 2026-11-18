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

Last update: 18/11/2026 (evening).

---

## 🟢 Live: test this / Live: test dit
**EN** On the test server now. Tell us in {#suggestions} or with `/bug <text>` in game.
- **Two lives**: a hardcore human Life 1 (`/ttl life`), then the Spirit Corridor (`/ttl menu`).
- **Life 2**: the canon continent, 11 new landmarks; Tempest and Dwargon are protected.
- **Story**: `/ttl story oath`, acts I to VII (Walpurgis, the Harvest Festival). 398 quests in one book.
- **Side jobs and companions (new)**: `/ttl sidequest offers` in a town, `/ttl companion hire`.
- **Paths (new)**: `/ttl paths`: the Necromancer (Bone Altar, `/ttl necro status`) and the Artificer (`/ttl artifice`).
- **Hard choices (new)** in the wilds: `/ttl choice`.
- **Bosses**: your party gets its own fight and cooldown, with a queue. Arenas: `/ttl arena list`.
- **World**: it changes as souls move on (`/ttl world where`); storms, Blood Moons.
**NL** Nu op de testserver. Zeg het ons in {#suggestions} of met `/bug <tekst>` in het spel.
- **Twee levens**: een hardcore mensenleven (`/ttl life`), dan de Spirit Corridor (`/ttl menu`).
- **Life 2**: het canon continent, 11 nieuwe plekken; Tempest en Dwargon zijn beschermd.
- **Verhaal**: `/ttl story oath`, akte I tot VII (Walpurgis, het Oogstfeest). 398 quests in één boek.
- **Klusjes en gezellen (nieuw)**: `/ttl sidequest offers` in een stad, `/ttl companion hire`.
- **Paden (nieuw)**: `/ttl paths`: de Necromancer (Bone Altar, `/ttl necro status`) en de Artificer (`/ttl artifice`).
- **Moeilijke keuzes (nieuw)** in de wildernis: `/ttl choice`.
- **Bosses**: je party krijgt een eigen gevecht en cooldown, met een wachtrij. Arena's: `/ttl arena list`.
- **Wereld**: verandert naarmate zielen verder komen (`/ttl world where`); stormen, Bloedmanen.

---

## 🛠 Being built / In de maak
**EN** What the team is working on now: not on the server yet, or not finished.
- **Tempest grows**: the town and capital rings are drawn, the switch between phases is next.
- **Mortal Realm destinations**: six new places to travel to in Life 1 (ferry, keep, market, mine, shrine, tower).
- **More paths**: Artificer golems, more moral choices, the Priest/Exorcist after the Necromancer.
- **Dutch translation** of the pack's own texts, and the **player wiki** going online.
- **Public web map** (BlueMap): the map runs, the public link is coming.
- **Faction banners** you can weave on a loom, and map markers.
**NL** Waar het team nu aan werkt: nog niet op de server, of nog niet af.
- **Tempest groeit**: de ringen voor stad en hoofdstad zijn getekend, de overgang tussen de fases komt nu.
- **Bestemmingen in het Mortal Realm**: zes nieuwe plekken in Life 1 (veerpont, burcht, markt, mijn, heiligdom, toren).
- **Meer paden**: golems voor de Artificer, meer morele keuzes, de Priester/Exorcist na de Necromancer.
- **Nederlandse vertaling** van de eigen teksten van de pack, en de **spelerswiki** online.
- **Publieke webkaart** (BlueMap): de kaart draait, de publieke link komt eraan.
- **Factiebanieren** om op een weefgetouw te maken, en kaartmarkeringen.

---

## 🗺️ Planned / Gepland
**EN** Decided, not started yet. The order can change: good ideas in {#suggestions} can move up.
- **Catch-up** for late joiners, and **raid groups** so light and dark souls can fight one boss together.
- **Radiant quests** and an **Orc Lord invasion** to defend (or join).
- **Politics**: fairer nation wars, taking over or vassalising canon nations.
- **PvP**: a proposal to keep PvP to quests, arenas and declared wars (today it is open everywhere, Life 1 too).
- **Playtest with about 5 players** (Life 1 to Life 2), then the **launch**.
**NL** Beslist, nog niet gestart. De volgorde kan veranderen: goede ideeën in {#suggestions} kunnen voorgaan.
- **Inhalen** voor wie later begint, en **raidgroepen** zodat lichte en donkere zielen samen één boss kunnen bevechten.
- **Radiant quests** en een **invasie van de Orc Lord** om te verdedigen (of om mee te doen).
- **Politiek**: eerlijkere oorlogen tussen naties, canon naties overnemen of tot vazal maken.
- **PvP**: een voorstel om PvP te beperken tot quests, arena's en verklaarde oorlogen (nu staat het overal open, ook in Life 1).
- **Playtest met een vijftal spelers** (Life 1 tot Life 2), daarna de **lancering**.
