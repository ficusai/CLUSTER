# AI Cluster Auto-Connect — Deep Audit — 2026-07-04 (Session 2)

Project: `/home/ficus-pro/Documents/ai-cluster-auto-connect`
Entry: `cluster.py`, `launcher.sh`, `launcher-notify.sh`, `ai-cluster.desktop`
Config: `config.yaml`
Docs: AGENTS.md, BLUEPRINT.md, README.md, ARCHITECTURE.md, INSTALLATION.md, OPS.md, IMPLEMENTATION-PLAN.md, CHANGELOG.md

## CRITICAL — Runtime bugs

### 1. ai-cluster-stop.sh: undefined PID_FILE crashes with `set -u`
- File: `ai-cluster-stop.sh:79`
- `set -euo pipefail` is active. `PID_FILE` is never defined.
- Lines 79 (`if [ -f "${PID_FILE}" ]`) and 119 (`for f in "${PID_FILE}"`) reference unset variable.
- `bash -n` passes (syntax OK), but runtime exits immediately on first access.
- This is the PRIMARY stop mechanism — silently broken.

### 2. ai-cluster-events.sh: logs/current.log doesn't exist at startup
- File: `ai-cluster-events.sh:12`
- Writes to `logs/current.log` but LogHub writes timestamped names (`2026-07-04-02-41-39.log`).
- `cluster-dashboard.py:31` reads `logs/launcher.log` (fixed in prior session).
- This script's `current.log` is a dead path — events logged there won't appear in any dashboard.

### 3. Dashboard binary artifacts from upstream
- `dashboard/build/exo-logo.png` (1.6 KB), `dashboard/build/favicon.ico` (4.3 KB), `dashboard/build/_app/` (directory).
- index.html does not reference these files. They're dead weight from the upstream exo project.
- `_app/` directory may contain stale compiled assets.

### 4. UDP listen loop exception on fresh boot
- File: `.run.log:1` — `[DISCOVERY] EXCEPTION: UDP listen loop failed`
- Occurs on first launch in a new session. Previous audit noted this but it persists.
- Root: `src/common/discovery.py:181` — `sock.bind(("0.0.0.0", 52052))` may fail when another process holds the port.

## MODERATE — Unfinished code & stubs

### 5. iOS onboarding is a dead stub
- File: `launcher.sh:387-389` — prints "iOS onboarding is not yet automated."
- File: `legacy/setup-iphone.sh` exists but is never invoked by any launcher path.
- IMPLEMENTATION-PLAN.md claims iOS is "Detection + on-device build scripts" (line 87), but no launcher connects to it.

### 6. Windows onboarding is a dead stub
- File: `launcher.sh:393-396` — prints "Windows onboarding is not yet automated."
- File: `windows/connect.bat` — 4-line echo stub with TODO comment.
- IMPLEMENTATION-PLAN.md says "Detection only; onboarding not implemented".

### 7. Linux onboarding is a dead stub
- File: `launcher.sh:399-403` — prints "Linux onboarding is not yet automated."
- Says "git clone <repo-url>" but no repo URL is provided and no actual deployment.

### 8. macOS onboarding is a dead stub
- File: `macos/connect.sh` — 4-line echo stub with TODO comment.
- IMPLEMENTATION-PLAN.md says "Detection only; onboarding not implemented".

### 9. connect.sh scripts are empty stubs (3 platforms)
- `linux/connect.sh`: echo + TODO stub
- `macos/connect.sh`: echo + TODO stub  
- `windows/connect.bat`: echo + TODO stub

### 10. Task queuing/scheduling is "Basic task dispatch only"
- IMPLEMENTATION-PLAN.md:94 marks "Task queuing / scheduling" as 🔄 partial.
- `TaskManager` in `src/root/main.py:122` has basic dispatch but no queue, priority, retry, or multi-task pipelining.

### 11. Production hardening (TLS, auth) marked "🔮 Future"
- IMPLEMENTATION-PLAN.md:95 — flagged as future.
- `POST /api/task/exec` now has Bearer token auth (fixed 07-04), but TCP control channel (port 52053) is still plaintext with no auth between root and workers.

### 12. Register/discover wireless — `register_discover_wireless` method does not exist
- `src/root/main.py:834` (the `auto_start_rpc` fan-out loop) was removed in prior fix.
- But search reveals no remaining fan-out bug. This issue is resolved.

## MODERATE — Design & architectural issues

### 13. `launcher-notify.sh` notification button label is misleading
- File: `notify-action.py:58` — `n.add_action("open", "Open Logs", _on_action)`
- The action opens a terminal, not logs. Label should be "Open Terminal".

### 14. `_term()` function in `launcher-notify.sh` returns echo strings directly
- File: `launcher-notify.sh:7-36`
- Returns command strings like `ptyxis -d '${PROJECT_DIR}' -x bash`. These contain literal `${PROJECT_DIR}` without quoting — safe only because `set -euo pipefail` is on and PROJECT_DIR is set, but the interpolation happens before the echo.

