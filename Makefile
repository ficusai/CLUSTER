.PHONY: help install uninstall install-local uninstall-local build run clean

ifeq ($(shell id -u), 0)
PREFIX ?= /usr/local
else
PREFIX ?= $(HOME)/.local
endif

BINDIR ?= $(PREFIX)/bin
BINARY_NAME=ai-cluster
PLATFORM:=$(shell uname -s | tr '[:upper:]' '[:lower:]')
ARCH:=$(shell uname -m)
BINARY=dist/cluster-$(PLATFORM)-$(ARCH)

help:
	@echo "AI Cluster Auto-Connect — Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  build           Build the executable (requires pyinstaller)"
	@echo "  install         Build and install system-wide (requires sudo)"
	@echo "  uninstall       Remove system-wide installation (requires sudo)"
	@echo "  install-local   Install for current user (~/.local)"
	@echo "  uninstall-local Remove user-level installation"
	@echo "  run             Run in terminal interactive mode"
	@echo "  run-gui         Run with desktop GUI (requires PySide6)"
	@echo "  clean           Remove build artifacts"

build:
	@bash build/build.sh

install:
	@bash scripts/install.sh

uninstall:
	@echo "=== Uninstalling AI Cluster ==="
	@sudo rm -f $(BINDIR)/$(BINARY_NAME) || true
	@sudo rm -f $(PREFIX)/share/icons/hicolor/scalable/apps/ai-cluster.svg || true
	@sudo rm -f $(PREFIX)/share/applications/ai-cluster*.desktop || true
	@sudo rm -f /etc/systemd/system/ai-cluster*.service || true
	@sudo systemctl daemon-reload 2>/dev/null || true
	@echo "Uninstalled."

install-local:
	@PREFIX="$(PREFIX)" bash scripts/install-local.sh

uninstall-local:
	@PREFIX="$(PREFIX)" bash scripts/install-local.sh --uninstall

run:
	python3 cluster.py

run-gui:
	python3 cluster.py --gui

run-root:
	python3 cluster.py --root

run-worker:
	python3 cluster.py --worker

clean:
	rm -rf dist/ __pycache__ */__pycache__ */*/__pycache__
	rm -rf /tmp/pyibuild-* 2>/dev/null || true
	@echo "Clean."
