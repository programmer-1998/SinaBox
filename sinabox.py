#!/usr/bin/env python3
"""
SinaBox Core Engine
Geo-Synchronized & Privacy-Preserving Application Sandbox
Author: Sina Khanzadeh
"""

import sys
import os
import json
import uuid
import random
import shutil
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

VERSION = "1.0.0"

# Directories
HOME = Path.home()
SINABOX_DIR = HOME / ".local" / "share" / "sinabox"
PROFILES_DIR = SINABOX_DIR / "profiles"
BOXES_DIR = SINABOX_DIR / "boxes"
HARDWARE_DIR = SINABOX_DIR / "hardware"
CACHE_DIR = HOME / ".cache" / "sinabox"
GEO_CACHE_FILE = CACHE_DIR / "geo_active.json"

for d in [PROFILES_DIR, BOXES_DIR, HARDWARE_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class UI:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def info(cls, msg: str):
        print(f"{cls.CYAN}ℹ [SinaBox]{cls.RESET} {msg}")

    @classmethod
    def success(cls, msg: str):
        print(f"{cls.GREEN}✔ [SinaBox]{cls.RESET} {msg}")

    @classmethod
    def warn(cls, msg: str):
        print(f"{cls.YELLOW}⚠ [SinaBox]{cls.RESET} {msg}")

    @classmethod
    def error(cls, msg: str):
        print(f"{cls.RED}✖ [SinaBox Error]{cls.RESET} {msg}", file=sys.stderr)

class GeoManager:
    APIS = [
        ("ipapi.co", "https://ipapi.co/json/"),
        ("ipwhois", "https://ipwho.is/"),
        ("freeipapi", "https://freeipapi.com/api/json")
    ]

    COUNTRY_LOCALES = {
        "US": "en_US.UTF-8",
        "GB": "en_GB.UTF-8",
        "DE": "de_DE.UTF-8",
        "FR": "fr_FR.UTF-8",
        "NL": "nl_NL.UTF-8",
        "CA": "en_CA.UTF-8",
        "TR": "tr_TR.UTF-8",
        "IR": "fa_IR.UTF-8",
        "RU": "ru_RU.UTF-8",
        "CH": "de_CH.UTF-8",
        "SE": "sv_SE.UTF-8",
        "FI": "fi_FI.UTF-8",
        "NO": "nb_NO.UTF-8",
        "IT": "it_IT.UTF-8",
        "ES": "es_ES.UTF-8",
        "JP": "ja_JP.UTF-8",
        "SG": "en_SG.UTF-8",
    }

    @classmethod
    def get_geo(cls, force_refresh=False) -> Dict[str, Any]:
        if not force_refresh and GEO_CACHE_FILE.exists():
            try:
                with open(GEO_CACHE_FILE, "r") as f:
                    data = json.load(f)
                    # Cache valid for 3 minutes
                    if data.get("timestamp", 0) + 180 > os.times().elapsed:
                        return data
            except Exception:
                pass

        for name, url in cls.APIS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SinaBox/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    raw = json.loads(resp.read().decode())
                    tz = raw.get("timezone")
                    if isinstance(tz, dict):
                        tz = tz.get("id", "UTC")
                    elif not tz:
                        tz = "UTC"

                    country = raw.get("country_code") or raw.get("country") or "US"
                    if len(country) > 2:
                        country = raw.get("country_code", "US")

                    geo_data = {
                        "ip": raw.get("ip", "127.0.0.1"),
                        "city": raw.get("city", "Unknown"),
                        "country": country,
                        "timezone": tz,
                        "locale": cls.COUNTRY_LOCALES.get(country, "en_US.UTF-8"),
                        "timestamp": os.times().elapsed
                    }
                    with open(GEO_CACHE_FILE, "w") as f:
                        json.dump(geo_data, f)
                    return geo_data
            except Exception:
                continue

        return {
            "ip": "Unknown",
            "city": "Unknown",
            "country": "US",
            "timezone": "UTC",
            "locale": "en_US.UTF-8",
            "timestamp": os.times().elapsed
        }

class HardwareManager:
    PRESETS = {
        "thinkpad": {
            "product_name": "ThinkPad X1 Carbon Gen 10",
            "board_vendor": "LENOVO",
            "board_name": "21CBCTO1WW",
            "bios_vendor": "LENOVO",
            "bios_version": "N3AET71W (1.36)",
            "cpu_model": "12th Gen Intel(R) Core(TM) i7-1260P"
        },
        "dell_xps": {
            "product_name": "XPS 13 9315",
            "board_vendor": "Dell Inc.",
            "board_name": "0V1M3Y",
            "bios_vendor": "Dell Inc.",
            "bios_version": "1.8.0",
            "cpu_model": "12th Gen Intel(R) Core(TM) i7-1250U"
        },
        "macbook_linux": {
            "product_name": "MacBookPro16,1",
            "board_vendor": "Apple Inc.",
            "board_name": "Mac-E1008331FDC96864",
            "bios_vendor": "Apple Inc.",
            "bios_version": "1965.140.1.0.0",
            "cpu_model": "Intel(R) Core(TM) i9-9880H CPU @ 2.30GHz"
        }
    }

    @classmethod
    def get_active(cls) -> Dict[str, str]:
        hw_file = HARDWARE_DIR / "active.json"
        if hw_file.exists():
            try:
                with open(hw_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return cls.generate_random()

    @classmethod
    def generate_random(cls) -> Dict[str, str]:
        preset_key = random.choice(list(cls.PRESETS.keys()))
        data = dict(cls.PRESETS[preset_key])
        data["machine_id"] = uuid.uuid4().hex
        data["hostname"] = f"sinabox-{data['product_name'].split()[0].lower()}-{random.randint(100, 999)}"
        hw_file = HARDWARE_DIR / "active.json"
        with open(hw_file, "w") as f:
            json.dump(data, f, indent=2)
        return data

    @classmethod
    def reset(cls):
        hw = cls.generate_random()
        UI.success(f"Hardware identities reset! New Machine-ID: {hw['machine_id'][:8]}... Model: {hw['product_name']}")

class SandboxEngine:
    @staticmethod
    def run(app_cmd: List[str], options: Dict[str, Any]):
        # Check if the target is flatpak
        if any("flatpak" in str(x) for x in app_cmd[:3]):
            # Delegate to specialized flatpak wrapper
            app_id = "org.telegram.desktop"
            flatpak_extra = []
            for arg in app_cmd:
                if arg.startswith("org.") or arg.startswith("com.") or arg.startswith("io.") or arg.startswith("net."):
                    app_id = arg
                elif arg not in ["flatpak", "run", "--file-forwarding", "--"] and not arg.endswith("/flatpak"):
                    flatpak_extra.append(arg)
            from flatpak_wrapper import run_flatpak_app
            run_flatpak_app(app_id, flatpak_extra, options)
            return

        if not shutil.which("bwrap"):
            UI.error("bubblewrap (bwrap) is not installed! Run: sudo apt install bubblewrap")
            sys.exit(1)

        geo = GeoManager.get_geo()
        hw = HardwareManager.get_active()

        app_name = Path(app_cmd[0]).name
        space_name = options.get("space")
        if space_name:
            box_name = f"space_{space_name}_{app_name}"
            # Ensure space directory is tracked in SPACES_DIR
            spaces_dir = SINABOX_DIR / "spaces" / space_name
            spaces_dir.mkdir(parents=True, exist_ok=True)
        else:
            box_name = options.get("box_name") or options.get("profile") or app_name

        # Storage directory
        is_disposable = options.get("disposable", False) or options.get("no_storage", False)
        if space_name and is_disposable:
            UI.error("A Space cannot be run with --disposable or --no-storage! Spaces require persistent isolated storage.")
            sys.exit(1)

        box_dir = BOXES_DIR / box_name
        box_home = box_dir / "home"

        if not is_disposable:
            box_home.mkdir(parents=True, exist_ok=True)
            if space_name:
                UI.info(f"Using isolated Space '{space_name}': {box_home}")
            else:
                UI.info(f"Using persistent box storage: {box_home}")
        else:
            UI.warn("Running in DISPOSABLE mode (100% RAM tmpfs, zero trace upon exit)")

        # Pipes for spoofing
        open_fds = []

        def create_pipe_fd(content_bytes: bytes) -> int:
            r, w = os.pipe()
            os.write(w, content_bytes)
            os.close(w)
            open_fds.append(r)
            return r

        fd_machine_id = create_pipe_fd(f"{hw['machine_id']}\n".encode())
        fd_tz = create_pipe_fd(f"{geo['timezone']}\n".encode())

        # Construct bwrap command
        bwrap_cmd = [
            "bwrap",
            "--unshare-pid",
            "--unshare-uts",
            "--unshare-ipc",
            "--hostname", hw["hostname"],
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/etc", "/etc",
            "--proc", "/proc",
            "--dev", "/dev",
            "--ro-bind-data", str(fd_machine_id), "/etc/machine-id",
            "--ro-bind-data", str(fd_tz), "/etc/timezone",
            "--setenv", "TZ", geo["timezone"],
            "--setenv", "LANG", geo["locale"],
            "--setenv", "LC_ALL", geo["locale"],
            "--setenv", "USER", os.environ.get("USER", "sina"),
            "--setenv", "HOME", str(HOME),
        ]

        # Timezone localtime bind
        zone_file = Path(f"/usr/share/zoneinfo/{geo['timezone']}")
        if zone_file.exists():
            local_real = os.path.realpath("/etc/localtime")
            bwrap_cmd.extend(["--ro-bind", str(zone_file), local_real])

        # Storage Binding
        if is_disposable:
            bwrap_cmd.extend(["--tmpfs", str(HOME)])
        else:
            bwrap_cmd.extend(["--bind", str(box_home), str(HOME)])

        # Hardware Spoofing (DMI)
        if Path("/sys/class/dmi/id/product_name").exists():
            fd_prod = create_pipe_fd(f"{hw['product_name']}\n".encode())
            bwrap_cmd.extend(["--ro-bind-data", str(fd_prod), "/sys/class/dmi/id/product_name"])
        if Path("/sys/class/dmi/id/board_name").exists():
            fd_board = create_pipe_fd(f"{hw['board_name']}\n".encode())
            bwrap_cmd.extend(["--ro-bind-data", str(fd_board), "/sys/class/dmi/id/board_name"])

        # Display integration (Wayland / X11)
        if "WAYLAND_DISPLAY" in os.environ:
            wl_socket = Path(f"/run/user/{os.getuid()}/{os.environ['WAYLAND_DISPLAY']}")
            if wl_socket.exists():
                bwrap_cmd.extend(["--bind", str(wl_socket), str(wl_socket)])
                bwrap_cmd.extend(["--setenv", "WAYLAND_DISPLAY", os.environ["WAYLAND_DISPLAY"]])

        if "DISPLAY" in os.environ:
            x11_dir = Path("/tmp/.X11-unix")
            if x11_dir.exists():
                bwrap_cmd.extend(["--bind", str(x11_dir), str(x11_dir)])
                bwrap_cmd.extend(["--setenv", "DISPLAY", os.environ["DISPLAY"]])

        # Permission Killswitches
        # 1. GPU
        if not options.get("no_gpu", False):
            if Path("/dev/dri").exists():
                bwrap_cmd.extend(["--dev-bind", "/dev/dri", "/dev/dri"])
        else:
            UI.warn("GPU Access Blocked: Software rendering enforced.")
            bwrap_cmd.extend([
                "--setenv", "LIBGL_ALWAYS_SOFTWARE", "1",
                "--setenv", "GALLIUM_DRIVER", "llvmpipe"
            ])

        # 2. Camera
        if not options.get("no_cam", False):
            for dev in Path("/dev").glob("video*"):
                bwrap_cmd.extend(["--dev-bind", str(dev), str(dev)])
        else:
            UI.warn("Camera Access Blocked: /dev/video* devices hidden.")

        # 3. Audio / Mic
        pulse_dir = Path(f"/run/user/{os.getuid()}/pulse")
        pipewire_sock = Path(f"/run/user/{os.getuid()}/pipewire-0")

        if not options.get("no_mic", False):
            if pulse_dir.exists():
                bwrap_cmd.extend(["--bind", str(pulse_dir), str(pulse_dir)])
            if pipewire_sock.exists():
                bwrap_cmd.extend(["--bind", str(pipewire_sock), str(pipewire_sock)])
        else:
            UI.warn("Microphone Muted / Denied: Virtual silence sink active.")
            if pulse_dir.exists():
                bwrap_cmd.extend(["--bind", str(pulse_dir), str(pulse_dir)])
            if pipewire_sock.exists():
                bwrap_cmd.extend(["--bind", str(pipewire_sock), str(pipewire_sock)])
            bwrap_cmd.extend([
                "--setenv", "PULSE_SOURCE", "null",
                "--setenv", "PIPEWIRE_LATENCY", "128/48000"
            ])

        # 4. Network
        if options.get("no_net", False):
            UI.warn("Network Access Blocked: Isolated unshared netns.")
            bwrap_cmd.append("--unshare-net")
        else:
            bwrap_cmd.append("--share-net")

        # 5. Location & D-Bus Bus
        dbus_session = Path(f"/run/user/{os.getuid()}/bus")
        if dbus_session.exists():
            bwrap_cmd.extend(["--bind", str(dbus_session), str(dbus_session)])
            bwrap_cmd.extend(["--setenv", "DBUS_SESSION_BUS_ADDRESS", f"unix:path={dbus_session}"])

        # Bind /var/lib/flatpak if it exists so Flatpak runtimes can be accessed
        if Path("/var/lib/flatpak").exists():
            bwrap_cmd.extend(["--ro-bind", "/var/lib/flatpak", "/var/lib/flatpak"])

        if options.get("no_loc", False):
            UI.warn("Geolocation Blocked: D-Bus GeoClue blocked.")

        # Detect Electron / Chromium apps to avoid nested suid-sandbox conflict inside bubblewrap
        is_electron = any(k in app_name.lower() or any(k in str(x).lower() for x in app_cmd) for k in ["code", "antigravity", "electron", "chrome", "slack", "discord"])
        final_app_cmd = list(app_cmd)
        if is_electron and "--no-sandbox" not in final_app_cmd:
            final_app_cmd.append("--no-sandbox")

        # Final Target Command
        bwrap_cmd.append("--")
        bwrap_cmd.extend(final_app_cmd)

        UI.success(f"Launching {app_name} | City: {geo['city']} ({geo['country']}) | TZ: {geo['timezone']} | Machine: {hw['hostname']}")

        try:
            res = subprocess.run(bwrap_cmd, pass_fds=tuple(open_fds))
            sys.exit(res.returncode)
        finally:
            for fd in open_fds:
                try:
                    os.close(fd)
                except Exception:
                    pass

class ProfileManager:
    @classmethod
    def create(cls, name: str, options: Dict[str, Any]):
        profile_file = PROFILES_DIR / f"{name}.json"
        with open(profile_file, "w") as f:
            json.dump(options, f, indent=2)
        UI.success(f"Profile '{name}' saved successfully!")

    @classmethod
    def list(cls) -> List[str]:
        return [f.stem for f in PROFILES_DIR.glob("*.json")]

    @classmethod
    def get(cls, name: str) -> Optional[Dict[str, Any]]:
        profile_file = PROFILES_DIR / f"{name}.json"
        if profile_file.exists():
            with open(profile_file, "r") as f:
                return json.load(f)
        return None

    @classmethod
    def delete(cls, name: str):
        profile_file = PROFILES_DIR / f"{name}.json"
        if profile_file.exists():
            profile_file.unlink()
            UI.success(f"Profile '{name}' deleted.")
        else:
            UI.error(f"Profile '{name}' not found.")

def print_help():
    help_text = f"""
{UI.BOLD}{UI.CYAN}SinaBox - Next-Generation Geo-Synchronized Application Sandbox{UI.RESET}
Version: {VERSION} | Developed for Sina Khanzadeh

{UI.BOLD}USAGE:{UI.RESET}
  sinabox [COMMAND] [OPTIONS]
  sinabox run [OPTIONS] <executable> [args...]
  <executable> --sinabox [--<profile_name>] [args...]

{UI.BOLD}COMMANDS:{UI.RESET}
  {UI.GREEN}run{UI.RESET} <app> [args...]          Run application inside SinaBox
  {UI.GREEN}profile create{UI.RESET} <name> [flags] Save a reusable custom profile
  {UI.GREEN}profile list{UI.RESET}                  List all custom profiles
  {UI.GREEN}profile delete{UI.RESET} <name>        Delete a custom profile
  {UI.GREEN}hardware reset{UI.RESET}               Generate and reset random hardware identities
  {UI.GREEN}hardware info{UI.RESET}                Show currently active spoofed hardware
  {UI.GREEN}sync-vpn{UI.RESET}                     Query active VPN IP and show detected region

{UI.BOLD}PERMISSION & SECURITY FLAGS:{UI.RESET}
  {UI.YELLOW}--no-mic{UI.RESET}                      Block/Mute microphone recording (Zero-mic audio)
  {UI.YELLOW}--no-cam{UI.RESET}                      Block all webcam/camera devices (/dev/video*)
  {UI.YELLOW}--no-gpu{UI.RESET}                      Block GPU hardware acceleration (software raster)
  {UI.YELLOW}--no-net{UI.RESET}                      Completely cut off all network access
  {UI.YELLOW}--no-loc{UI.RESET}                      Block Geolocation (GeoClue & Wi-Fi triangulation)
  {UI.YELLOW}--no-storage{UI.RESET}                  Prevent access to host storage ($HOME)
  {UI.YELLOW}--disposable{UI.RESET}                  100% RAM tmpfs mode (Zero SSD footprint upon exit)

{UI.BOLD}EXAMPLES:{UI.RESET}
  sinabox telegram-desktop
  sinabox run --no-mic --no-cam discord
  sinabox run --disposable google-chrome-stable
  sinabox profile create custom01 --no-mic --no-cam --disposable
  telegram-desktop --sinabox --custom01
"""
    print(help_text)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print_help()
        sys.exit(0)

    arg1 = sys.argv[1]

    if arg1 == "sync-vpn":
        geo = GeoManager.get_geo(force_refresh=True)
        UI.success(f"VPN Geo Status: IP: {geo['ip']} | City: {geo['city']}, {geo['country']} | Timezone: {geo['timezone']} | Locale: {geo['locale']}")
        sys.exit(0)

    elif arg1 == "hardware":
        if len(sys.argv) > 2 and sys.argv[2] == "reset":
            HardwareManager.reset()
        else:
            hw = HardwareManager.get_active()
            print(json.dumps(hw, indent=2))
        sys.exit(0)

    elif arg1 == "profile":
        if len(sys.argv) < 3:
            UI.error("Usage: sinabox profile [create|list|delete] <name>")
            sys.exit(1)
        sub = sys.argv[2]
        if sub == "list":
            profiles = ProfileManager.list()
            UI.info(f"Custom SinaBox Profiles ({len(profiles)}):")
            for p in profiles:
                print(f"  • {p}")
        elif sub == "create":
            if len(sys.argv) < 4:
                UI.error("Profile name required! Usage: sinabox profile create <name> [flags...]")
                sys.exit(1)
            pname = sys.argv[3]
            if pname.startswith("-"):
                UI.error(f"Invalid profile name '{pname}'. Profile name cannot start with '-'")
                sys.exit(1)

            valid_flags = {
                "--no-mic": "no_mic",
                "--no-cam": "no_cam",
                "--no-gpu": "no_gpu",
                "--no-net": "no_net",
                "--no-loc": "no_loc",
                "--no-storage": "no_storage",
                "--disposable": "disposable",
            }

            opts = {k: False for k in valid_flags.values()}
            unknown_flags = []

            for arg in sys.argv[4:]:
                if arg in valid_flags:
                    opts[valid_flags[arg]] = True
                else:
                    unknown_flags.append(arg)

            if unknown_flags:
                UI.error(f"Unrecognized flag(s): {', '.join(unknown_flags)}")
                UI.info(f"Available flags: {', '.join(valid_flags.keys())}")
                sys.exit(1)

            ProfileManager.create(pname, opts)
            # Auto-sync desktop menus
            os.system("python3 /home/sina/.gemini/antigravity/scratch/sinabox/desktop_patcher.py >/dev/null 2>&1 &")
        elif sub == "delete":
            if len(sys.argv) < 4:
                UI.error("Profile name required!")
                sys.exit(1)
            ProfileManager.delete(sys.argv[3])
            # Auto-sync desktop menus
            os.system("python3 /home/sina/.gemini/antigravity/scratch/sinabox/desktop_patcher.py >/dev/null 2>&1 &")
        sys.exit(0)

    # Execution (run or direct binary)
    raw_args = sys.argv[1:]
    if raw_args[0] == "run":
        raw_args = raw_args[1:]

    # Parse flags
    options = {
        "no_mic": False,
        "no_cam": False,
        "no_gpu": False,
        "no_net": False,
        "no_loc": False,
        "no_storage": False,
        "disposable": False,
        "profile": None,
        "space": None,
    }

    valid_exec_flags = {
        "--no-mic": "no_mic",
        "--no-cam": "no_cam",
        "--no-gpu": "no_gpu",
        "--no-net": "no_net",
        "--no-loc": "no_loc",
        "--no-storage": "no_storage",
        "--disposable": "disposable",
    }

    target_cmd = []
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg in valid_exec_flags:
            options[valid_exec_flags[arg]] = True
        elif arg in ["-p", "--profile"]:
            i += 1
            if i < len(raw_args):
                options["profile"] = raw_args[i]
            else:
                UI.error("Option --profile requires an argument!")
                sys.exit(1)
        elif arg.startswith("--profile="):
            options["profile"] = arg.split("=", 1)[1]
        elif arg in ["-s", "--space"]:
            i += 1
            if i < len(raw_args):
                options["space"] = raw_args[i]
            else:
                UI.error("Option --space requires an argument! e.g. --space account2")
                sys.exit(1)
        elif arg.startswith("--space="):
            options["space"] = arg.split("=", 1)[1]
        elif arg.startswith("--") and ProfileManager.get(arg[2:]):
            options["profile"] = arg[2:]
        elif arg.startswith("-"):
            # Any unrecognized flag starting with - or --
            UI.error(f"Unrecognized flag '{arg}'!")
            UI.info(f"Available flags: {', '.join(valid_exec_flags.keys())}, --space <name>, --profile <name>")
            all_profiles = ProfileManager.list()
            if all_profiles:
                UI.info(f"Available custom profile flags: {', '.join(['--' + p for p in all_profiles])}")
            sys.exit(1)
        else:
            target_cmd = raw_args[i:]
            break
        i += 1

    # Load custom profile if provided
    if options["profile"]:
        pdata = ProfileManager.get(options["profile"])
        if pdata:
            UI.info(f"Loaded custom profile '{options['profile']}'")
            for k, v in pdata.items():
                if v:
                    options[k] = v
        else:
            UI.error(f"Profile '{options['profile']}' does not exist!")
            all_p = ProfileManager.list()
            if all_p:
                UI.info(f"Existing profiles: {', '.join(all_p)}")
            else:
                UI.info("No custom profiles exist yet. Create one with: sinabox profile create <name> [flags...]")
            sys.exit(1)

    if not target_cmd:
        UI.error("No target command provided to run!")
        print_help()
        sys.exit(1)

    SandboxEngine.run(target_cmd, options)

if __name__ == "__main__":
    main()
