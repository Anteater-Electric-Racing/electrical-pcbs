@echo off
title Anteater Parts Library (close this window or click Quit in the app to stop)
cd /d "%~dp0"

where git >nul 2>nul && (
    echo Getting the latest parts from GitHub...
    git pull --ff-only || echo   Could not update automatically. Pull in GitHub Desktop, then reopen.
    echo.
)

set "PY=py -3"
where py >nul 2>nul || set "PY=python"
%PY% "%~dp0Library Manager\app.py" --library "%~dp0Anteater Parts"
if errorlevel 1 (
    echo.
    echo The Library Manager stopped with an error. Has "Setup (run once).bat" been run on this PC?
    pause
)
