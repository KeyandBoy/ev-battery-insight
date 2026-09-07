@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title EV-Battery Insight - Startup

set "ROOT=%~dp0"
set "ENV_NAME=evBatteryInsight"
set "CONDA_ROOT=D:\computerProgram\Anaconda"
set "PYTHON_EXE=%CONDA_ROOT%\envs\%ENV_NAME%\python.exe"
set "NPM_EXE=npm.cmd"
set "LOG_DIR=%ROOT%logs"
set "MYSQL_HOST=127.0.0.1"
set "MYSQL_PORT=3306"
set "MYSQL_USER=root"
set "MYSQL_PASSWORD="

echo ============================================================
echo   EV-Battery Insight startup
echo ============================================================
echo [INFO] Project: %ROOT%
echo [INFO] Conda environment: %ENV_NAME%

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python environment not found:
    echo         %PYTHON_EXE%
    echo [HINT]  Create it with: conda create -n %ENV_NAME% python=3.12
    pause
    exit /b 1
)

if not exist "%ROOT%frontend\package.json" (
    echo [ERROR] Frontend project was not found.
    pause
    exit /b 1
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [INFO] Logs: %LOG_DIR%
echo.

call :load_mysql_env
if not defined MYSQL_PASSWORD (
    echo [INFO] MySQL password is not configured in .env.
    set /p "MYSQL_PASSWORD=Enter MySQL password, or press Enter to skip DataFlow and Region: "
)
if defined MYSQL_PASSWORD (
    echo [INFO] MySQL credentials loaded for DataFlow and Region.
    echo [INFO] Checking required MySQL databases...
    "%PYTHON_EXE%" "%ROOT%scripts\ensure_mysql_databases.py"
    if errorlevel 1 (
        echo [ERROR] MySQL is reachable only if credentials and server are correct.
        echo [WARN]  DataFlow and Region were skipped. See logs or fix .env.
    ) else (
        call :start_mysql_python "DataFlow" "%ROOT%backend\dataflow" "%ROOT%backend\dataflow\run.py" 5001 "%LOG_DIR%\dataflow.log" dataflow_canvas
        call :start_mysql_python "Region" "%ROOT%backend\region" "%ROOT%backend\region\app.py" 5002 "%LOG_DIR%\region.log" highdim_region_vis
    )
) else (
    echo [WARN] No MySQL password. DataFlow and Region were skipped.
    echo [HINT] Put MYSQL_PASSWORD in .env or enter it when starting again.
)
call :start_python "Voronoi" "%ROOT%backend\voronoi" "%ROOT%backend\voronoi\run.py" 5003 "%LOG_DIR%\voronoi.log"
call :start_python "Chain-Connect" "%ROOT%backend\chain-connect" "%ROOT%backend\chain-connect\app.py" 5004 "%LOG_DIR%\chain-connect.log"
call :start_python "EV Insight" "%ROOT%" "%ROOT%backend\ev-insight\app.py" 5005 "%LOG_DIR%\ev-insight.log"

echo [INFO] Starting frontend on port 5175...
start "" /b /D "%ROOT%frontend" cmd /c "npm.cmd run dev > "%LOG_DIR%\frontend.log" 2>&1"
if errorlevel 1 (
    echo [ERROR] Frontend process could not be created.
) else (
    echo [OK]    Frontend process created. Log: logs\frontend.log
)

echo.
echo [INFO] Waiting for services to become ready...
timeout /t 10 /nobreak >nul

call :check_port "DataFlow" 5001
call :check_port "Region" 5002
call :check_port "Voronoi" 5003
call :check_port "Chain-Connect" 5004
call :check_port "EV Insight" 5005
call :check_port "Frontend" 5175

echo.
echo ============================================================
echo   Startup finished
echo ============================================================
echo [INFO] Frontend: http://localhost:5175
echo [INFO] EV page:  http://localhost:5175/ev-insight/health
echo [INFO] Logs:     %LOG_DIR%
echo [HINT] If a service failed, open its log file for details.
echo [HINT] Use stop.bat to stop project services.
echo.
start "" "http://localhost:5175"
pause
exit /b 0

:start_python
set "SERVICE_NAME=%~1"
set "SERVICE_DIR=%~2"
set "SERVICE_SCRIPT=%~3"
set "SERVICE_PORT=%~4"
set "SERVICE_LOG=%~5"
call :is_port_in_use %SERVICE_PORT%
if defined PORT_FOUND (
    echo [SKIP]  %SERVICE_NAME% is already running on port %SERVICE_PORT%.
    exit /b 0
)
echo [INFO] Starting %SERVICE_NAME% on port %SERVICE_PORT%...
start "" /b /D "%SERVICE_DIR%" cmd /c ""%PYTHON_EXE%" "%SERVICE_SCRIPT%" > "%SERVICE_LOG%" 2>&1"
if errorlevel 1 (
    echo [ERROR] %SERVICE_NAME% process could not be created.
) else (
    echo [OK]    %SERVICE_NAME% process created. Log: %SERVICE_LOG%
)
exit /b 0

:start_mysql_python
set "SERVICE_NAME=%~1"
set "SERVICE_DIR=%~2"
set "SERVICE_SCRIPT=%~3"
set "SERVICE_PORT=%~4"
set "SERVICE_LOG=%~5"
set "SERVICE_DATABASE=%~6"
call :is_port_in_use %SERVICE_PORT%
if defined PORT_FOUND (
    echo [SKIP]  %SERVICE_NAME% is already running on port %SERVICE_PORT%.
    exit /b 0
)
echo [INFO] Starting %SERVICE_NAME% on port %SERVICE_PORT%...
start "" /b /D "%SERVICE_DIR%" cmd /c "set DATABASE_URL=mysql+pymysql://%MYSQL_USER%:%MYSQL_PASSWORD%@%MYSQL_HOST%:%MYSQL_PORT%/%SERVICE_DATABASE%?charset=utf8mb4&& "%PYTHON_EXE%" "%SERVICE_SCRIPT%" > "%SERVICE_LOG%" 2>&1"
if errorlevel 1 (
    echo [ERROR] %SERVICE_NAME% process could not be created.
) else (
    echo [OK]    %SERVICE_NAME% process created. Log: %SERVICE_LOG%
)
exit /b 0

:load_mysql_env
if not exist "%ROOT%.env" exit /b 0
for /f "usebackq tokens=1,* delims==" %%A in ("%ROOT%.env") do (
    if "%%A"=="MYSQL_HOST" set "MYSQL_HOST=%%B"
    if "%%A"=="MYSQL_PORT" set "MYSQL_PORT=%%B"
    if "%%A"=="MYSQL_USER" set "MYSQL_USER=%%B"
    if "%%A"=="MYSQL_PASSWORD" set "MYSQL_PASSWORD=%%B"
)
exit /b 0

:is_port_in_use
set "PORT_FOUND="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%~1 .*LISTENING"') do set "PORT_FOUND=%%P"
exit /b 0

:check_port
set "CHECK_NAME=%~1"
set "CHECK_PORT=%~2"
set "PORT_FOUND="
for /l %%I in (1,1,30) do (
    if not defined PORT_FOUND (
        for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%CHECK_PORT% .*LISTENING"') do set "PORT_FOUND=%%P"
        if not defined PORT_FOUND timeout /t 1 /nobreak >nul
    )
)
if defined PORT_FOUND (
    echo [OK]    %CHECK_NAME% is listening on %CHECK_PORT%
) else (
    echo [ERROR] %CHECK_NAME% is not listening on %CHECK_PORT%
)
exit /b 0
