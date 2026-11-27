# Approved early Tempest forest trails

Yasuke chose unpaved forest trails immediately after the Kijin naming, with later paving on the same routes. The source now uses `trail` on **tempest_dwargon** and **tempest_blumund**. All vertices, endpoints,23 route IDs and58 site reservations are retained. The existing Dwargon-to-dwarf-village road remains `main`. This is an authored early surface and route reservation, not a claim that canon supplies these surveyed tracks.

## Approved fixed-constraint exception

The standard checker initially rejected the change because arrival had to be near a `main` road. Yasuke separately authorized **one data value** in `tools/world/canon_relations.toml`: `site_rule` arrival, `road_kind = "main"` becomes `road_kind = "trail"`. Its16-block distance limit and every other field and record remain. No checker code or other protected file changes. This is additional to the five earlier owner-approved geography records.

## Actual terrain consequence

Source **534d07ade01d21f3763bebf98cfd18428761aba50388ec70cff4b77e87e787f0**. Standard checker:0errors,56relations,2standing warnings (Laura escarpment river and design box above ordinary target). Normal staging export ran without skip-check in68.6s; no apply or deployment.

| Export evidence | Result |
| --- | --- |
| All58 site exports | Byte-identical, including heights |
| Other21 road records | Byte-identical |
| Water and biome rasters | Byte-identical |
| Height raster |309changed4-block cells;maximum1block difference |
| Road / exclusion / ruggedness rasters |2118 /375 /2419changed cells |
| Road dimensions from current exporter | Half-width2→1;corridor5→4 on the two approved routes |
| Maximum sampled grade across23 exported roads |0.5000000000000455,within floating-point tolerance of1:2 |

The coast,lakes,rivers,mountains,forests,biome masks,regions and all site attributes are unchanged. Narrower road grading changes the listed nearby terrain cells. The owned terrain atlas,painted continent,numbered painting and same-frame comparison are refreshed; the painting uses original earth-coloured track strokes over the retained routes. Historical embedded brushwork is retained and is not an exact height reconstruction. Preview and comparison were visually inspected against the official illustrative context; the official map does not survey these local paths.

The original pre-approval isolated export used skip-check because the then-unchanged arrival rule blocked it. That historical candidate is superseded by the completed normal standard-checked export, not presented as a passing standard run.

## Remaining handoff

Later paving needs a separate runtime phase; no scheduler,structure placement,chunks or live world change is implemented. The Filtwood legacy U/J dependency,larger-island and Malukshure choices,other era/source questions and missing location coverage remain open. This approval closes the two Tempest road-kind conflict only,not all C18 era obligations. The new ledger record is explicitly our interpretation;356unique records are not356canon facts. [Exact audit](early-tempest-trails-audit.json).

Repository gate:494 tests in67.443s,26skipped,the same two Filtwood legacy U/J failures plus validation;zero changed JS files. Gate is not passing. Active XML comparison proves only the two approved road-kind attributes differ from the parent;all14 normal hashes and current presentation root sources match. Local delivery links resolve. No in-game or final fluid acceptance is claimed.