### 15. Log file proliferation — 3 competing log schemes
1. LogHub (`src/common/loghub.py`) → timestamped logs in `logs/YYYY-MM-DD-HH-MM-SS.log`
2. `launcher.sh` → `logs/launcher.log`
3. `ai-cluster-events.sh` → `logs/current.log` + `logs/events.log` + `logs/session-*.log`
4. `.run.log` (project root) — used by `ai-cluster-run.sh`, `quick-start-cluster.sh`
5. `src/logs/rpc-server.log`, `src/logs/llama-server.log` — subprocess logs

No single view shows all events. `cluster-dashboard.py` reads `logs/launcher.log` + all `logs/*.log` but misses `.run.log`.

### 16. `config/` directory is empty
- Created as a placeholder but contains nothing. Unnecessary.

### 17. PyInstaller spec hardcodes absolute home path
- `cluster-linux-x86_64.spec:5` — `['/home/ficus-pro/Documents/ai-cluster-auto-connect/cluster.py']`
- Machine-specific. Won't work on any other system.

### 18. Default config paths hardcoded to user's Desktop/Documents
- `src/root/main.py:242-244` — searches `~/Desktop/ai-cluster-auto-connect/` and `~/Documents/ai-cluster/bin/`
- These are machine-specific fallbacks that won't work elsewhere.

### 19. No test for GUI, dashboard, or platform-specific code
- `tests/` covers: protocol, discovery, worker_exec, root_fallback (4 files)
- Missing: root main, worker main, GUI (app, main_window, system_tray, resources), progress_ui, cluster.py orchestrator, dashboard, loghub
- No integration test for root + worker handshake
- No test for `POST /api/task/exec` auth flow

### 20. `ssh-android.sh` referenced by `legacy/start-cluster.sh` but deprecated
- `legacy/start-cluster.sh:52` calls `ssh-android.sh` with a hardcoded command.
- `ssh-android.sh` still exists but the current launcher (`launcher.sh`) does NOT use it — it uses inline SSH commands instead.
- Legacy script is dead code but has a TODO marker.

### 21. `_app/` directory in dashboard/build is an upstream leftover
- `dashboard/build/_app/` contains unknown contents. Not referenced by current index.html.
- From a prior build system (possibly SvelteKit). Dead artifact.

## MINOR — Docs, consistency, polish

### 22. TODO markers still in code (3 total)
- `src/common/discovery.py:59` — `# TODO FIX LATER: IPv4-only mDNS via socket.inet_aton().`
- `legacy/start-cluster.sh:49` — `# TODO FIX LATER: legacy/start-cluster.sh still hardcodes Android-specific behavior.`
- `macos/connect.sh:4` / `linux/connect.sh:4` — connect script stubs with TODO

### 23. AGENTS.md references 5 files that don't exist
- `deploy/deploy-worker.sh` — EXISTS but is a binary push script, not a worker runtime deploy
- `linux/launch-cluster.sh` — EXISTS
- `legacy/cluster-config.env` — NOT SOURCED (removed in prior fix), but agent doc still lists it

### 24. AGENTS.md says `deploy-worker.sh` deploys "worker files" but it pushes a PyInstaller binary
- `deploy/deploy-worker.sh` expects `dist/cluster-*` binary. If not built, it fails.
- Doc description is misleading — it's a binary pusher, not a source deployer.

### 25. IMPLEMENTATION-PLAN.md says "deploy/" directory exists for remote deployment
- It does exist but contains only one script (`deploy-worker.sh`). No multi-platform deploy matrix.

### 26. `ai-cluster-events.sh` hangs waiting for Enter on exit
- Line 200: `read -r _ || true` — interactive wait that hangs GUI-less contexts.

### 27. `ai-cluster-stop.sh` duplicate log patterns
- `*.log` appears twice in `.gitignore` (lines 23 and 25).

### 28. `cluster-dashboard.py` imports `LogHub` but uses its own `_log_call` decorator
- Has a local `_log_call` redefinition that duplicates LogHub's but omits FAILED traceback formatting.
- Uses `__import__("traceback")` inline instead of top-level import — unusual pattern.

### 29. `VERSION = "1.3.0"` in cluster.py — no CHANGELOG entry for 1.3.0
- CHANGELOG.md exists but was not read. Likely stale.

### 30. `install.sh` writes a Python wrapper with hardcoded sitepath
- Lines 57-62 create a wrapper with `/../share/ai-cluster` — path that doesn't exist and never gets populated.

## PREVIOUSLY FIXED (confirmed still intact)
- mDNS NonUniqueNameException handling ✅
- Worker async PID returns correct Popen.pid ✅
- UDP discovery IP set capped at 512 ✅
- Fan-out dispatcher loop removed ✅
- Dashboard sys.path insertion ✅
- Bearer token auth on /api/task/exec ✅
- File descriptor leak in Popen(stdout=open(...)) ✅
- Shebang + chmod on cluster.py and cluster-dashboard.py ✅
- notify-action.py vendored inside project ✅
- legacy/start-cluster.sh no longer sources cluster-config.env ✅

## Summary counts
- CRITICAL: 4 (stop script broken, events log to dead path, upstream binary artifacts, UDP bind failure)
- MODERATE: 14 (stubs, missing implementations, design issues)
- MINOR: 8 (TODOs, docs drift, polish)
- PREVIOUSLY FIXED: 10 (verified intact)
