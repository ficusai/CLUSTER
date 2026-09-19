# DEAD-CODE Archive

This directory archives code that was verified unused (dead) as of 2026-09-19 and
moved out of the live `src/` tree. Everything here is intentionally NOT imported or
invoked by the running application; it is preserved for history and reference.

## How to restore

Any file can be restored by moving it back to its original path:

    git mv DEAD-CODE/src/common/progress_ui.py src/common/progress_ui.py

## Inventory

### Whole files (moved verbatim; path mirrors original layout)

| Archived path | Original live path | Reason it was dead |
| --- | --- | --- |
| `DEAD-CODE/src/common/progress_ui.py` | `src/common/progress_ui.py` | Shadowed by the `src/common/progress_ui/` package; unimportable shim |
| `DEAD-CODE/src/common/loghub/notify_orchestrator.py` | `src/common/loghub/notify_orchestrator.py` | `NotifyOrchestratorMixin.notify_orchestrator()` had zero call sites |
| `DEAD-CODE/src/gui/main_window.py` | `src/gui/main_window.py` | Shadowed by the `src/gui/main_window/` package; unimportable shim |
| `DEAD-CODE/src/gui/widgets/__init__.py` | `src/gui/widgets/__init__.py` | Empty placeholder; package never imported |
| `DEAD-CODE/src/root/http/__init__.py` | `src/root/http/__init__.py` | Empty placeholder; package never imported |
| `DEAD-CODE/src/root/cluster/api_handler.py` | `src/root/cluster/api_handler.py` | Docstring-only stub; code moved into `start_http_api.py` |
| `DEAD-CODE/src/root/detection/find_bin_dir.py` | `src/root/detection/find_bin_dir.py` | Dead duplicate of live `cluster/FindBinDirMixin` |
| `DEAD-CODE/src/root/detection/find_llama_bin.py` | `src/root/detection/find_llama_bin.py` | Dead duplicate of live `cluster/FindLlamaBinMixin` |
| `DEAD-CODE/src/root/detection/find_rpc_bin.py` | `src/root/detection/find_rpc_bin.py` | Dead duplicate of live `cluster/FindRpcBinMixin` |
| `DEAD-CODE/src/root/detection/find_model.py` | `src/root/detection/find_model.py` | Dead duplicate of live `cluster/FindModelMixin` |
| `DEAD-CODE/src/root/ollama/` (5 files) | `src/root/ollama/` | Package never imported; superseded by `cluster/*Mixin` |
| `DEAD-CODE/src/root/utils/` (6 files) | `src/root/utils/` | Only consumer was the dead `api_handler.py`; superseded by cluster mixins |
| `DEAD-CODE/src/root/registry/contains.py` | `src/root/registry/contains.py` | `ContainsMixin.contains()` had zero call sites |
| `DEAD-CODE/src/worker/config/` (3 files) | `src/worker/config/` | Package never imported; duplicates live worker mixins |
| `DEAD-CODE/src/worker/detection/get_local_ip.py` | `src/worker/detection/get_local_ip.py` | Byte-for-byte duplicate of `common/discovery/get_local_ip.py` |
| `DEAD-CODE/src/worker/handlers/__init__.py` | `src/worker/handlers/__init__.py` | Empty placeholder; package never imported |
| `DEAD-CODE/assets/ai-cluster.svg` | `assets/ai-cluster.svg` | Orphaned asset; not referenced by any desktop file, script, or installer |

### Extracted dead code (removed from still-live files)

| Archived path | Origin | Reason |
| --- | --- | --- |
| `DEAD-CODE/src/common/archive/protocol_dead_constants.py` | `src/common/protocol.py` (`MAGIC`, `PROTO_VERSION`, `MSG_DEPLOY`, `MSG_DEPLOY_ACK`) | Never referenced; deploy message type never implemented |
| `DEAD-CODE/src/common/archive/progress_ui_notify_once.py` | `src/common/progress_ui/state.py` (`StateMixin.notify_once`) | Zero call sites |

## Known related anomalies (NOT archived — out of scope)

- `MainWindow` currently does not inherit from a Qt widget (broken refactor, needs a fix, not deletion).
- `ClusterBridge` is never wired to the cluster via `ui=` (unfinished integration, needs a fix).
- `src/common/progress_ui/lifecycle.py` uses `Live`/`threading` without importing them (runtime NameError, needs a fix).