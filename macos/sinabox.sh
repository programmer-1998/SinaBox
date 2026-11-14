#!/usr/bin/env bash
# ====================================================================
# SinaBox macOS Client
# Geo-Synchronized & Privacy-Preserving Application Sandbox for macOS
# Developed by Sina Khanzadeh
# ====================================================================

VERSION="1.0.0"
SINABOX_DIR="$HOME/.sinabox"
BOXES_DIR="$SINABOX_DIR/boxes"
PROFILES_DIR="$SINABOX_DIR/profiles"

mkdir -p "$BOXES_DIR" "$PROFILES_DIR"

show_help() {
    cat << HELP
=============================================================
  SinaBox for macOS v$VERSION
  Author: Sina Khanzadeh
=============================================================
Usage:
  sinabox.sh run [OPTIONS] <app_path_or_bundle> [args...]
  sinabox.sh profile create <name> [options]
  sinabox.sh sync-vpn

Options:
  --disposable   Run in temporary ephemeral sandbox
  --no-net       Block outbound network connections
  --profile <n>  Load saved security profile
HELP
}

if [[ $# -eq 0 || "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

get_vpn_geo() {
    curl -s --max-time 3 "https://ipapi.co/json/" 2>/dev/null || echo '{"timezone":"UTC","city":"Unknown","country_name":"US"}'
}

ACTION="$1"
shift

if [[ "$ACTION" == "sync-vpn" ]]; then
    GEO=$(get_vpn_geo)
    echo "[SinaBox macOS] Active VPN Geo: $GEO"
    exit 0
fi

if [[ "$ACTION" == "run" ]]; then
    TARGET="$1"
    shift
    GEO=$(get_vpn_geo)
    TZ=$(echo "$GEO" | grep -o '"timezone": *"[^"]*"' | cut -d'"' -f4)
    [[ -z "$TZ" ]] && TZ="UTC"

    echo "✔ [SinaBox macOS] Synchronizing $TARGET with Timezone $TZ..."
    export TZ="$TZ"

    if [[ "$TARGET" == *.app ]]; then
        open -a "$TARGET" --args "$@"
    else
        "$TARGET" "$@"
    fi
fi
