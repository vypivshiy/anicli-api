"""Extract HLS stream URLs from Alloha player (research script).

Usage:
    python test_alloha.py [PLAYER_URL]

Requires: node + puppeteer. test_alloha.mjs must be in the same directory.
"""

import subprocess
import sys
from pathlib import Path

PLAYER_URL = (
    "https://alloha.yani.tv/?token_movie=d9a17e70501e90d29994419cd7575e"
    "&season=1&episode=4"
    "&token=8b5512267a2a52e9de06d67d342e0c"
    "&skip_button=%5Bopening%5D0-39%2C%5Bending%5D1369-1388"
)

HELPER = Path(__file__).parent / "test_alloha.mjs"

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else PLAYER_URL
    sys.exit(subprocess.call(["node", str(HELPER), url]))
