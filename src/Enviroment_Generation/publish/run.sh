#!/bin/bash

# Get the full path to the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Extract the full path up to (and including) "AIprobe"
AIPROBE_ROOT=$(echo "$SCRIPT_DIR" | sed -E 's|(.*AIprobe).*|\1|')

# Determine OS-specific build folder
OS="$(uname -s)"
ARCH="$(uname -m)"

if [[ "$OS" == "Linux" ]]; then
    APP_DIR="linux-x64"
elif [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        APP_DIR="osx-arm64"
    else
        APP_DIR="osx-x64"
    fi
elif [[ "$OS" =~ MINGW.* || "$OS" =~ CYGWIN.* || "$OS" =~ MSYS.* ]]; then
    APP_DIR="win-x64"
else
    echo "❌ Unsupported OS: $OS"
    exit 1
fi

echo "✅ Detected OS folder: $APP_DIR"
echo "📁 AIprobe root path resolved as: $AIPROBE_ROOT"

# Path to config file
CONFIG_FILE="$SCRIPT_DIR/$APP_DIR/AIprobeConfig.xml"