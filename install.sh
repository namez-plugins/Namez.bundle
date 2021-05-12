#!/bin/sh
set -e

echo "Installing Namez python packages..."
echo ""
CURR=$(pwd)
DEST=$CURR/Contents/Libraries/Shared
PIP=$CURR/Contents/Libraries/Shared/bin/pip2.7

echo "Current directory: $CURR"
echo "Using pip: '$PIP'"

echo "Ensure $DEST exists..."
mkdir -p "$DEST"

echo "Setting PYTHONUSERBASE to $CURR"
export PYTHONUSERBASE="$CURR"
echo ""
echo "Install Python into Shared"
echo "$CURR/Contents/Libraries/Shared/bin/pip2.7 install from $CURR/requirements.txt"

"$PIP" install -r requirements.txt -t "$CURR/Contents/Libraries/Shared"
# echo "Syncing installed packages to $DEST"

# echo "Cleaning up original install dir.."
# rm -Rf lib
echo "Removing dist-info from $DEST ..."
cd "$DEST"
ls | grep \.dist-info | xargs rm -Rf
cd -
echo ""
echo "Done"