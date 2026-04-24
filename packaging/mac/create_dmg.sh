#!/bin/bash
# Create DMG for macOS (onefile mode)
APP_NAME="编码转换器"
DIST_DIR="../../dist"
DMG_NAME="编码转换器-macOS.dmg"

cd "$(dirname "$0")"

if [ -f "$DIST_DIR/$APP_NAME" ]; then
    echo "Creating DMG for $APP_NAME..."
    
    # Create a temporary directory for DMG contents
    TEMP_DIR=$(mktemp -d)
    cp "$DIST_DIR/$APP_NAME" "$TEMP_DIR/"
    
    # Create Applications folder alias
    ln -s /Applications "$TEMP_DIR/Applications"
    
    if command -v create-dmg &> /dev/null; then
        create-dmg \
          --volname "$APP_NAME" \
          --window-pos 200 120 \
          --window-size 600 400 \
          --icon-size 100 \
          --app-drop-link 400 200 \
          "$DIST_DIR/$DMG_NAME" \
          "$TEMP_DIR"
    else
        echo "create-dmg not found. Using hdiutil..."
        hdiutil create -volname "$APP_NAME" \
          -srcfolder "$TEMP_DIR" \
          -ov -format UDZO \
          "$DIST_DIR/$DMG_NAME"
    fi
    
    # Clean up
    rm -rf "$TEMP_DIR"
    
    echo "DMG created: $DIST_DIR/$DMG_NAME"
else
    echo "Error: $DIST_DIR/$APP_NAME not found"
    exit 1
fi
