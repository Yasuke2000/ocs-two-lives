# World-map geography corrections — owner-approved 2026-11-19

This note supersedes the corresponding server liberties in the older world brief. Yasuke chose anime/wiki
placement over those liberties, then explicitly authorized updating **only five relation entries** in
`tools/world/canon_relations.toml`. No checker code or other technical rules are changed.

The [claim ledger](../../docs/research/tensura-world-2026-11-19/geography-facts.csv) separates source continuity,
verification and interpretation. Prefer directly verified LN > WN > manga > anime > official map > wiki.
No exact block distance below is a measured canonical distance.

| Relation | Source basis and confidence | Server constraint adopted |
| --- | --- | --- |
| Ogre village relative to Tempest | Supplied wiki associates it with Khusha; pinned fan marker is southeast. **fan-wiki**, not a verified LN bearing. WN chapter 31 says west of the invasion route, which does not establish a Tempest-relative compass bearing. | SE, 400..900 blocks, default diagonal tolerance. |
| Jia relative to Tempest | Supplied atlas and pinned fan marker put Fulbrosia south of Jura. **fan-wiki / visual map evidence**; official guide confirms cold high mountains. Exact bearing is provisional under the owner choice. | S, 2000..4350 blocks, tolerance 35 degrees. |
| Jia relative to Laura | Same reference places Fulbrosia west/southwest of Eurazania. **fan-wiki / visual map evidence**. | W, 900..2600 blocks; range is **our interpretation**, replacing old western displacement. |
| Ulgr park relative to Blumund | The official guide explicitly places Ulgracia south of Sarion, not just below Blumund. The resulting Blumund distance is a server adaptation. | S, 2400..4000 blocks; **our interpretation** of compression. |
| Ulgr park relative to Elmine | Official guide: Ulgracia adjoins Sarion to its south; Ulgr Nature Park is in northernmost Ulgracia. **canon-explicit** country adjacency. Capital/park point spacing is still a server adaptation. | S, 800..1600 blocks. |

References (links only):

- [Official anime world guide](https://www.ten-sura.com/map), Ulgracia, Ulgr Nature Park, Khusha and Fulbrosia entries.
- [Official introductory map](https://www.ten-sura.com/4GfGdAp7/wp-content/themes/tensura_portal/assets/images/portal-map/world/intro/map-base.webp).
- [Pinned interactive reference](https://git.fish/KartoffelChipss/TensuraMap/src/commit/ec4d0e3db2ba4b229d412a273bbcdd19f45425b6), secondary marker positions, not surveyed canon coordinates.
- [Author WN chapter 31](https://ncode.syosetu.com/n6316bn/33/), route-relative ogre village wording; WN continuity.
- [Magic Continent wiki](https://tensura.fandom.com/wiki/Magic_Continent), supplied excerpt, secondary.

The whole continent remains an original server-scale adaptation. Coast vertices, heights, habitat shares,
roads and exact point positions are **our interpretation**; see [regions.md](../../world/regions.md).
