#!/usr/bin/env python3
"""
SinaBox Flatpak Orchestrator
Handles Flatpak apps (like Telegram, Discord, Spotify) by orchestrating Flatpak overrides & environments
seamlessly within SinaBox.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_flatpak_app(app_id: str, app_args: list, options: dict):
    # 1. Geo & Timezone
    sys.path.insert(0, "/home/sina/.gemini/antigravity/scratch/sinabox")
    from sinabox import GeoManager, HardwareManager, UI, BOXES_DIR

    geo = GeoManager.get_geo()
    tz = geo["timezone"]

    # 2. Storage / Space / Profile
    space_name = options.get("space")
    profile_name = options.get("profile")

    cmd = ["flatpak", "run"]

    # Handle Space
    extra_app_args = list(app_args)
    if space_name:
        space_dir = Path.home() / ".local" / "share" / "sinabox" / "spaces" / space_name / app_id
        space_dir.mkdir(parents=True, exist_ok=True)
        cmd.extend([
            f"--filesystem={space_dir}"
        ])
        if "telegram" in app_id.lower():
            # Telegram uses -workdir for completely isolated session/account
            tg_data = space_dir / "tdata"
            tg_data.mkdir(parents=True, exist_ok=True)
            extra_app_args.extend(["-workdir", str(space_dir)])
        else:
            cmd.append(f"--env=XDG_DATA_HOME={space_dir}")
        UI.info(f"Using isolated Flatpak Space '{space_name}': {space_dir}")

    # Timezone & Locale env
    cmd.extend([
        f"--env=TZ={tz}",
        f"--env=LANG={geo['locale']}",
        f"--env=LC_ALL={geo['locale']}"
    ])

    # Killswitches
    if options.get("no_net"):
        cmd.append("--unshare=network")
        UI.warn("Network Access Blocked: Flatpak network unshared.")
    if options.get("no_cam"):
        cmd.append("--nosocket=fallback-x11")
    if options.get("no_gpu"):
        cmd.extend([
            "--env=LIBGL_ALWAYS_SOFTWARE=1",
            "--env=GALLIUM_DRIVER=llvmpipe"
        ])

    cmd.append(app_id)
    cmd.extend(extra_app_args)

    UI.success(f"Launching Flatpak {app_id} | City: {geo['city']} ({geo['country']}) | TZ: {tz}")
    res = subprocess.run(cmd)
    sys.exit(res.returncode)

if __name__ == "__main__":
    pass
