#!/usr/bin/env bash
# =============================================================================
# USB Tethering Setup (Fedora - Root Node)
# Handles both iPhone and Android connections.
#
# Run this once when connecting a new device. After pairing, it's remembered.
# =============================================================================
set -euo pipefail

echo "============================================"
echo "  USB Tethering Setup"
echo "============================================"
echo "Choose device type:"
echo "  1) iPhone (jailbroken, via libimobiledevice)"
echo "  2) Android (via RNDIS/CDC-ECM)"
echo -n "Enter choice [1-2]: "
read DEVICE_TYPE

case "${DEVICE_TYPE}" in
    1)
        echo ""
        echo "--- iPhone Setup ---"

        # Load ipheth kernel module
        echo "[USB] Loading ipheth kernel module..."
        sudo modprobe ipheth 2>/dev/null && echo "[USB] ipheth loaded" || echo "[USB] ipheth already loaded"

        # Ensure usbmuxd is running
        echo "[USB] Starting usbmuxd service..."
        sudo systemctl start usbmuxd 2>/dev/null || echo "[USB] usbmuxd already running"

        # Pair with iPhone
        echo "[USB] Pairing with iPhone..."
        echo "   CHECK YOUR iPhone: You should see a 'Trust this computer?' prompt."
        echo "   Enter your passcode and tap 'Trust'."
        sudo idevicepair pair 2>&1 || true

        # Check pairing
        sudo idevicepair validate || {
            echo "[USB] Pairing failed. Trying again..."
            sleep 2
            sudo idevicepair pair || echo "[USB] Retry pairing. Make sure iPhone is unlocked."
        }

        echo ""
        echo "On your iPhone:"
        echo "  1. Settings > Personal Hotspot > Enable"
        echo "  2. Use 'USB Only' if available"
        echo ""
        ;;

    2)
        echo ""
        echo "--- Android Setup ---"

        # Load RNDIS/CDC-ECM modules
        echo "[USB] Loading Android tethering modules..."
        sudo modprobe rndis_host 2>/dev/null || echo "[USB] rndis_host already loaded or unavailable"
        sudo modprobe cdc_ether 2>/dev/null || echo "[USB] cdc_ether already loaded or unavailable"

        echo ""
        echo "On your Android:"
        echo "  1. Connect phone to computer via USB cable"
        echo "  2. Settings > Connections > Mobile Hotspot/Tethering"
        echo "  3. Enable 'USB Tethering'"
        echo ""
        echo "Note: On Samsung, it's under Settings > Connections"
        echo "      On Pixel/Stock, it's under Settings > Network & Internet > Hotspot & Tethering"
        echo ""
        ;;

    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo "============================================"
echo "  After enabling tethering, wait 5-10 seconds"
echo "  then check for the new network interface:"
echo ""
echo "    ip addr show | grep -E 'ipheth|enp.*u|usb0'"
echo "    ip route | grep -E 'ipheth|enp.*u|usb0'"
echo ""
echo "  To find the device's assigned IP:"
echo "    ip -4 addr show | grep -E 'ipheth|enp.*u|usb0' | grep inet"
echo ""
echo "  Update cluster-config.env with the IP address."
echo "============================================"
