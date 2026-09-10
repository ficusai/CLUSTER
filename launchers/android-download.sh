#!/usr/bin/env bash
# Download files/folders from Android phone (Termux) to the PC.
# Uses scp -r (secure copy) over the existing SSH key auth.

PHONE_HOST="10.0.0.190"
PHONE_PORT=8022
PHONE_USER="u0_a377"

ICON_OK="emblem-ok-symbolic"
ICON_ERR="dialog-error-symbolic"

echo "Download from Android Phone -> PC"
echo "=================================="
echo ""

# Optional preset path if given as argument
if [ -n "$1" ]; then
    REMOTE_PATH="$1"
else
    echo -n "Enter the file or folder path ON THE PHONE: "
    read -r REMOTE_PATH
fi

if [ -z "$REMOTE_PATH" ]; then
    echo "No path given. Aborting."
    read -r -p "Press Enter to close..."
    exit 1
fi

echo -n "Where to save it on THIS PC? [default: $HOME/Downloads] "
read -r LOCAL_DEST
if [ -z "$LOCAL_DEST" ]; then
    LOCAL_DEST="$HOME/Downloads"
fi
mkdir -p "$LOCAL_DEST"

echo ""
echo "Checking phone is reachable..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 \
     -p "$PHONE_PORT" "$PHONE_USER@$PHONE_HOST" true 2>/dev/null; then
    echo "NOT CONNECTED: open Termux on the phone and retry."
    notify-send -i "$ICON_ERR" -t 8000 "Android Download" "NOT CONNECTED: phone unreachable." || true
    read -r -p "Press Enter to close..."
    exit 1
fi

echo "Downloading: ${PHONE_USER}@${PHONE_HOST}:${REMOTE_PATH}"
echo "     -> ${LOCAL_DEST}"
echo ""

if scp -r -o BatchMode=yes -o ConnectTimeout=10 -P "$PHONE_PORT" \
    "$PHONE_USER@$PHONE_HOST:${REMOTE_PATH}" "$LOCAL_DEST/" ; then
    echo ""
    echo "Download complete."
    notify-send -i "$ICON_OK" -t 8000 "Android Download" "Saved to $LOCAL_DEST" || true
else
    echo ""
    echo "Download FAILED. Check the path exists on the phone."
    notify-send -i "$ICON_ERR" -t 8000 "Android Download" "Download failed." || true
fi

read -r -p "Press Enter to close..."
