#!/bin/bash
# Mac launcher for the Anteater parts library. Double-click in Finder.
# (Windows users: use "Open Library Manager.bat" instead.)
cd "$(dirname "$0")" || exit 1
for b in /opt/homebrew/bin /usr/local/bin; do [[ -d "$b" ]] && PATH="$b:$PATH"; done

# Only one Library Manager may edit the library at a time; two copies corrupt saves.
if pgrep -f "Library Manager/app.py" >/dev/null; then
    echo "The Library Manager is already running."
    echo "Closing the browser tab does NOT stop it. Either:"
    echo "  - click \"Quit manager\" at the bottom-left of the app, or"
    echo "  - close the other Terminal window running it"
    echo "then open this again."
    read -r -p "Press Enter to close"
    exit 0
fi

if command -v git >/dev/null; then
    echo "Getting the latest parts from GitHub..."
    git pull --ff-only || echo "  Could not update automatically. Use Publish in the app, or pull in GitHub Desktop."
    echo
fi

# KiCad may live outside /Applications; Setup saved where it found it
if [[ -z "$KICAD_CLI" && -f "$HOME/.config/anteater-parts/kicad-cli" ]]; then
    export KICAD_CLI="$(cat "$HOME/.config/anteater-parts/kicad-cli")"
fi

if ! python3 "Library Manager/app.py" --library "Anteater Parts"; then
    echo
    echo "The Library Manager stopped - see the message above. If it isn't clear, run \"Setup (run once).command\" again or message the library owner."
    read -r -p "Press Enter to close"
fi
