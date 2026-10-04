#!/bin/sh
# Build PhoneRemote.app and zip it into dist/ (no Python needed to run it).
# Usage: scripts/build-macos.sh [name of the zip, PhoneRemote-macOS.zip when left out]
# The app only runs on the kind of Mac it was built on: Apple chip or Intel.
set -e
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  echo "Create .venv first: python3 -m venv .venv && .venv/bin/python -m pip install -e ."
  exit 1
fi
.venv/bin/python -m pip install -q pyinstaller
# A folder inside the .app instead of --onefile: PyInstaller advises against one-file app bundles
.venv/bin/python -m PyInstaller --noconfirm --clean --windowed --name PhoneRemote \
  --icon "$PWD/scripts/phone-remote.ico" --osx-bundle-identifier local.phone-remote \
  --add-data "$PWD/src/phone_remote/web:phone_remote/web" \
  --collect-submodules pystray \
  --specpath build --workpath build --distpath dist "$PWD/scripts/entry.py"
# It lives in the menu bar, so no Dock icon. Editing Info.plist breaks the signature PyInstaller made,
# so sign again ("-" is an ad hoc signature: no Apple developer account, Gatekeeper still asks on first open).
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" dist/PhoneRemote.app/Contents/Info.plist
codesign --force --deep --sign - dist/PhoneRemote.app
# ditto keeps the links inside the app, which a plain zip would turn into copies
ditto -c -k --keepParent dist/PhoneRemote.app "dist/${1:-PhoneRemote-macOS.zip}"
echo "Built dist/${1:-PhoneRemote-macOS.zip}"
