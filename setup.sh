#!/usr/bin/env bash
# anime-cli setup for Linux / macOS. Run with: bash setup.sh
set -e
cd "$(dirname "$0")"

have() { command -v "$1" >/dev/null 2>&1; }

# 1. System programs
if have pacman; then
    sudo pacman -S --needed --noconfirm python nodejs npm git mpv ffmpeg
elif have apt; then
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip nodejs npm git mpv ffmpeg
elif have dnf; then
    sudo dnf install -y python3 python3-pip nodejs npm git mpv ffmpeg
elif have brew; then
    brew install python node git mpv ffmpeg
else
    echo "Unknown package manager. Install manually: python3, node, npm, git, mpv, ffmpeg"
fi

# 2. Python virtual environment + libraries
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

# 3. Node package (JustalK)
if have npm; then
    [ -f package.json ] || npm init -y >/dev/null
    npm install @justalk/anime-api
fi

# 4. Settings file
if [ ! -f settings.xml ] && [ -f settings.example.xml ]; then
    cp settings.example.xml settings.xml
    echo "Created settings.xml from settings.example.xml"
fi

echo
echo "Done. Run the CLI with:"
echo "  .venv/bin/python player.py"