#!/usr/bin/env bash
# ====================================================================
# SinaBox macOS One-Click Installer
# Developed by Sina Khanzadeh
# ====================================================================

set -e

echo "==> Installing SinaBox for macOS..."

TARGET_DIR="$HOME/.sinabox"
BIN_DIR="/usr/local/bin"
mkdir -p "$TARGET_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/sinabox.sh" "$TARGET_DIR/sinabox.sh"
chmod +x "$TARGET_DIR/sinabox.sh"

if [ -w "$BIN_DIR" ]; then
    ln -sf "$TARGET_DIR/sinabox.sh" "$BIN_DIR/sinabox"
    echo "[OK] Symlinked to $BIN_DIR/sinabox"
else
    mkdir -p "$HOME/.local/bin"
    ln -sf "$TARGET_DIR/sinabox.sh" "$HOME/.local/bin/sinabox"
    echo "[OK] Symlinked to $HOME/.local/bin/sinabox (ensure ~/.local/bin is in your PATH)"
fi

echo ""
echo "✅ SinaBox for macOS installed successfully!"
echo "Run 'sinabox --help' to get started."
