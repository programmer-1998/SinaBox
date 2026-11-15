#!/usr/bin/env python3
"""
SinaBox Transparent Shim Generator
Creates shims in ~/.local/share/sinabox/shims for system and flatpak apps.
When an app is run with --sinabox, it routes into SinaBox; otherwise runs normally.
"""

import os
import shutil
from pathlib import Path

SHIMS_DIR = Path.home() / ".local" / "share" / "sinabox" / "shims"
SHIMS_DIR.mkdir(parents=True, exist_ok=True)
SINABOX_BIN = Path.home() / ".local" / "bin" / "sinabox"

TARGET_APPS = [
    "code", "gimp", "telegram", "telegram-desktop", "discord", "google-chrome", "google-chrome-stable", "vlc", "spotify"
]

def create_shim(app_name):
    shim_file = SHIMS_DIR / app_name
    real_path = shutil.which(app_name)
    if not real_path or str(SHIMS_DIR) in real_path:
        # Check standard binary locations
        for p in [f"/usr/bin/{app_name}", f"/bin/{app_name}"]:
            if Path(p).exists():
                real_path = p
                break

    # If flatpak app exists
    is_flatpak = False
    flatpak_app_id = ""
    if app_name in ["telegram", "telegram-desktop"]:
        is_flatpak = True
        flatpak_app_id = "org.telegram.desktop"
    elif app_name == "discord":
        is_flatpak = True
        flatpak_app_id = "com.discordapp.Discord"
    elif app_name == "spotify":
        is_flatpak = True
        flatpak_app_id = "com.spotify.Client"

    if is_flatpak and shutil.which("flatpak"):
        content = f"""#!/usr/bin/env bash
# SinaBox Shim for {app_name} (Flatpak)

IS_SINABOX=false
CUSTOM_PROFILE=""
SPACE_NAME=""
CLEAN_ARGS=()

for arg in "$@"; do
    if [[ "$arg" == "--sinabox" || "$arg" == "--Sinabox" ]]; then
        IS_SINABOX=true
    elif [[ "$arg" =~ ^--space=.*$ ]]; then
        SPACE_NAME="${{arg#--space=}}"
    elif [[ "$arg" =~ ^--custom.*$ || "$arg" =~ ^--no-.*$ || "$arg" == "--test" || "$arg" == "--disposable" ]]; then
        CUSTOM_PROFILE="${{arg#--}}"
    else
        CLEAN_ARGS+=("$arg")
    fi
done

if [[ "$IS_SINABOX" == true ]]; then
    EXTRA_FLAGS=()
    if [[ -n "$SPACE_NAME" ]]; then
        EXTRA_FLAGS+=("--space" "$SPACE_NAME")
    fi
    if [[ -n "$CUSTOM_PROFILE" ]]; then
        EXTRA_FLAGS+=("--profile" "$CUSTOM_PROFILE")
    fi
    exec {SINABOX_BIN} run "${{EXTRA_FLAGS[@]}}" flatpak run {flatpak_app_id} "${{CLEAN_ARGS[@]}}"
else
    exec flatpak run {flatpak_app_id} "$@"
fi
"""
    elif real_path:
        content = f"""#!/usr/bin/env bash
# SinaBox Shim for {app_name} (Binary: {real_path})

IS_SINABOX=false
CUSTOM_PROFILE=""
SPACE_NAME=""
CLEAN_ARGS=()

for arg in "$@"; do
    if [[ "$arg" == "--sinabox" || "$arg" == "--Sinabox" ]]; then
        IS_SINABOX=true
    elif [[ "$arg" =~ ^--space=.*$ ]]; then
        SPACE_NAME="${{arg#--space=}}"
    elif [[ "$arg" =~ ^--custom.*$ || "$arg" =~ ^--no-.*$ || "$arg" == "--test" || "$arg" == "--disposable" ]]; then
        CUSTOM_PROFILE="${{arg#--}}"
    else
        CLEAN_ARGS+=("$arg")
    fi
done

if [[ "$IS_SINABOX" == true ]]; then
    EXTRA_FLAGS=()
    if [[ -n "$SPACE_NAME" ]]; then
        EXTRA_FLAGS+=("--space" "$SPACE_NAME")
    fi
    if [[ -n "$CUSTOM_PROFILE" ]]; then
        EXTRA_FLAGS+=("--profile" "$CUSTOM_PROFILE")
    fi
    exec {SINABOX_BIN} run "${{EXTRA_FLAGS[@]}}" "{real_path}" "${{CLEAN_ARGS[@]}}"
else
    exec "{real_path}" "$@"
fi
"""
    else:
        return

    shim_file.write_text(content)
    shim_file.chmod(0o755)

for a in TARGET_APPS:
    create_shim(a)

print(f"✔ Generated transparent shims in {SHIMS_DIR}")
