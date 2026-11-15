#!/usr/bin/env python3
"""
SinaBox Desktop Actions Injector & Submenu Synchronizer
Dynamically reads all user custom profiles from ~/.local/share/sinabox/profiles/*.json
and updates .desktop files (App Menu, Taskbar/Dock) and Nautilus Scripts with cascading submenus.
"""

import os
import sys
import re
import stat
from pathlib import Path

HOME = Path.home()
USER_APPS = HOME / ".local" / "share" / "applications"
USER_APPS.mkdir(parents=True, exist_ok=True)
PROFILES_DIR = HOME / ".local" / "share" / "sinabox" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
NAUTILUS_SCRIPTS = HOME / ".local" / "share" / "nautilus" / "scripts"
NAUTILUS_SCRIPTS.mkdir(parents=True, exist_ok=True)
SINABOX_BIN = HOME / ".local" / "bin" / "sinabox"

SEARCH_DIRS = [
    Path("/usr/share/applications"),
    Path("/var/lib/flatpak/exports/share/applications"),
    HOME / ".local" / "share" / "flatpak" / "exports" / "share" / "applications",
]

def get_profiles():
    return sorted([f.stem for f in PROFILES_DIR.glob("*.json")])

def sync_nautilus_scripts(profiles):
    """
    In Nautilus/GNOME, a directory inside ~/.local/share/nautilus/scripts/
    renders as a native cascading flyout submenu (موس بره روش لیست باز میشه).
    """
    old_flat = NAUTILUS_SCRIPTS / "Open with Custom SinaBoxes"
    if old_flat.exists() and not old_flat.is_dir():
        old_flat.unlink()

    # 1. Main Action: Default Launch
    main_script = NAUTILUS_SCRIPTS / "Open with SinaBox (Default)"
    main_content = f"""#!/usr/bin/env bash
while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        {SINABOX_BIN} run "$file" &
    fi
done <<< "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
"""
    main_script.write_text(main_content, encoding="utf-8")
    main_script.chmod(main_script.stat().st_mode | stat.S_IEXEC)

    # 2. Spaces Action (Multi-Instance Accounts)
    space_script = NAUTILUS_SCRIPTS / "Open with SinaBox Space..."
    space_content = f"""#!/usr/bin/env bash
while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        python3 /home/sina/.gemini/antigravity/scratch/sinabox/space_gui.py "$file" &
    fi
done <<< "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
"""
    space_script.write_text(space_content, encoding="utf-8")
    space_script.chmod(space_script.stat().st_mode | stat.S_IEXEC)

    # 3. SinaBox Profiles Submenu Directory
    submenu_dir = NAUTILUS_SCRIPTS / "SinaBox Profiles"
    submenu_dir.mkdir(parents=True, exist_ok=True)

    # Clean old scripts inside submenu
    for item in submenu_dir.iterdir():
        if item.is_file():
            item.unlink()

    # Generate an individual script for each profile
    for p in profiles:
        script_file = submenu_dir / f"Run with profile [{p}]"
        content = f"""#!/usr/bin/env bash
while IFS= read -r file; do
    if [[ -n "$file" ]]; then
        {SINABOX_BIN} run --profile "{p}" "$file" &
    fi
done <<< "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"
"""
        script_file.write_text(content, encoding="utf-8")
        script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC)

    # Add GUI Profile Creator button at the bottom of the submenu
    add_script = submenu_dir / "➕ Create New Profile..."
    add_content = """#!/usr/bin/env bash
python3 /home/sina/.gemini/antigravity/scratch/sinabox/create_profile_gui.py &
"""
    add_script.write_text(add_content, encoding="utf-8")
    add_script.chmod(add_script.stat().st_mode | stat.S_IEXEC)

