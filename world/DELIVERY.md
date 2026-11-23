# Current world-map review bundle

![Named original painted atlas](painting-round112/atlas.png)

The post-Kijin map now includes Yasuke's approved Filtwood western forest-edge placement: **(-1050,74,600),gameplay J**,with a1102-block woodland trail. Exact western bearing remains interpreted; Filtwood remains an independent kingdom.

| Deliverable | Current evidence |
| --- | --- |
| Geometry and checked preview | [map.svg](map.svg) · [preview.png](preview.png);58sites,23roads |
| Named original illustration | [Painted atlas](painting-round112/atlas.png) · [marked terrain](atlas.png) |
| Export versus illustration | [Same-frame comparison](painting-round112/current-source-comparison.png) |
| Geography and evidence | [Regions](regions.md) · [356-record ledger](../docs/research/tensura-world-2026-11-19/geography-facts.csv) · [official reference comparison](comparison.md) |
| Place concepts | [58image/sheet pairs](../docs/art/places/README.md) |
| Current approval and checks | [Filtwood adoption](filtwood-approved.md) · [audit](filtwood-approved-audit.json) · [delivery manifest](current-delivery.json) |
| Initial story state | [Immediately after Kijin naming](era.md),anime S1E10 |

Source/export `555c842fe9673fc8e4c4e129c7c29afe51073bc4ad6762e08fb71f061b5f6d4a`. Fresh normal staging passed without skip-check in68.6s. Standard checker:0errors,56relations,2standingwarnings. For the latest early-trail change,biome/water rasters,all58site exports and21other road records are unchanged;309height cells change by at most1block. Original painting now includes the trail and new marker39. Original place PNGs and exact prompts are retained.

**Repository integration remains blocked by the old-map binding:** latest combined gate ran 494 tests, 26 skipped, 2 failures; validation reads U at the retained legacy Filtwood(-900,700) while the approved source binding is J. [Exact handoff](filtwood-approved.md). No runtime,mod or tool code was authored; the six individually approved relation-data records are the protected-path exceptions. This is a draft creative delivery,not a main-ready or deployed world.

Two owner choices remain pending: [larger Ice/ElDorado proportions](https://github.com/Yasuke2000/ocs-two-lives/pull/132) and [Malukshure coastal H-to-O setting](https://github.com/Yasuke2000/ocs-two-lives/pull/135). Their candidate geometry remains inactive. Filtwood's [earlier proposal](https://github.com/Yasuke2000/ocs-two-lives/pull/142) is now adopted here.

The143-entry location inventory still has42physical follow-ups. Source gaps,C05mountain bearing,C07Amrita nesting,Galut registration and complete cities remain open. Claude owns runtime conversion,in-game acceptance,world apply and chunk generation. No main merge,apply or deployment by this delivery.

The requested `chatgpt/world-map` draft now includes the approved-Filtwood and source-review item PRs, plus upstream main history. Both document conflicts were resolved with both histories retained. The [consolidation audit](consolidation-audit.json) records current checker/test scope and the protected-path comparison. Runtime, mod and tools match upstream main except for the five earlier owner-approved geography records and the newly approved single arrival-road kind. No main merge or deployment.

[Approved early Tempest trail adoption](early-tempest-trails-review.md): both Tempest routes are unpaved at the initial snapshot;all points retained,later paving is separate. Updated original painting and comparison follow the same source.
