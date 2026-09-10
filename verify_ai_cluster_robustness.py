#!/usr/bin/env python3
"""Robustness verification for AI Cluster Auto-Connect error-handling patch."""
import ast
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.path.dirname(os.path.abspath(__file__)))

report = []
report.append("=== AI Cluster Error-Handling Robustness Report ===\n")

# 1) Python syntax
report.append("[1] Python syntax check")
py_files = list(BASE.rglob("*.py"))
py_ok = 0
for fp in py_files:
    try:
        ast.parse(fp.read_text())
        py_ok += 1
    except SyntaxError as e:
        report.append(f"  FAIL: {fp.relative_to(BASE)} - {e}")
report.append(f"  PASS: {py_ok}/{len(py_files)} files OK\n")

# 2) Shell syntax
report.append("[2] Shell syntax check")
sh_files = list(BASE.rglob("*.sh"))
sh_ok = 0
for fp in sh_files:
    r = subprocess.run(["bash", "-n", str(fp)], capture_output=True, text=True)
    if r.returncode == 0:
        sh_ok += 1
    else:
        report.append(f"  FAIL: {fp.relative_to(BASE)}")
        report.append(f"    {r.stderr.strip()}")
report.append(f"  PASS: {sh_ok}/{len(sh_files)} files OK\n")

# 3) Import smoke test (exclude GUI)
report.append("[3] Import smoke test (core modules)")
sys.path.insert(0, str(BASE / "src"))
modules = [
    "common.loghub",
    "common.protocol",
    "common.discovery",
    "common.progress_ui",
    "root.main",
    "worker.main",
]
imp_ok = 0
for mod in modules:
    try:
        __import__(mod)
        imp_ok += 1
    except Exception as e:
        report.append(f"  FAIL: {mod} - {e}")
report.append(f"  PASS: {imp_ok}/{len(modules)} modules OK\n")

# 4) Decorator smoke test
report.append("[4] LogHub decorator smoke test")
from common.loghub import LogHub

@LogHub.log_call("VERIFY")
def _test_ok():
    return "ok"

@LogHub.log_call("VERIFY")
def _test_fail():
    raise RuntimeError("smoke test error")

try:
    _test_ok()
except Exception:
    report.append("  FAIL: _test_ok raised unexpectedly")
else:
    report.append("  PASS: _test_ok logged SUCCESS")

try:
    _test_fail()
except RuntimeError:
    report.append("  PASS: _test_fail logged FAILED and re-raised")
except Exception as e:
    report.append(f"  FAIL: unexpected exception {e}")

report.append("")
report.append("=== Verification complete ===")

print("\n".join(report))
