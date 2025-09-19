@echo off
REM Windows Firewall Configuration for Code Summarizer
REM Run this as Administrator to allow external access

echo ====================================
echo Code Summarizer Firewall Setup
echo ====================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Configuring Windows Firewall to allow external access...
echo.

REM Allow inbound connections on port 8000 (API)
echo Adding firewall rule for API server (port 8000)...
netsh advfirewall firewall add rule name="Code Summarizer API" dir=in action=allow protocol=TCP localport=8000
if %errorlevel% equ 0 (
    echo ✅ API port 8000 allowed
) else (
    echo ❌ Failed to add API firewall rule
)

REM Allow inbound connections on port 8080 (Frontend)
echo Adding firewall rule for Frontend server (port 8080)...
netsh advfirewall firewall add rule name="Code Summarizer Frontend" dir=in action=allow protocol=TCP localport=8080
if %errorlevel% equ 0 (
    echo ✅ Frontend port 8080 allowed
) else (
    echo ❌ Failed to add Frontend firewall rule
)

echo.
echo ====================================
echo Firewall Configuration Complete!
echo ====================================
echo.
echo Your Code Summarizer is now accessible from other machines:
echo.

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set LOCAL_IP=%%b
        goto :found_ip
    )
)
:found_ip

if defined LOCAL_IP (
    echo Frontend: http://%LOCAL_IP%:8080
    echo API:      http://%LOCAL_IP%:8000
    echo API Docs: http://%LOCAL_IP%:8000/docs
) else (
    echo Frontend: http://YOUR_IP_ADDRESS:8080
    echo API:      http://YOUR_IP_ADDRESS:8000
    echo API Docs: http://YOUR_IP_ADDRESS:8000/docs
)

echo.
echo To find your IP address, run: ipconfig
echo Look for "IPv4 Address" under your network adapter
echo.
echo To remove these rules later, run:
echo   netsh advfirewall firewall delete rule name="Code Summarizer API"
echo   netsh advfirewall firewall delete rule name="Code Summarizer Frontend"
echo.
pause