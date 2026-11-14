#!/usr/bin/env python3
"""
SinaBox Desktop & Context Menu Integrator
Installs:
1. "Open with SinaBox" in Nautilus / Dolphin / Thunar
2. "Open with Custom SinaBoxes" submenu / dynamic selector
3. Flag Interception shims for CLI (<app> --sinabox --custom01)
4. Desktop Notification VPN status monitor
"""

import sys
import os
import stat
from pathlib import Path

HOME = Path.home()
BIN_DIR = HOME / ".local" / "bin"
SHIMS_DIR = HOME / ".local" / "share" / "sinabox" / "shims"
NAUTILUS_SCRIPTS = HOME / ".local" / "share" / "nautilus" / "scripts"
DOLPHIN_SERVICES = HOME / ".local" / "share" / "kio" / "servicemenus"
XFCE_UCA = HOME / ".config" / "Thunar" / "uca.xml"
APPLICATIONS_DIR = HOME / ".local" / "share" / "applications"

for d in [BIN_DIR, SHIMS_DIR, NAUTILUS_SCRIPTS, DOLPHIN_SERVICES, APPLICATIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SINABOX_BIN = BIN_DIR / "sinabox"

def install_cli_symlink():
    script_source = Path("/home/sina/.gemini/antigravity/scratch/sinabox/sinabox.py")
    if SINABOX_BIN.exists() or SINABOX_BIN.is_symlink():
        SINABOX_BIN.unlink()
    SINABOX_BIN.symlink_to(script_source)
    print(f"✔ Linked CLI binary: {SINABOX_BIN}")

def install_nautilus():
    # 1. Main Action: Open with SinaBox
    script_main = NAUTILUS_SCRIPTS / "Open with SinaBox"
    content_main = f"""#!/usr/bin/env bash
while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        {SINABOX_BIN} run "$file" &
    fi
done <<< "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
"""
    with open(script_main, "w") as f:
        f.write(content_main)
    script_main.chmod(script_main.stat().st_mode | stat.S_IEXEC)

    # 2. Custom Profiles Action
    script_custom = NAUTILUS_SCRIPTS / "Open with Custom SinaBoxes"
    content_custom = f"""#!/usr/bin/env bash
PROFILES_DIR="$HOME/.local/share/sinabox/profiles"
mkdir -p "$PROFILES_DIR"

PROFILES=$(find "$PROFILES_DIR" -name "*.json" -exec basename {{}} .json \;)

if [[ -z "$PROFILES" ]]; then
    zenity --info --title="SinaBox" --text="No custom profiles found.\\nCreate one using:\\nsinabox profile create <name> [flags]" 2>/dev/null || \\
    notify-send "SinaBox" "No custom profiles found. Create one with: sinabox profile create <name>"
    exit 0
fi

CHOSEN=$(zenity --list --title="SinaBox - Choose Custom Profile" --column="Available Profiles" $PROFILES 2>/dev/null)

if [[ -n "$CHOSEN" ]]; then
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            {SINABOX_BIN} run --profile "$CHOSEN" "$file" &
        fi
    done <<< "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
fi
"""
    with open(script_custom, "w") as f:
        f.write(content_custom)
    script_custom.chmod(script_custom.stat().st_mode | stat.S_IEXEC)
    print("✔ Installed Nautilus context menu actions.")

def install_dolphin():
    service_file = DOLPHIN_SERVICES / "sinabox.desktop"
    content = f"""[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=application/x-executable;application/x-shellscript;application/vnd.appimage;application/x-desktop;
Actions=OpenWithSinaBox;OpenWithCustomSinaBox;

[Desktop Action OpenWithSinaBox]
Name=Open with SinaBox
Icon=security-high
Exec={SINABOX_BIN} run %f

[Desktop Action OpenWithCustomSinaBox]
Name=Open with Custom SinaBoxes...
Icon=security-medium
Exec={NAUTILUS_SCRIPTS}/"Open with Custom SinaBoxes"
"""
    with open(service_file, "w") as f:
        f.write(content)
    print("✔ Installed Dolphin (KDE) context menu action.")

def install_shim_wrapper(app_name="telegram-desktop"):
    shim_file = SHIMS_DIR / app_name
    real_path = shutil_which(app_name) or f"/usr/bin/{app_name}"

    content = f"""#!/usr/bin/env bash
# SinaBox Flag Interception Shim for {app_name}

IS_SINABOX=false
CUSTOM_PROFILE=""
CLEAN_ARGS=()

for arg in "$@"; do
    if [[ "$arg" == "--sinabox" || "$arg" == "--Sinabox" ]]; then
        IS_SINABOX=true
    elif [[ "$arg" =~ ^--custom[0-9a-zA-Z_-]+$ ]]; then
        CUSTOM_PROFILE="${{arg#--}}"
    else
        CLEAN_ARGS+=("$arg")
    fi
done

if [[ "$IS_SINABOX" == true ]]; then
    if [[ -n "$CUSTOM_PROFILE" ]]; then
        exec {SINABOX_BIN} run --profile "$CUSTOM_PROFILE" "{real_path}" "${{CLEAN_ARGS[@]}}"
    else
        exec {SINABOX_BIN} run "{real_path}" "${{CLEAN_ARGS[@]}}"
    fi
else
    exec "{real_path}" "$@"
fi
"""
    with open(shim_file, "w") as f:
        f.write(content)
    shim_file.chmod(shim_file.stat().st_mode | stat.S_IEXEC)
    print(f"✔ Generated flag shim: {shim_file}")

def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)

def main():
    install_cli_symlink()
    install_nautilus()
    install_dolphin()
    install_shim_wrapper("telegram-desktop")
    install_shim_wrapper("google-chrome")
    install_shim_wrapper("google-chrome-stable")
    install_shim_wrapper("discord")
    print("\n✅ SinaBox Desktop & Context Menu Integration Complete!")

if __name__ == "__main__":
    main()
