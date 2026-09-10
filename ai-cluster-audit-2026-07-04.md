# AI Cluster Auto-Connect — Codebase Audit

**Date:** 2026-07-04
**Project:** `/home/ficus-pro/Documents/ai-cluster-auto-connect`
**Desktop entry:** `/home/ficus-pro/Desktop/ai-cluster.desktop` (Exec = `launcher-notify.sh --root`)

## Verdict
No critical defects remain. Root launches cleanly, serves the dashboard, starts local RPC + llama-server, and `/api/task/exec` is now authenticated.

## Issues found and fixed

| # | File | Problem | Fix |
|---|------|---------|-----|
| 1 | `cluster-dashboard.py` | Missing `src/` in `sys.path`; crashed at import | Added `sys.path.insert(0, os.path.join(..., "src"))` |
| 2 | `cluster.py:224` | Imported `UDPBroadcastDiscovery` from `common.protocol` (does not exist) | Imported from `common.discovery` |
| 3 | `src/root/main.py:824` | Open LAN RCE via `POST /api/task/exec` | Bearer-token auth; token from `AI_CLUSTER_API_TOKEN` or `security.api_token` |
| 4 | `legacy/start-cluster.sh` | Unbound `MODEL_PATH` variable | Added `MODEL_PATH="${MODEL_PATH:-}"` default |
| 5 | `config.yaml` | No API token configured | Added `security.api_token` (override via env) |
| 6 | `src/root/main.py`, `src/worker/main.py` | Log file handles leaked from `Popen(stdout=open(...))` | Wrapped with `with open(...)` |
| 7 | `cluster.py`, `cluster-dashboard.py` | Had shebangs but were not executable | `chmod +x` applied |

## Verification
- `python3 -m py_compile` on all `.py` files — OK
- `bash -n` on all modified `.sh` files — OK
- `python3 -m pytest -q` — 9 passed
- Import smoke tests for `common.discovery`, `root.main`, `worker.main` — OK
- Live root smoke launch: dashboard reachable, `llama-server` starts, `/api/task/exec` returns `401` without token and dispatches with valid token
- Worker smoke test: worker registers with root on `127.0.0.1`

## Notes
- Binary artifact `dashboard/build/exo-logo.png` still exists (legacy upstream asset). It is not referenced by the current dashboard and does not affect runtime.
- The `notify-action.py` helper is now vendored inside the project; the Desktop entry uses the local copy.
- Existing prior fixes (mDNS exception handling, worker async PID, dashboard `build/` directory, capped UDP discovery set) remain intact.
