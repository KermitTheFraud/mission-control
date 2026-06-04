#!/usr/bin/env bash
# mission-control launcher (macOS) - double-click in Finder.
# serve.py opens the browser itself once the server is up.
cd "$(dirname "$0")" && exec python3 serve.py
