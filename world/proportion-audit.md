# Relative-position audit — provisional reference benchmark

[CSV](proportion-audit.csv) compares 14 authored sites with the user-supplied pinned interactive reference.
Distances are normalized to Tempest–Siss in each coordinate system, so absolute block scaling cancels out.
Bearings use north-up image pixels and north-up world coordinates. Values are computed from the source
metadata and current SVG, not from remembered lore.

**Limit:** these are fan marker positions over an illustrated map, not a surveyed canonical coordinate system.
A discrepancy is a review signal, not evidence that a licensed novel is wrong. No claim of official precision
or a known projection is made. The official base image is a separate visual reference in comparison.md.

The audit exposes nonuniform compression that the geometry checker cannot assess. Fixed server distances,
site footprints, parent offsets and route constraints still apply; do not loosen technical rules beyond the
five specifically approved entries. Any source-supported alternative that cannot fit those constraints must
be drawn in a comment and explained in the PR, as required by the task.

Round 6 corrects Blumund, Marris and the Sealed Cave, with matching coast/approach changes. Before/after
columns preserve the baseline at commit 4c99877. The three distance-ratio discrepancies fall from
57.4% to 32.8%, 41.8% to 11.4% and 24.3% to 3.3% respectively.

[Reference-scaled study](proportion-study.png) and the inert `reference-proportion-*` circles inside
map.svg show where fixed rules prevent a single common scale. The trial coordinates are **our interpretation**
of secondary marker pixels with an unknown projection; they do not prove primary canon coordinates.
Further changes should follow stronger source evidence or an explicit owner choice on those conflicts.
