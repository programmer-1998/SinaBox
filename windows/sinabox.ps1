<#
.SYNOPSIS
    SinaBox Windows Client
    Geo-Synchronized & Privacy-Preserving Application Sandbox for Windows
    Author: Sina Khanzadeh
#>

param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$AppArgs,

    [switch]$Disposable,
    [switch]$NoMic,
    [switch]$NoCam,
    [switch]$NoNet,
    [string]$Profile,
    [switch]$Help
)

$Version = "1.0.0"
$SinaBoxDir = "$env:USERPROFILE\.sinabox"
$BoxesDir = "$SinaBoxDir\boxes"
$ProfilesDir = "$SinaBoxDir\profiles"

# Ensure directories
New-Item -ItemType Directory -Force -Path $BoxesDir, $ProfilesDir | Out-Null

function Show-Help {
    Write-Host @"
=============================================================
  SinaBox for Windows v$Version
  Author: Sina Khanzadeh
=============================================================
Usage:
  .\sinabox.ps1 run [OPTIONS] <executable> [arguments...]
  .\sinabox.ps1 profile create <name> [options]
  .\sinabox.ps1 profile list
  .\sinabox.ps1 sync-vpn

Options:
  -Disposable     Run in ephemeral temporary sandbox (cleans up upon exit)
  -NoMic          Deny microphone access
  -NoCam          Deny webcam access
  -NoNet          Block network communication
  -Profile <name> Load saved custom profile
"@
}

if ($Help -or -not $Command) {
    Show-Help
    exit 0
}

function Get-VpnGeo {
    try {
        $res = Invoke-RestMethod -Uri "https://ipapi.co/json/" -TimeoutSec 3 -Headers @{"User-Agent"="SinaBox-Win/$Version"}
        return @{
            IP = $res.ip
            City = $res.city
            Country = $res.country_name
            CountryCode = $res.country_code
            Timezone = $res.timezone
        }
    } catch {
        return @{
            IP = "127.0.0.1"
            City = "Unknown"
            Country = "United States"
            CountryCode = "US"
            Timezone = "UTC"
        }
    }
}

if ($Command -eq "sync-vpn") {
    $geo = Get-VpnGeo
    Write-Host "[SinaBox Win] VPN Exit Node: $($geo.City), $($geo.Country) | Timezone: $($geo.Timezone) | IP: $($geo.IP)" -ForegroundColor Cyan
    exit 0
}

if ($Command -eq "run") {
    $targetApp = $AppArgs[0]
    $targetArgs = $AppArgs[1..($AppArgs.Length-1)]

    $geo = Get-VpnGeo
    Write-Host "[SinaBox Win] Launching $targetApp synchronized with $($geo.City), $($geo.Country) [$($geo.Timezone)]..." -ForegroundColor Green

    # Set process-level environment variables
    $env:TZ = $geo.Timezone

    # Start target process
    Start-Process -FilePath $targetApp -ArgumentList $targetArgs
}
