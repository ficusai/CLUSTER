@echo off
REM AI Cluster Auto-Connect — Windows worker quick-connect
REM Run this on a target Windows machine to join the cluster as a worker.
echo AI Cluster Auto-Connect -- Windows Worker
echo.
echo To join this machine as a worker:
echo   1. Ensure Python 3.9+ is installed (winget install Python.Python.3)
echo   2. Clone this repo: git clone ^<repo-url^> ai-cluster-auto-connect
echo   3. cd ai-cluster-auto-connect
echo   4. python src\worker\main.py
echo.
echo The worker will auto-discover the root via mDNS/UDP broadcast.
