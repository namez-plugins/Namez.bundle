#!/bin/sh

echo "Installing Namez python packages..."
echo ""
CURR=$(pwd)
DEST=$CURR/Contents/Libraries/Shared

echo "Current directory: $CURR"

echo "Ensure $DEST exists..."
mkdir -p "$DEST"

echo "Setting PYTHONUSERBASE to $CURR"
export PYTHONUSERBASE="$CURR"
echo ""
echo "Start install from $CURR/requirements.txt"
pip install -I --user -r "$CURR/requirements.txt"
echo "Syncing installed packages to $DEST"
# mv -v lib/python/site-packages/* "$DEST"

echo "Cleaning up original install dir.."
rm -Rf lib
echo "Removing dist-info from $DEST ..."
cd "$DEST"
ls | grep \.dist-info | xargs rm -Rf
cd -
echo ""
echo "Done"