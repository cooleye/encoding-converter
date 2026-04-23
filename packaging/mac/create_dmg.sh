#!/bin/bash
# Create DMG for macOS
APP_NAME="编码转换器"
DIST_DIR="../../dist"
DMG_NAME="编码转换器-macOS.dmg"

cd "$(dirname "$0")"

if [ -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo "Creating DMG for $APP_NAME..."
    
    if command -v create-dmg &> /dev/null; then
        create-dmg \
          --volname "$APP_NAME" \
          --window-pos 200 120 \
          --window-size 600 400 \
          --icon-size 100 \
          --app-drop-link 400 200 \
          "$DIST_DIR/$DMG_NAME" \
          "$DIST_DIR/$APP_NAME.app"
    else
        echo "create-dmg not found. Using hdiutil..."
        hdiutil create -volname "$APP_NAME" \
          -srcfolder "$DIST_DIR/$APP_NAME.app" \
          -ov -format UDZO \
          "$DIST_DIR/$DMG_NAME"
    fi
    
    echo "DMG created: $DIST_DIR/$DMG_NAME"
else
    echo "Error: $DIST_DIR/$APP_NAME.app not found"
    exit 1
fi
