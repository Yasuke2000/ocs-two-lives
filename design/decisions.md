# Decisions log

Append-only. Locked decisions D1–D20 are in `master-plan.md` → "Locked decisions"; this log records
changes and new decisions with a date.

| Date | # | Decision | Why |
| --- | --- | --- | --- |
| 16/11/2026 | Q1 | Hosting: homelab K3s node3 (side tier), not a rented host | Owner's choice. Node3 has 12 cores / 16 GB; pod gets 10 Gi limit with a 7G heap — below the plan's 12G. Revisit before the full ~200-mod pack or >10 players. |
| 16/11/2026 | D1 | NeoForge pinned to 21.1.266; Tensura 2.0.1.5 (Modrinth) | Latest 1.21.1 builds at init; 2-week soak on staging before launch pin. |
| 16/11/2026 | D2 | Pack repo is public (`Yasuke2000/ocs-two-lives`); server installs via `PACKWIZ_URL` from raw GitHub `main` | No jars committed; configs/scripts only. Simplest path for server and Prism clients. |
| 16/11/2026 | — | Modrinth preferred over CurseForge when a mod is on both | CurseForge files resolve through its API at install time and authors can block third-party downloads. FTB suite, FTB XMod Compat, AllTheLeaks, TensuraMoreConfig are CurseForge-only. |
| 16/11/2026 | — | JEI as the recipe viewer (not EMI) | One viewer only; JEI has the widest addon compat on 1.21.1. |
| 16/11/2026 | — | Staging server whitelist-only, LAN/Tailscale (10.0.20.103); no public port yet | Public exposure decided at soft launch (plan Q6). |
