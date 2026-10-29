<#
.SYNOPSIS
  Installs krish-clone on this Windows home computer, in its own virtual environment.

.DESCRIPTION
  Checks first and installs nothing if a required piece is missing, saying which.
  Then creates %LOCALAPPDATA%\krish-clone\venv, installs content-watcher from its clone beside this
  one, installs krish-clone with its voice, face and speaker extras (CPU only, no compiler needed),
  downloads the face models once (sha256 checked) and runs `clone doctor`.

  Run from the krish-clone folder in PowerShell:
    powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1
  To only check:
    powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1 -CheckOnly
#>
param(
  [switch]$CheckOnly,
  [string]$Python = "py",
  [string]$PythonVersion = "-3.12",
  [string]$ContentWatcher = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "content-watcher")
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $env:LOCALAPPDATA "krish-clone\venv"
$missing = @()

function Check($name, $ok, $detail) {
  if ($ok) { Write-Host ("ok       {0,-18} {1}" -f $name, $detail) }
  else { Write-Host ("MISSING  {0,-18} {1}" -f $name, $detail); $script:missing += $name }
}

$pyOk = $false
try { $pyVer = & $Python $PythonVersion -c "import sys; print(sys.version.split()[0])" 2>$null; $pyOk = $LASTEXITCODE -eq 0 } catch {}
Check "python" $pyOk ($(if ($pyOk) { $pyVer } else { "winget install Python.Python.3.12" }))
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
Check "ffmpeg" ([bool]$ffmpeg) ($(if ($ffmpeg) { $ffmpeg.Source } else { "winget install Gyan.FFmpeg, then open a new terminal" }))
$cwOk = Test-Path -LiteralPath (Join-Path $ContentWatcher "content_watcher") -PathType Container
Check "content-watcher" $cwOk ($(if ($cwOk) { $ContentWatcher } else { "clone krishanraja/content-watcher beside krish-clone, or pass -ContentWatcher" }))
$free = (Get-PSDrive -Name ($env:LOCALAPPDATA.Substring(0,1))).Free / 1GB
Check "disk" ($free -gt 8) ("{0:N1} GB free (about 4 GB for models and voice masters)" -f $free)

if ($missing.Count) { Write-Host "`nNothing installed. Fix the MISSING lines above, then run again."; exit 1 }
if ($CheckOnly) { Write-Host "`nAll checks pass. Run without -CheckOnly to install."; exit 0 }

if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) { & $Python $PythonVersion -m venv $venv }
$py = Join-Path $venv "Scripts\python.exe"
& $py -m pip install --upgrade pip --quiet
& $py -m pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu
& $py -m pip install --quiet -e $ContentWatcher
& $py -m pip install --quiet -e "$repo[voice,face,speaker]"
if ($LASTEXITCODE -ne 0) { Write-Host "pip failed; see above."; exit 1 }

Write-Host "`nInstalled into $venv. Checking:"
& (Join-Path $venv "Scripts\clone.exe") doctor
