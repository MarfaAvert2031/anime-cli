#!/usr/bin/env sh
# Starts anime-cli using its own virtual environment.
cd "$(dirname "$0")"
exec venv/bin/python player.py "$@"
