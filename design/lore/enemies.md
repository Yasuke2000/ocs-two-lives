# The enemies of the roads (bandits, highwaymen, deserters, rogue adventurers)

Data: `design/data/enemies.toml` (camps, archetypes, loot). Script: `world/enemies.js`. Looks: `tools/npc_looks.py`
(`bandit`, `highwayman`, `deserter`, `rogue_adventurer`).

## References

- **Light novel / web novel, vol. 1-3**: the Free Guild (Fuze's Blumund branch) exists because the roads between the Western
  Nations are dangerous; its rank system and bounties are for monsters *and* for criminals. Kaval, Gido and Elen are hired to
  scout the Jura forest because nobody else will go there.
- **Vol. 5-6 (Falmuth)**: Falmuth's army is a levy of knights, mercenaries and conscripts; after the defeat at Tempest the
  survivors scatter. Deserters on the border are not canon characters, they are what such a war leaves behind.
- **Western Nations in general**: the guild has adventurers who were struck off for crimes; "rogue adventurer" is our name
  for them.

## Our interpretation

- **Bandits (Dwarven Road)**: once Tempest and Dwargon trade (the treaty with King Gazel), caravans use the new road; small
  bands camp beside it north of Tempest's bend. Patched leathers, axes, bandanas.
- **Highwaymen (the road to Blumund)**: better dressed, bows, they hold the stretch between Blumund's border and Jura's west
  woods, the route Kaval's party and the Blumund merchants take.
- **Falmuth deserters**: soldiers in Falmuth's blue (the royal bridge palette of `heraldry.toml`) with torn tabards, holding
  the woods on the Falmuth border north of Englassia. Killing them pleases Falmuth (they are its runaways) and Blumund.
- **Rogue adventurers**: dark hoods, no guild plate; they prey on rookies in Jura's west woods (the track to the Sealed Cave)
  and east of Englassia, near the Free Guild's own home.
- No orc raiders yet: Tensura's own orcs already roam, and a pig-faced orc look is not in the skin generator.

Camps stay away from towns, sites, the arrival and the spawn zones round Tempest (`tools/enemies_check.py`), so a fresh
soul meets them only when it goes looking.
