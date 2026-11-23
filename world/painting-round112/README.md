> Current23November2026: [approved early Tempest trails](../early-tempest-trails-review.md),source555c842f. Original earthy trail strokes and fresh actual terrain are included in the continent,numbered atlas and same-frame comparison. Historical nested brushwork remains and is not an exact height reconstruction. All58 registrations retained.

> Current update22November2026: [approved Filtwood forest-edge adoption](../filtwood-approved.md). Pin(-1050,74,600),J;updated maps and23roads. Standard map checker passes; repository gate has two legacy-map failures. Earlier dated source/hash/check statements below remain historical.

# Current source and painted map together

![Named painted atlas](atlas.png)

[Same-frame terrain/painting comparison](current-source-comparison.png) · [editable comparison](current-source-comparison.svg) · [source-adoption audit](current-source-adoption-audit.json) · [58-site registration](site-registration.json) · [component provenance](provenance.json).

This branch combines the complete current source dossier from `d1f4882` with the original painted atlas from `7446b2b`. The local source now includes the Laura basin/head139→river137 small-fall correction,the individual reference-era limits,the conditional Malukshure proposal,the Eastern Plains label,the inland-palace source-note correction and the selected LN14 primary evidence. The351-record ledger and143/42 inventory are present together with the painting.

Display source **b48666e9** and normal terrain **a9b6b970** remain separate: the Eastern Plains geographical text changes the display source without changing parsed terrain. All14 existing normal files are adopted byte-exact from current source staging; no conversion is rerun or falsely repinned. The approved inland Frost Palace remains at(-1530,71,-3680). Live integration is not performed.

The original native brushwork,continent PNG,atlas PNG,58 numerical registration records,22context labels and42open rows are retained. Their historical component/height provenance remains in provenance.json and the component groups. Updating the root source context does not assert an exact vertical-height reconstruction. The comparison places the current owned normal preview beside the owned illustration in exactly the same12800x10752world frame; it embeds no external art or reference pixels.

The [previous scoped label delivery](https://github.com/Yasuke2000/ocs-two-lives/blob/7446b2be7bfc3622c4762b745e05f41a6009d9a9/world/painting-round112/README.md) remains the history of the earlier mixed-source branch. Its full-source-adoption:false note describes that earlier step. The new current_full_source_adoption record describes this integration. All historical painting decisions are retained.

The larger-island and Malukshure H→O proposals remain inactive pending the owner's choices. Canon-source gaps,unlocated places and post-Kijin architecture/runtime limits stay explicit. This combines reviewable map/source/illustration deliverables; it does not certify complete wiki coverage,whole-city builds or a deployed Minecraft world.

Verification: standard checker0errors,56relations,2standingwarnings. Required `bash tools/check.sh` passed:472tests,26skipped,zero failures in65.650s. Native/atlas bitmap and XML/58registration retention assertions pass. Browser finds no context overlap or clipped panel text. Preview,atlas and comparison were visually inspected;`git diff --check` passes.

The inherited registration metadata `open_inventory_rows` is corrected41→42 to match the42 unchanged visible SVG rows and physical-follow-up inventory; no place is added or closed.
