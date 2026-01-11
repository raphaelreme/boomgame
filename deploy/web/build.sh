# NOTE: To optimize some assets, ffmpeg should be installed.

set -e

/bin/rm -rf build  # Delete previous build
cp -r ../../src/boomgame .
uv run pygbag --package BOOM --title BOOM --icon icon.png --app_name BOOM --build .
/bin/rm -rf boomgame
