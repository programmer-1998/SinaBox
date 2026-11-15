#!/usr/bin/env python3
"""
SinaBox GUI Profile Creator
Allows users to visually create custom profiles with toggles for all permissions.
"""

import sys
import subprocess
import shutil
from pathlib import Path

SINABOX_BIN = Path.home() / ".local" / "bin" / "sinabox"

def run_gui():
    if not shutil.which("zenity"):
        print("zenity is required for GUI creation", file=sys.stderr)
        sys.exit(1)

    # 1. Ask for Profile Name
    res = subprocess.run([
        "zenity", "--entry",
        "--title=SinaBox - Create New Profile",
        "--text=Enter a unique name for this profile (e.g. secure01, work, gaming):",
    ], capture_output=True, text=True)

    if res.returncode != 0:
        sys.exit(0)

    name = res.stdout.strip()
    if not name or name.startswith("-"):
        subprocess.run([
            "zenity", "--error",
            "--title=SinaBox Error",
            "--text=Invalid profile name! It cannot be empty or start with '-'.",
        ])
        sys.exit(1)

    # 2. Checklist for permissions & settings
    list_res = subprocess.run([
        "zenity", "--list", "--checklist",
        "--title=SinaBox - Select Security Flags",
        "--text=Check the restrictions you want to apply to profile [" + name + "]:",
        "--column=Enable", "--column=Flag", "--column=Description",
        "FALSE", "--no-mic", "Block & mute microphone recording",
        "FALSE", "--no-cam", "Hide all webcam/video devices (/dev/video*)",
        "FALSE", "--no-gpu", "Disable GPU acceleration (force software rendering)",
        "FALSE", "--no-net", "Completely cut off network connection",
        "FALSE", "--no-loc", "Block GeoClue location services",
        "FALSE", "--no-storage", "Prevent access to host storage ($HOME)",
        "FALSE", "--disposable", "Run 100% in temporary RAM (zero trace upon exit)",
    ], capture_output=True, text=True)

    if list_res.returncode != 0:
        sys.exit(0)

    selected = [x.strip() for x in list_res.stdout.strip().split("|") if x.strip()]

    cmd = [str(SINABOX_BIN), "profile", "create", name] + selected
    create_res = subprocess.run(cmd, capture_output=True, text=True)

    if create_res.returncode == 0:
        subprocess.run([
            "zenity", "--info",
            "--title=SinaBox - Success",
            "--text=Profile '" + name + "' created successfully!\nIt is now accessible in the terminal and context menus.",
        ])
    else:
        err_msg = create_res.stderr or create_res.stdout or "Failed to create profile"
        subprocess.run([
            "zenity", "--error",
            "--title=SinaBox Error",
            "--text=" + err_msg,
        ])

if __name__ == "__main__":
    run_gui()
