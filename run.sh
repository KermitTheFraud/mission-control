#!/usr/bin/env bash
# mission-control launcher (Linux / Omarchy) - double-click or `./run.sh`.
# serve.py opens the browser itself once the server is up.
cd "$(dirname "$0")" && exec python3 serve.py
