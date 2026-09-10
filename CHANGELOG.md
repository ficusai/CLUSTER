# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.3.0] — 2026-07-04

### Fixed
- `ai-cluster-stop.sh`: undefined `PID_FILE` crash under `set -u` (#1).
- `ai-cluster-events.sh`: dead `current.log` path; now writes to `logs/` glob-friendly path (#2).
- `dashboard/build/`: removed upstream binary artifacts (`exo-logo.png`, `favicon.ico`, `_app/`) (#3).
- `src/common/discovery.py`: added `SO_REUSEPORT` and improved bind error logging for UDP listener (#4).
- `launcher.sh`: dead onboarding stubs replaced with clear status messages (#5-9).
- `notify-action.py`: button label "Open Logs" → "Open Terminal" (#13).
- `ai-cluster-events.sh`: `read -r` prompts now gated with `[ -t 0 ]` for non-interactive use (#26).
- `ai-cluster-stop.sh`: `read -p` prompt gated with `[ -t 0 ]` (#26).
- `cluster-dashboard.py`: replaced local `_log_call` with `LogHub.log_call` decorator (#28).
- `AGENTS.md`: fixed stale descriptions for `deploy-worker.sh` (#23-24).
- `.gitignore`: removed duplicate `*.log` entry (#27).
- `install.sh`: removed broken Python wrapper path that pointed to nonexistent `/../share/ai-cluster` (#30).
- `linux/connect.sh`, `macos/connect.sh`, `windows/connect.bat`: replaced echo stubs with actionable instructions (#9).

### Removed
- Empty `config/` directory (#16).
- `dashboard/build/_app/`, `exo-logo.png`, `favicon.ico` — upstream SvelteKit artifacts (#3, #21).

---

## [1.2.0] — 2026-06-25

### Added
- Auto-healing supervisor for topology changes
- iPhone + Android worker support (jailbroken + Termux)
- IPv4 + SSH key authentication with keepalive

### Fixed
- Supervisor `set +e` loop stability
- Android IP drift handling via dynamic re-resolution

---

## [1.1.0] — 2026-06-20

- Two-node RPC inference validated (Fedora + Android)
- UDP broadcast fallback when mDNS unavailable
- Tensor parallelism across llama.cpp RPC shards

---

## [1.0.0] — 2026-06-15

- Initial heterogeneous cluster prototype
