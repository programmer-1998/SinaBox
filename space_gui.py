#!/usr/bin/env python3
"""
SinaBox Space Manager GUI
Allows creating and launching isolated multi-instance spaces (e.g. whatsapp2, telegram_work)
"""

import sys
import subprocess
import shutil
from pathlib import Path

SINABOX_BIN = Path.home() / ".local" / "bin" / "sinabox"
SPACES_DIR = Path.home() / ".local" / "share" / "sinabox" / "spaces"
SPACES_DIR.mkdir(parents=True, exist_ok=True)

def run_space_gui():
    target_app = sys.argv[1] if len(sys.argv) > 1 else ""

    if not shutil.which("zenity"):
        print("zenity is required for Space GUI", file=sys.stderr)
        sys.exit(1)

    existing_spaces = sorted([f.name for f in SPACES_DIR.iterdir() if f.is_dir()])
    
    # Prompt: Choose an existing space or create new
    options = ["➕ Create New Space..."] + existing_spaces
    
    cmd = [
        "zenity", "--list",
        "--title=SinaBox Spaces (Multi-Instance)",
        "--text=Select a Space to launch or create a new one:",
        "--column=Available Spaces",
    ] + options

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(0)

    chosen = res.stdout.strip()
    if not chosen:
        sys.exit(0)

    if chosen == "➕ Create New Space...":
        name_res = subprocess.run([
            "zenity", "--entry",
            "--title=SinaBox - Create New Space",
            "--text=Enter Space name (e.g. account2, work, personal):",
        ], capture_output=True, text=True)
        if name_res.returncode != 0:
            sys.exit(0)
        space_name = name_res.stdout.strip()
        if not space_name or space_name.startswith("-"):
            subprocess.run(["zenity", "--error", "--text=Invalid space name!"])
            sys.exit(1)
        (SPACES_DIR / space_name).mkdir(parents=True, exist_ok=True)
        chosen = space_name

    # Launch app in chosen space
    if target_app:
        subprocess.Popen([str(SINABOX_BIN), "run", "--space", chosen, target_app])
    else:
        subprocess.run(["zenity", "--info", "--text=Space '" + chosen + "' ready! Use: sinabox run --space " + chosen + " <app>"])

if __name__ == "__main__":
    run_space_gui()
