---
description: Push, reload the staging server and run an in-game RCON test
argument-hint: <test-name> [--restart]
---

1. `python tools/validate.py` must pass.
2. Commit and push to `main` (ask first if there are unrelated changes).
3. If `--restart` was given or any file outside `pack/kubejs/` changed: `tools/server.sh restart` (re-runs packwiz-installer). Otherwise `tools/server.sh restart` too — the server only sees new scripts after packwiz pulls them — then `tools/server.sh reload` for later script-only iterations.
4. `tools/server.sh logs 500 | python tools/logscan.py`.
5. `tools/server.sh test $ARGUMENTS` and compare against the expectation in the test file's comments.
6. Report pass/fail with the relevant log lines.
