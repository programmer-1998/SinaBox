#!/usr/bin/env python3
"""
SinaBox Desktop Actions Injector
Patches user and system .desktop files to add:
- "Open with SinaBox"
- "Open with Custom SinaBoxes"
directly to App Menu, Taskbar/Dock, Desktop shortcuts, and File Manager context menus!
"""

import os
import sys
import re
from pathlib import Path

HOME = Path.home()
USER_APPS = HOME / ".local" / "share" / "applications"
USER_APPS.mkdir(parents=True, exist_ok=True)

SEARCH_DIRS = [
    Path("/usr/share/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
    HOME / ".local" / "share" / "flatpak" / "exports" / "share" / "applications",
]

HELPER_CUSTOM = HOME / ".local" / "share" / "sinabox" / "sinabox_gui_picker.sh"

def create_gui_picker():
    HELPER_CUSTOM.parent.mkdir(parents=True, exist_ok=True)
    content = """#!/usr/bin/env bash
PROFILES_DIR="$HOME/.local/share/sinabox/profiles"
mkdir -p "$PROFILES_DIR"

PROFILES=$(find "$PROFILES_DIR" -name "*.json" -exec basename {} .json \\;)

if [[ -z "$PROFILES" ]]; then
    zenity --info --title="SinaBox" --text="No custom profiles found.\\nCreate one using:\\nsinabox profile create <name> [flags]" 2>/dev/null || \\
    notify-send "SinaBox" "No custom profiles found. Create one with: sinabox profile create <name>"
    exit 0
fi

CHOSEN=$(zenity --list --title="SinaBox - Choose Custom Profile" --column="Available Profiles" $PROFILES 2>/dev/null)

if [[ -n "$CHOSEN" ]]; then
    sinabox run --profile "$CHOSEN" "$@" &
fi
"""
    with open(HELPER_CUSTOM, "w") as f:
        f.write(content)
    HELPER_CUSTOM.chmod(0o755)

def patch_desktop_file(src_path: Path):
    try:
        content = src_path.read_text(encoding="utf-8")
    except Exception:
        return

    # Check if it is a normal application
    if "Type=Application" not in content or "NoDisplay=true" in content:
        return

    # Extract original Exec command
    exec_match = re.search(r"^Exec=(.+)$", content, re.MULTILINE)
    if not exec_match:
        return
    orig_exec = exec_match.group(1).strip()

    # Don't patch sinabox itself
    if "sinabox" in orig_exec.lower():
        return

    # Extract target binary without flags for clean invocation
    raw_tokens = orig_exec.split()
    clean_binary = raw_tokens[0]
    field_args = [t for t in raw_tokens[1:] if t.startswith("%")]
    arg_suffix = (" " + " ".join(field_args)) if field_args else ""

    # Parse existing Actions
    actions_match = re.search(r"^Actions=(.*)$", content, re.MULTILINE)
    existing_actions = actions_match.group(1).strip() if actions_match else ""
    
    actions_list = [a.strip() for a in existing_actions.split(";") if a.strip()]
    
    if "OpenWithSinaBox" not in actions_list:
        actions_list.append("OpenWithSinaBox")
    if "OpenWithCustomSinaBox" not in actions_list:
        actions_list.append("OpenWithCustomSinaBox")

    new_actions_line = f"Actions={';'.join(actions_list)};"

    if actions_match:
        content = re.sub(r"^Actions=.*$", new_actions_line, content, flags=re.MULTILINE)
    else:
        content = re.sub(r"(\[Desktop Entry\][\s\S]*?)(?=\n\[|\Z)", r"\1" + f"{new_actions_line}\n", content, count=1)

    # Append Action definitions if missing
    if "[Desktop Action OpenWithSinaBox]" not in content:
        action_blocks = f"""
[Desktop Action OpenWithSinaBox]
Name=Open with SinaBox
Icon=security-high
Exec=sinabox run {clean_binary}{arg_suffix}

[Desktop Action OpenWithCustomSinaBox]
Name=Open with Custom SinaBoxes...
Icon=security-medium
Exec={HELPER_CUSTOM} {clean_binary}{arg_suffix}
"""
        content = content.strip() + "\n" + action_blocks

    target_file = USER_APPS / src_path.name
    try:
        target_file.write_text(content, encoding="utf-8")
    except PermissionError:
        pass

def main():
    create_gui_picker()
    count = 0
    for d in SEARCH_DIRS:
        if d.exists():
            for f in d.glob("*.desktop"):
                patch_desktop_file(f)
                count += 1

    # Also patch any existing writable files in ~/.local/share/applications
    for f in list(USER_APPS.glob("*.desktop")):
        patch_desktop_file(f)

    # Update desktop database
    os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
    print(f"✅ Successfully injected SinaBox actions into {count} applications!")
    print("Now right-clicking any app icon in the Taskbar, Dock, App Menu, or Desktop will show:")
    print("  ⭐ Open with SinaBox")
    print("  ⭐ Open with Custom SinaBoxes...")

if __name__ == "__main__":
    main()
