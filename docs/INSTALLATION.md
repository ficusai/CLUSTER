# Installation Guide

## Prerequisites

- **Python** 3.9+ (3.11 recommended)
- **pip**
- Recommended packages: `pyyaml`, `zeroconf`, `psutil`, `rich`, `PySide6`

```bash
pip install -r requirements.txt
```

For `cluster.py gui`, `PySide6` is required. Without it, the application falls back to a terminal UI.

---

## Linux (system-wide)

```bash
sudo ./scripts/install.sh
```

This installs:
- `/usr/local/bin/ai-cluster` — wrapper binary
- `/usr/share/icons/hicolor/scalable/apps/ai-cluster.svg`
- `/usr/share/applications/ai-cluster-*.desktop`
- `/etc/systemd/system/ai-cluster-*.service`

Enable auto-start:

```bash
sudo systemctl enable ai-cluster-root.service
sudo systemctl start ai-cluster-root.service
sudo systemctl status ai-cluster-root.service
```

Logs:

```bash
sudo journalctl -u ai-cluster-root.service -f
```

---

## Linux (user-only, no sudo)

```bash
./scripts/install-local.sh
```

This installs user-level systemd units under `~/.config/systemd/user/` and desktop entries under `~/.local/share/applications/`. It also copies `linux/ai-cluster-root.desktop` to `~/Desktop/` as `ai-cluster.desktop`.

Manage services without `sudo`:

```bash
systemctl --user start ai-cluster-root.service
systemctl --user enable ai-cluster-root.service
journalctl --user -u ai-cluster-root.service -f
```

---

## Desktop Launcher

The live Desktop file is:

```
~/Desktop/ai-cluster.desktop
```

It executes:

```
~/ai-cluster/launcher-notify.sh --root
```

This starts the root node and shows a notification with **Stop / Restart / Logs** action buttons.

---

## macOS

```bash
make build
./dist/cluster-darwin-x86_64 root
```

To auto-start at boot, create a `LaunchAgent` plist in `~/Library/LaunchAgents/`.

---

## Windows

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python cluster.py root
```

For deployment, build with PyInstaller and publish to a shared folder. Automated Windows onboarding is not yet implemented.

---

## Android (Termux)

1. Install Termux from F-Droid.
2. Run the bootstrap on the device:

```bash
bash scripts/setup-termux.sh
```

3. From the Fedora host, deploy or connect via SSH (port `8022` by default).

To build the llama.cpp `rpc-server` binary directly on the device, use:

```bash
bash legacy/setup-android.sh
```

To auto-start on boot, use `Termux:Boot` from F-Droid and place a boot script in `~/.termux/boot/`. A reference script is in `legacy/termux-boot-script.sh`.

---

## iOS (Jailbroken)

1. Connect via SSH (USB tunnel with `iproxy` or Wi-Fi).
2. Run the on-device build script:

```bash
bash legacy/setup-iphone.sh
```

3. Start the worker with `~/ai-cluster/start-worker.sh`.

---

## Docker (advanced)

A worker container can be built from the project source. Expose:
- `52052/udp` (discovery)
- `50052/tcp` (RPC)
- `52053/tcp` (control channel)
- `8080/tcp` (HTTP API, if running root)

---

## Uninstall

```bash
sudo make uninstall
```

or manually remove the paths listed above and run `sudo systemctl daemon-reload`.
