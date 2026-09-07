@echo off
setlocal
chcp 65001 >nul
title EV-Battery Insight - Stop

echo [INFO] Stopping EV-Battery Insight services...
for %%P in (5001 5002 5003 5004 5005 5175) do (
    for /f "tokens=5" %%I in ('netstat -ano ^| findstr ":%%P .*LISTENING"') do (
        echo [INFO] Stopping port %%P, PID %%I
        taskkill /PID %%I /T /F >nul 2>&1
    )
)
echo [OK] Services stopped.
pause
