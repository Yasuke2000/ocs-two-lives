# Southern coast painting/source alignment — R118

[Current painted delivery](../../../world/painting-round112/README.md) follows [source PR105](https://github.com/Yasuke2000/ocs-two-lives/pull/105), commit `98b438f`, SHA `5938a823`. All original native children are retained; the exact mainland sea mask and new shore replace the old broad foot. The source itself is unchanged by this review.

The first 64/128-block core/support trial left a ghost of the old shore. Visual inspection rejected it. Final 220/380 buffers and 40-block feather remove the ghost. Final changed pixels: 16,989, bounded by the declared support plus 16 blocks; all exterior pixels match the baseline. This is original vector composition over the original painting, with no new bitmap generation or copyrighted reference pixels. All 58 site registrations, 20 context names and 42 inventory rows remain; browser minimum number spacing 32.47 pixels, no overlap.

Current source checker, normal staging and R117 regional census are adopted only at their exact pinned source. The painting is not proof of global height identity or in-game behavior. No further source-geometry issue was found from this silhouette comparison. Larger-scale fidelity, early-era semantic consistency, missing-source coverage and C23 remain open. The unchanged site exports preserve R113 concept reservations without another art copy.

This branch is stacked over the preceding painting branch and incorporates PR105’s source correction. PR74/PR102 retain their earlier base snapshot until the newer proposals are reconciled. No main merge, world apply or deployment.

Required repository gate: 472 tests, 26 skipped, zero failures in 63.715 seconds. Default checker: zero errors, 56 relations, two prior warnings. No changed JavaScript; validation and `git diff --check` pass.
