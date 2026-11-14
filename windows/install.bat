@echo off
:: ====================================================================
:: SinaBox Windows One-Click Installer
:: Developed by Sina Khanzadeh
:: ====================================================================

echo [*] Installing SinaBox for Windows...

set TARGET_DIR=%USERPROFILE%\.sinabox
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

copy /Y "%~dp0sinabox.ps1" "%TARGET_DIR%\sinabox.ps1" >nul

echo [*] Registering context menu (Open with SinaBox)...
reg import "%~dp0install_context_menu.reg" >nul

echo.
echo [OK] SinaBox for Windows installed successfully!
echo You can now right-click any file or directory and choose "Open with SinaBox".
pause
