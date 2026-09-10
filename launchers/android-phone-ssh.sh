#!/usr/bin/env bash

HOST="10.0.0.190"
PORT=8022
USER="u0_a377"

ICON_OK="emblem-ok-symbolic"
ICON_ERR="dialog-error-symbolic"

check_ssh() {
    ssh -o BatchMode=yes -o ConnectTimeout=5 -o ConnectionAttempts=1 -o StrictHostKeyChecking=accept-new -p "$PORT" "$USER@$HOST" true 2>/dev/null
}

if check_ssh; then
    notify-send -i "$ICON_OK" -t 6000 "Android Phone" "Connected to $USER@$HOST:$PORT" || true
else
    notify-send -i "$ICON_ERR" -t 8000 "Android Phone" "NOT CONNECTED: sshd not responding on $HOST:$PORT" || true
    read -r -p "Phone not reachable. Retry? [y/N] " -n 1 -r
    echo
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        exit 1
    fi
    while ! check_ssh; do
        notify-send -i "$ICON_ERR" -t 4000 "Android Phone" "Waiting for sshd on $HOST:$PORT ..." || true
        sleep 5
    done
    notify-send -i "$ICON_OK" -t 6000 "Android Phone" "Connected to $USER@$HOST:$PORT" || true
fi

ssh "$USER@$HOST" -p "$PORT"

EXIT=$?
if [ "$EXIT" -eq 0 ]; then
    notify-send -i "$ICON_OK" -t 6000 "Android Phone" "Disconnected from $HOST (session ended normally)" || true
else
    notify-send -i "$ICON_ERR" -t 8000 "Android Phone" "Disconnected from $HOST (exit code $EXIT)" || true
fi

exit "$EXIT"
