<#
.SYNOPSIS
  Installs krish-clone on this Windows home computer, in its own virtual environment.

.DESCRIPTION
  Checks first and installs nothing if a required piece is missing, saying which.
  Then creates %LOCALAPPDATA%\makeyourmindup\krish-clone\venv (the shared layout's runtime folder), installs
  content-watcher (from its clone in the shared layout if there is one, else straight from GitHub, so no clone
  is needed), installs krish-clone with its voice, face and speaker extras (CPU only, no compiler), downloads
  the face models once (sha256 checked) and runs `clone doctor`.

  Usually run for you by scripts\bootstrap.ps1. On its own, from the krish-clone folder:
    powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1
  Only check:
    powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1 -CheckOnly
#>
param(
  [switch]$CheckOnly,
  [string]$Python = "py",
  [string]$PythonVersion = "-3.12"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$studio = Get-Content (Join-Path $repo "config\studio.json") -Raw | ConvertFrom-Json
$runtime = Join-Path ([Environment]::ExpandEnvironmentVariables($studio.local_roots.runtime)) "krish-clone"
$venv = Join-Path $runtime "venv"
$cwClone = $studio.local_roots.repos.Replace("{repo}", "content-watcher")
$cwClone = $cwClone.Replace("C:\Users\krish", $env:USERPROFILE)
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
$free = (Get-PSDrive -Name ($env:LOCALAPPDATA.Substring(0,1))).Free / 1GB
Check "disk" ($free -gt 8) ("{0:N1} GB free (about 4 GB for models and voice masters)" -f $free)
$cwLocal = Test-Path -LiteralPath (Join-Path $cwClone "content_watcher") -PathType Container
Write-Host ("info     {0,-18} {1}" -f "content-watcher", $(if ($cwLocal) { "using the clone at $cwClone" } else { "no clone at $cwClone; installing from GitHub" }))

if ($missing.Count) { Write-Host "`nNothing installed. Fix the MISSING lines above, then run again."; exit 1 }
if ($CheckOnly) { Write-Host "`nAll checks pass. Run without -CheckOnly to install."; exit 0 }

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) { & $Python $PythonVersion -m venv $venv }
$py = Join-Path $venv "Scripts\python.exe"
& $py -m pip install --upgrade pip --quiet
& $py -m pip install --quiet torch torchaudio --index-url https://download.pytorch.org/whl/cpu
if ($cwLocal) { & $py -m pip install --quiet -e $cwClone }
else { & $py -m pip install --quiet "content-watcher @ https://github.com/krishanraja/content-watcher/archive/refs/heads/main.zip" }
& $py -m pip install --quiet -e "$repo[voice,face,speaker]"
if ($LASTEXITCODE -ne 0) { Write-Host "pip failed; see above."; exit 1 }

Write-Host "`nInstalled into $venv. Checking:"
& (Join-Path $venv "Scripts\clone.exe") doctor
