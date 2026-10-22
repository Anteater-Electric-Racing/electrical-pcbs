#!/bin/bash
# One-time Mac setup for the Anteater Racing parts library. Double-click in Finder.
# (Windows users: run "Setup (run once).bat" instead.)
cd "$(dirname "$0")" || exit 1
ROOT="$(pwd)"
LIBRARY="$ROOT/Anteater Parts"
HELPER="$ROOT/Library Manager/anteater_setup.py"

step() { printf '\n\033[36m[%s/5] %s\033[0m\n' "$1" "$2"; }
ok()   { printf '  \033[32mOK\033[0m  %s\n' "$1"; }
fail() { printf '  \033[31m!!\033[0m  %s\n\n' "$1"; read -r -p "Fix the above, then run Setup again. Press Enter to close"; exit 1; }
ask()  { read -r -p "  $1 [Y/n] " a; [[ ! "$a" =~ ^[nN] ]]; }

echo "Anteater Racing - Parts Library setup (Mac)"

# Homebrew lives in different places on Apple Silicon and Intel Macs
for b in /opt/homebrew/bin /usr/local/bin; do [[ -x "$b/brew" ]] && PATH="$b:$PATH"; done

step 1 "Python 3.11 or newer"
py_ok() { command -v python3 >/dev/null && python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))'; }
if ! py_ok; then
    if command -v brew >/dev/null && ask "Python 3.11+ not found. Install it with Homebrew?"; then
        brew install python@3.12 && hash -r
    fi
    py_ok || fail "Install Python 3.11+ from https://www.python.org/downloads/macos/, then run Setup again."
fi
ok "$(python3 --version)"
if command -v git >/dev/null; then ok "Git found"; else
    printf '  Git not found: install GitHub Desktop (https://desktop.github.com) to publish parts.\n'
fi

step 2 "KiCad 10"
is_kicad10() { [[ -x "$1/Contents/MacOS/kicad-cli" ]] && "$1/Contents/MacOS/kicad-cli" version 2>/dev/null | grep -q '^10\.'; }
find_kicad() {
    local saved="$HOME/.config/anteater-parts/kicad-cli"
    local c
    for c in "$( [[ -f "$saved" ]] && dirname "$(dirname "$(dirname "$(cat "$saved")")")" )" \
             /Applications/KiCad/KiCad.app /Applications/KiCad.app \
             "$HOME/Applications/KiCad/KiCad.app" "$HOME/Applications/KiCad.app"; do
        [[ -n "$c" ]] && is_kicad10 "$c" && { echo "$c"; return; }
    done
    # Spotlight, then the usual places people drop it
    while IFS= read -r c; do is_kicad10 "$c" && { echo "$c"; return; }; done < <(
        mdfind 'kMDItemFSName == "KiCad.app"' 2>/dev/null
        find "$HOME/Documents" "$HOME/Desktop" "$HOME/Downloads" -maxdepth 5 -name KiCad.app -type d 2>/dev/null)
}
echo "  Looking for KiCad 10..."
KICAD_APP="$(find_kicad)"
if [[ -z "$KICAD_APP" ]]; then
    echo "  KiCad 10 wasn't found automatically."
    echo "  If it IS installed: drag KiCad.app into this window, then press Enter."
    read -r -p "  If it isn't installed: just press Enter " answer
    # Terminal pastes a dragged path with escaped spaces and a trailing space
    answer="$(printf '%s' "$answer" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    answer="${answer//\\ / }"; answer="${answer#\'}"; answer="${answer%\'}"; answer="${answer%/}"
    if [[ -n "$answer" ]]; then
        is_kicad10 "$answer" || fail "That isn't KiCad 10's KiCad.app (it must be version 10)."
        KICAD_APP="$answer"
    fi
fi
if [[ -z "$KICAD_APP" ]]; then
    if command -v brew >/dev/null && ask "Install KiCad 10 with Homebrew?"; then
        brew install --cask kicad
        KICAD_APP="$(find_kicad)"
    fi
    [[ -n "$KICAD_APP" ]] || fail "Install KiCad 10 from https://www.kicad.org/download/macos/, open it once, quit, then run Setup again."
fi
# Remember where it is, so the Library Manager's previews and board tools find it too
mkdir -p "$HOME/.config/anteater-parts"
echo "$KICAD_APP/Contents/MacOS/kicad-cli" > "$HOME/.config/anteater-parts/kicad-cli"
export KICAD_CLI="$KICAD_APP/Contents/MacOS/kicad-cli"
ok "KiCad 10 found: $KICAD_APP"

step 3 "SQLite ODBC driver (lets KiCad read the parts database)"
if ! command -v brew >/dev/null; then
    fail "Homebrew is needed for the database driver. Install it from https://brew.sh, then run Setup again."
fi
if ! brew list sqliteodbc >/dev/null 2>&1; then
    echo "  Installing the SQLite ODBC driver with Homebrew..."
    brew install sqliteodbc || fail "brew install sqliteodbc failed (see above)."
fi
DRIVER="$(brew --prefix sqliteodbc)/lib/libsqlite3odbc.dylib"
[[ -f "$DRIVER" ]] || fail "Driver not found at $DRIVER"
ok "Driver installed"
# Use the data source name the library itself asks for, so setup can never disagree with it.
DSN="$(python3 -c 'import json,re,sys; s=json.load(open(sys.argv[1]))["source"]["connection_string"]; m=re.search(r"DSN=([^;]+)", s); print(m.group(1) if m else "AnteaterSQLite")' "$LIBRARY/appdata/parts.kicad_dbl")"
ODBC_INI="$HOME/.odbc.ini"
if grep -q "^\[$DSN\]" "$ODBC_INI" 2>/dev/null; then
    ok "Data source '$DSN' already in ~/.odbc.ini"
else
    # append; never touch other people's/other tools' data sources
    printf '\n[%s]\nDriver=%s\nDescription=Anteater Racing KiCad parts library\n' "$DSN" "$DRIVER" >> "$ODBC_INI"
    ok "Data source '$DSN' added to ~/.odbc.ini"
fi

step 4 "Connect the library to KiCad"
while pgrep -xq "kicad|eeschema|pcbnew" || pgrep -fq "KiCad.app/Contents/MacOS"; do
    read -r -p "  KiCad is open. Save your work, quit KiCad (Cmd+Q), then press Enter "
done
python3 "$HELPER" "$LIBRARY"; rc=$?
if [[ $rc -eq 2 ]] && ask "This Mac is connected to a different Library Manager library. Switch it to the Anteater library?"; then
    python3 "$HELPER" "$LIBRARY" --switch; rc=$?
fi
[[ $rc -eq 0 ]] || fail "Connecting to KiCad failed (see message above)."
ok "KiCad will show the parts under 'Anteater Parts' in the symbol chooser"

step 5 "Desktop shortcut"
chmod +x "$ROOT/Open Library Manager.command" 2>/dev/null
SHORTCUT="$HOME/Desktop/Anteater Parts Library.command"
printf '#!/bin/bash\nexec "%s"\n' "$ROOT/Open Library Manager.command" > "$SHORTCUT"
chmod +x "$SHORTCUT"
ok "Shortcut 'Anteater Parts Library' added to your Desktop"

printf '\n\033[32mSetup complete. Double-click "Anteater Parts Library" on your Desktop to add or browse parts.\033[0m\n'
read -r -p "Press Enter to close"
