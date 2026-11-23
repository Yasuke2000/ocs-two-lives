# Runtime switch source review and provenance correction

23 November 2026. Read-only comparison with [own-world-switch commit 0fc6eb27](https://github.com/Yasuke2000/ocs-two-lives/commit/0fc6eb27e97ab74c0b53bcc55ffb3d116b6ae877). Its WIP commit explicitly says it is not for main. No technical branch is merged or executed here.

## Source alignment

| Bundle | Canonical SVG text SHA256 |
| --- | --- |
| Technical branch map and applied index | `b48666e9a6785a5900bb694525c38487fea2c9ade1171df62d843589c671c661` |
| Current authoring map and normal export | `534d07ade01d21f3763bebf98cfd18428761aba50388ec70cff4b77e87e787f0` |
| Larger-island review source | `97667b2a`; inactive pending owner choice |

The previous current-source label555c842f was the raw Windows CRLF file hash. The converter normalizes text to LF;the Git blob and existing normal index use534d07ad. The source file now has LF bytes too. Parsed geometry is unchanged;no new conversion is required because the converter input text and all14normal outputs already match. Root presentation metadata and the visible comparison label are corrected. Historical records using555c842f describe that earlier raw worktree hash,not a distinct geography.

The technical bundle is self-consistent about its older source. Six of11core runtime files differ from current staging:exclude,height,index,road,roads and ruggedness. Biome,water,canon grid,flat site configuration and site mask are exact. The different files still need regeneration from the approved source;equal files do not certify the complete bundle. [Exact snapshot](runtime-source-review.json).

| Contract | Technical snapshot | Current approved drawing |
| --- | --- | --- |
| Filtwood | (-1200,65,2750),gameplay U | (-1050,74,600),gameplay J |
| Tempest-Dwargon / Tempest-Blumund | main / main | trail / trail |
| Filtwood woodland trail | absent;22routes total | present;23routes total |

Filtwood is the only changed placement-index record;the other57match. This is not proof of placed structures or an initial resident roster.

## Why a region check can pass at the wrong coordinate

At this technical commit,tools/gen_data.py lines34-35 select the applied own-world canon grid when it exists. Read-only sampling shows J both at the approved Filtwood coordinate and the old authoring anchor(-900,700) on that grid. The old anchor reads U on the legacy grid. Changing the selected grid can therefore clear a region check while retaining the wrong position. Acceptance must verify actual x,y,z and source hashes alongside region letters. Static evidence is not a test-pass claim.

## Correct export counts

The exporter has58placement-index records and34flat terrain-preparation records in sites.json. Four carved sites and20unplated markers are represented separately in the index. The island proposal changes3index records but only2flat preparations:32of34flat records remain unchanged. Its earlier56configuration count was wrong and is corrected in the report/audit. Its55unchanged index records and21unchanged road records remain correct. The earlier approved-trail58-site claim was independently verified against the actual before/after index and holds.

## Technical acceptance handoff

Use active world/map.svg with canonical source534d07ad and the matching14-file manifest. Refresh the technical drawing and generated inputs together using the existing switch workflow;carry the approved J anchor and arrival trail relation through that integration. Compare all58index positions,all23road records and generated artifact hashes against the current bundle. The larger-island proposal remains a separate pending choice.

Run the combined checks and actual-pack site,road,carve,fluid and initial-era verification in the technical workflow. The branch's WIP quest-distance and Dwargon-carve notes are not resolved or rerun here. The creative gate still has the disclosed two legacy Filtwood failures. No source-faithful Minecraft output,main readiness,world apply,chunks or deployment is claimed.

Verification:standard checker0errors/56relations/2standingwarnings;494repository tests in66.206seconds,26skipped,the same2legacy Filtwood failures plus validation;zero changed JS files. Git blob,worktree and converter source are now equal;all14normal hashes and rendered preview/terrain atlas/continent/painted atlas are retained. Only the comparison's visible source label changes. Local delivery links resolve;protected paths are unchanged. Technical WIP tests and actual-pack behaviour were not run here.
