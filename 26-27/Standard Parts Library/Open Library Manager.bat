@echo off
title Anteater Parts Library - close this window or click Quit in the app to stop
cd /d "%~dp0"
rem KiCad files are UTF-8; without this Windows Python garbles symbols with characters like Ohm/micro signs
set "PYTHONUTF8=1"

rem Only one Library Manager may edit the library at a time; two copies corrupt saves.
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*Library Manager\app.py*' }) { exit 1 }"
if errorlevel 1 goto already_running

set "PY=py -3"
where py >nul 2>nul || set "PY=python"

rem GitHub Desktop ships its own git but doesn't put it on PATH; use it if there's no other git
where git >nul 2>nul || for /d %%D in ("%LOCALAPPDATA%\GitHubDesktop\app-*") do if exist "%%D\resources\app\git\cmd\git.exe" set "PATH=%%D\resources\app\git\cmd;%PATH%"
where git >nul 2>nul || if exist "%ProgramFiles%\Git\cmd\git.exe" set "PATH=%ProgramFiles%\Git\cmd;%PATH%"

rem A GitHub Desktop pull can stop halfway on library files; finish or undo it safely first
where git >nul 2>nul && %PY% "%~dp0Library Manager\anteater_repair.py" "%~dp0Anteater Parts"

rem Get teammates' parts. Works with KiCad open: the parts database KiCad keeps open is
rem rebuilt locally instead of being replaced by git (only skipped if an update would replace it)
where git >nul 2>nul && (
    %PY% "%~dp0Library Manager\anteater_repair.py" "%~dp0Anteater Parts" --pull
    rem boards linked from other repos, e.g. 26-27/VCU from OTA-pcb-testing
    git submodule update --init --recursive >nul 2>nul
    echo.
)
rem rebuild the local parts database if it's missing or out of date
%PY% "%~dp0Library Manager\anteater_repair.py" "%~dp0Anteater Parts" --check-generated

:launch
%PY% "%~dp0Library Manager\app.py" --library "%~dp0Anteater Parts"
if errorlevel 1 goto crashed
exit /b

:already_running
echo The Library Manager is already running.
echo Closing the browser tab does NOT stop it. Either:
echo   - click "Quit manager" at the bottom-left of the app, or
echo   - close the other black "Anteater Parts Library" window - check the taskbar, it may be minimized
echo then open this again.
echo.
pause
exit /b

:crashed
echo.
echo The Library Manager stopped - see the message above. If it isn't clear, run "Setup (run once).bat" again or message the library owner.
pause
