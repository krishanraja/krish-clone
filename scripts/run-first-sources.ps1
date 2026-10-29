<#
.SYNOPSIS
  The first run: the approved episodes source (3 Posts) into the Krish Clone - Assets library.

.DESCRIPTION
  1. Checks everything with `clone doctor`.
  2. Inventory: measures every video, audio file and photo in 3 Posts and writes only
     manifest.json and inventory.md to the library. No media copied. Read it before step 3.
  3. Harvest: writes the clean voice segments (48 kHz WAV) and the chosen face stills.
  4. Builds the reading script for the voice session from the scripts in 3 Posts.

  Identity comes from the dominant face across 3 Posts (Krish presents every episode); speaker
  verification enrols on Friday-join-candidates.wav from the Two passports quality evidence.
  Both live inside the approved source, so nothing pending is read. Nothing is uploaded and no
  ElevenLabs or HeyGen credit is used. Reruns resume from the cache and never overwrite.

  Run from the krish-clone folder:
    powershell -ExecutionPolicy Bypass -File scripts\run-first-sources.ps1
  Inventory only:
    powershell -ExecutionPolicy Bypass -File scripts\run-first-sources.ps1 -Step inventory
#>
param(
  [ValidateSet("all", "inventory", "harvest", "script")][string]$Step = "all",
  [string]$Posts = "H:\My Drive\Ventures\Active Ventures\makeyourmindup\3 Posts",
  [string]$Library = "H:\My Drive\Ventures\Side Hustles, Tools & Projects\Krish Clone - Assets",
  [string]$Enrol = "",
  [double]$Fps = 2
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$studio = Get-Content (Join-Path $repo "config\studio.json") -Raw | ConvertFrom-Json
$runtime = Join-Path ([Environment]::ExpandEnvironmentVariables($studio.local_roots.runtime)) "krish-clone"
$clone = Join-Path $runtime "venv\Scripts\clone.exe"
if (-not (Test-Path $clone)) { Write-Host "Install first: scripts\bootstrap.ps1 or scripts\install-krish-clone.ps1."; exit 1 }
if (-not $Enrol) {
  $Enrol = Join-Path $Posts "2026-10-23 Fri mind.the.gap - Two passports\3 Video\quality evidence\Friday-join-candidates.wav"
}
$logDir = Join-Path $runtime "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ("run-{0:yyyyMMdd-HHmmss}.log" -f (Get-Date))
$env:PYTHONIOENCODING = "utf-8"

function Run([string[]]$arguments) {
  Write-Host "`n> clone $($arguments -join ' ')"
  & $clone @arguments 2>&1 | Tee-Object -FilePath $log -Append | Out-Host
  if ($LASTEXITCODE -ne 0) { Write-Host "Stopped: clone exited $LASTEXITCODE. Log: $log"; exit $LASTEXITCODE }
}

Run @("doctor")
$common = @($Posts, "--source", "episodes", "--out", $Library, "--fps", "$Fps")
if (Test-Path -LiteralPath $Enrol) { $common += @("--enrol", $Enrol) } else { Write-Host "No enrolment clip at $Enrol; voice stays unverified." }

if ($Step -in "all", "inventory") {
  Run (@("inventory") + $common)
  Write-Host "`nInventory: $(Join-Path $Library 'inventory.md')"
  if ($Step -eq "all") {
    $answer = Read-Host "Read the inventory. Harvest the media into the library now? (y/n)"
    if ($answer -ne "y") { Write-Host "Stopped before harvest. Run again with -Step harvest."; exit 0 }
  }
}
if ($Step -in "all", "harvest") {
  Run (@("harvest") + $common)
}
if ($Step -in "all", "script") {
  Run @("script", $Posts, "--source", "episodes", "--out", (Join-Path $Library "reading-script.md"))
}
Write-Host "`nDone. Library: $Library`nLog: $log"