def patch_desktop_file(src_path: Path, profiles: list):
    try:
        content = src_path.read_text(encoding="utf-8")
    except Exception:
        return

    if "Type=Application" not in content or "NoDisplay=true" in content:
        return

    exec_match = re.search(r"^Exec=(.+)$", content, re.MULTILINE)
    if not exec_match:
        return
    orig_exec = exec_match.group(1).strip()

    if "sinabox" in orig_exec.lower():
        return

    raw_tokens = orig_exec.split()
    clean_binary = raw_tokens[0]
    field_args = [t for t in raw_tokens[1:] if t.startswith("%")]
    arg_suffix = (" " + " ".join(field_args)) if field_args else ""

    # Build Actions list
    actions_match = re.search(r"^Actions=(.*)$", content, re.MULTILINE)
    existing_actions = actions_match.group(1).strip() if actions_match else ""
    
    actions_list = [a.strip() for a in existing_actions.split(";") if a.strip() and not a.startswith("SinaBox_") and a not in ["OpenWithSinaBox", "OpenWithCustomSinaBox"]]
    
    # 1. Default Action
    actions_list.append("SinaBox_Default")
    # 2. Space Action (Multi-Instance)
    actions_list.append("SinaBox_Space")
    
    # 3. Custom Profiles Actions
    for p in profiles:
        clean_action_id = "SinaBox_Profile_" + re.sub(r"[^a-zA-Z0-9_]", "_", p)
        actions_list.append(clean_action_id)

    # 4. Create New Profile Action
    actions_list.append("SinaBox_Create_Profile")

    new_actions_line = f"Actions={';'.join(actions_list)};"

    # Strip existing [Desktop Action SinaBox...] blocks
    content = re.sub(r"\n\[Desktop Action (?:SinaBox_|OpenWithSinaBox).*?\][\s\S]*?(?=\n\[|\Z)", "", content)

    if actions_match:
        content = re.sub(r"^Actions=.*$", new_actions_line, content, flags=re.MULTILINE)
    else:
        content = re.sub(r"(\[Desktop Entry\][\s\S]*?)(?=\n\[|\Z)", r"\1" + f"{new_actions_line}\n", content, count=1)

    # Build Action definitions
    action_blocks = f"""
[Desktop Action SinaBox_Default]
Name=Open with SinaBox (Default)
Icon=security-high
Exec={SINABOX_BIN} run {clean_binary}{arg_suffix}

[Desktop Action SinaBox_Space]
Name=Open with SinaBox Space (Multi-Account)...
Icon=user-available
Exec=python3 /home/sina/.gemini/antigravity/scratch/sinabox/space_gui.py {clean_binary}{arg_suffix}
"""
    for p in profiles:
        clean_action_id = "SinaBox_Profile_" + re.sub(r"[^a-zA-Z0-9_]", "_", p)
        action_blocks += f"""
[Desktop Action {clean_action_id}]
Name=Open with SinaBox ➔ {p}
Icon=security-medium
Exec={SINABOX_BIN} run --profile "{p}" {clean_binary}{arg_suffix}
"""

    action_blocks += f"""
[Desktop Action SinaBox_Create_Profile]
Name=➕ Create New SinaBox Profile...
Icon=list-add
Exec=python3 /home/sina/.gemini/antigravity/scratch/sinabox/create_profile_gui.py
"""

    content = content.strip() + "\n" + action_blocks

    target_file = USER_APPS / src_path.name
    try:
        target_file.write_text(content, encoding="utf-8")
    except PermissionError:
        pass

def main():
    profiles = get_profiles()
    sync_nautilus_scripts(profiles)
    
    count = 0
    for d in SEARCH_DIRS:
        if d.exists():
            for f in d.glob("*.desktop"):
                patch_desktop_file(f, profiles)
                count += 1

    for f in list(USER_APPS.glob("*.desktop")):
        patch_desktop_file(f, profiles)

    os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
    print(f"✅ Synced {len(profiles)} profiles + Spaces across {count} desktop apps and file manager menus!")

if __name__ == "__main__":
    main()
