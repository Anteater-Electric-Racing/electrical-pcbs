@echo off
title Anteater Parts Library - close this window or click Quit in the app to stop
cd /d "%~dp0"

rem Only one Library Manager may edit the library at a time; two copies corrupt saves.
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*Library Manager\app.py*' }) { exit 1 }"
if errorlevel 1 goto already_running

set "PY=py -3"
where py >nul 2>nul || set "PY=python"

rem A GitHub Desktop pull can stop halfway on library files; finish or undo it safely first
where git >nul 2>nul && %PY% "%~dp0Library Manager\anteater_repair.py" "%~dp0Anteater Parts"

where git >nul 2>nul && (
    echo Getting the latest parts from GitHub...
    git pull --ff-only || echo   Could not update automatically. Use Publish in the app, or pull in GitHub Desktop.
    rem boards linked from other repos, e.g. 26-27/VCU from OTA-pcb-testing
    git submodule update --init --recursive >nul 2>nul
    rem a bad merge can delete or stale the parts database; rebuild it if so
    %PY% "%~dp0Library Manager\anteater_repair.py" "%~dp0Anteater Parts" --check-generated
    echo.
)

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
