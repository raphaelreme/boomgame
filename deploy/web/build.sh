set -e

/bin/rm -rf build  # Delete previous build
cp -r ../../src/boomgame .
python -m pygbag --title BOOM --icon icon.png --app_name BOOM --ume_block 1 --no_opt --build .
/bin/rm -r boomgame
