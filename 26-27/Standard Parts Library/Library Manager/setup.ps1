# One-time setup for the Anteater Racing parts library. Run through "Setup (run once).bat".
$ErrorActionPreference = "Stop"
$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root    = Split-Path -Parent $Here
$Library = Join-Path $Root "Anteater Parts"
$Driver  = "SQLite3 ODBC Driver"

function Step($n, $text) { Write-Host ""; Write-Host "[$n/5] $text" -ForegroundColor Cyan }
function Ok($text)   { Write-Host "  OK  $text" -ForegroundColor Green }
function Fail($text) { Write-Host "  !!  $text" -ForegroundColor Red; Write-Host ""; Read-Host "Fix the above, then run Setup again. Press Enter to close"; exit 1 }
function Ask($text)  { (Read-Host "  $text [Y/n]") -notmatch '^[nN]' }

function Find-Python {
    foreach ($cmd in @(@("py", "-3"), @("python"))) {
        try {
            $v = & $cmd[0] $cmd[1..9] -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and [version]$v -ge [version]"3.11") { return ,$cmd }
        } catch {}
    }
    return $null
}

Write-Host "Anteater Racing - Parts Library setup" -ForegroundColor White

Step 1 "Python 3.11 or newer"
$py = Find-Python
if (-not $py) {
    if ((Get-Command winget -ErrorAction SilentlyContinue) -and (Ask "Python not found. Install Python 3.12 now with winget?")) {
        winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
        $py = Find-Python
    }
    if (-not $py) { Fail "Install Python 3.11+ from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then reopen this window." }
}
Ok ("Python " + (& $py[0] $py[1..9] --version))

if (Get-Command git -ErrorAction SilentlyContinue) {
    git config --global core.longpaths true   # library paths can exceed Windows' 260-character limit
    Ok "Git long paths enabled"
} else {
    Write-Host "  Git not found: install GitHub Desktop (https://desktop.github.com) to publish parts." -ForegroundColor Yellow
}

Step 2 "KiCad 10"
$kicad = "C:\Program Files\KiCad\10.0\bin\kicad.exe"
if (-not (Test-Path $kicad)) {
    if ((Get-Command winget -ErrorAction SilentlyContinue) -and (Ask "KiCad 10 not found. Install it now with winget?")) {
        winget install --id KiCad.KiCad -e --accept-package-agreements --accept-source-agreements
    }
    if (-not (Test-Path $kicad)) { Fail "Install KiCad 10 from https://www.kicad.org/download/windows/ (default location), open it once, close it, then run Setup again." }
}
Ok "KiCad 10 found"

Step 3 "SQLite ODBC driver (lets KiCad read the parts database)"
if (-not (Get-OdbcDriver -Name $Driver -Platform 64-bit -ErrorAction SilentlyContinue)) {
    Write-Host "  The 64-bit SQLite ODBC driver is not installed."
    Write-Host "  Opening the download page: download and run 'sqliteodbc_w64.exe' (accept the defaults)."
    Start-Process "http://www.ch-werner.de/sqliteodbc/"
    Read-Host "  Press Enter after the installer has finished"
    if (-not (Get-OdbcDriver -Name $Driver -Platform 64-bit -ErrorAction SilentlyContinue)) { Fail "Driver '$Driver' (64-bit) still not found." }
}
Ok "Driver installed"
# Use the data source name the library itself asks for, so setup can never disagree with it.
$dbl = Get-Content (Join-Path $Library "appdata\parts.kicad_dbl") -Raw | ConvertFrom-Json
$Dsn = if ($dbl.source.connection_string -match 'DSN=([^;]+)') { $Matches[1] } else { "AnteaterSQLite" }
if (-not (Get-OdbcDsn -Name $Dsn -DsnType User -Platform 64-bit -ErrorAction SilentlyContinue)) {
    Add-OdbcDsn -Name $Dsn -DsnType User -Platform 64-bit -DriverName $Driver
}
Ok "Data source '$Dsn' ready"

Step 4 "Connect the library to KiCad"
while (Get-Process kicad, eeschema, pcbnew -ErrorAction SilentlyContinue) {
    Read-Host "  KiCad is open. Save your work, close ALL KiCad windows, then press Enter"
}
$helper = Join-Path $Here "anteater_setup.py"
& $py[0] $py[1..9] $helper $Library
if ($LASTEXITCODE -eq 2) {
    if (Ask "This PC is connected to a different Library Manager library. Switch it to the Anteater library?") {
        & $py[0] $py[1..9] $helper $Library --switch
    }
}
if ($LASTEXITCODE -ne 0) { Fail "Connecting to KiCad failed (see message above)." }
Ok "KiCad will show the parts under 'Anteater Parts' in the symbol chooser"

Step 5 "Desktop shortcut"
$launcher = Join-Path $Root "Open Library Manager.bat"
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Anteater Parts Library.lnk"))
$link.TargetPath = $launcher
$link.WorkingDirectory = $Root
$link.IconLocation = "$kicad,0"
$link.Save()
Ok "Shortcut 'Anteater Parts Library' added to your desktop"

Write-Host ""
Write-Host "Setup complete. Double-click 'Anteater Parts Library' on your desktop to add or browse parts." -ForegroundColor Green
Read-Host "Press Enter to close"
