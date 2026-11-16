---
description: Triage a staging-server crash or failed boot
---

Use the `log-triage` agent. Give it the output of `tools/server.sh logs 1500` and, if present, the newest crash report (`ssh root@100.109.28.21 "k3s kubectl -n ocs-two-lives exec deploy/mc -- sh -c 'ls -t /data/crash-reports | head -1 | xargs -I{} cat /data/crash-reports/{}'"`). Report the culprit mod, the evidence line, and a fix that does not involve editing generated files by hand.
