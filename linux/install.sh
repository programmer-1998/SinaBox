#!/usr/bin/env bash
# ====================================================================
# SinaBox Linux One-Click Installer
# Developed by Sina Khanzadeh
# ====================================================================

set -e

RED="\033[31m"
GREEN="\033[32m"
CYAN="\033[36m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}==> Installing SinaBox for Linux...${RESET}"

# 1. Check bubblewrap
if ! command -v bwrap &>/dev/null; then
    echo -e "${RED}Bubblewrap (bwrap) is not installed!${RESET}"
    echo "Installing bwrap..."
    if command -v apt &>/dev/null; then
        sudo apt update && sudo apt install -y bubblewrap
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm bubblewrap
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y bubblewrap
    else
        echo -e "${RED}Please install bubblewrap using your package manager.${RESET}"
        exit 1
    fi
fi

# 2. Setup user binary directory
BIN_DIR="$HOME/.local/bin"
SHARE_DIR="$HOME/.local/share/sinabox"
mkdir -p "$BIN_DIR" "$SHARE_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Install CLI binary
cp "$SCRIPT_DIR/sinabox.py" "$BIN_DIR/sinabox"
chmod +x "$BIN_DIR/sinabox"

# Run desktop integration & patching
python3 "$SCRIPT_DIR/install_desktop.py"
python3 "$SCRIPT_DIR/desktop_patcher.py"

echo -e "\n${GREEN}${BOLD}✅ SinaBox for Linux has been installed successfully!${RESET}"
echo -e "You can now run: ${CYAN}sinabox --help${RESET}"
echo -e "Or right-click any application in your Taskbar or App Menu to launch in SinaBox."
