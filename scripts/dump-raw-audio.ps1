<#
.SYNOPSIS
  Dump the audio of Krish's raw recordings (the Video Engine Inbox) into the Krish Clone library.

.DESCRIPTION
  Krish, 2026-10-31: "Just give me a script to do only the raw recordings from inbox and archive,
  because the rest definitely have music under them. All I want right now is a dump of the
  repository in the clone folder of audio ASAP."

  Every video or audio file at the top of the Inbox becomes one WAV (48 kHz, 24-bit, its own
  channels) in "<Library>\voice\raw-dump". Nothing is cut, cleaned or judged: this is the whole
  soundtrack of each raw take. The sources are only read. An output that already exists is never
  overwritten, so a rerun only adds what is new. A list of what was written (source, size, output,
  seconds) goes to raw-dump.csv beside the WAVs. Nothing is uploaded and no credit is used.

  The Archive holds finished cuts, which carry the music bed, so it is read only with -IncludeArchive.

  Run on SURFACE from any folder:
    powershell -ExecutionPolicy Bypass -File "<path>\dump-raw-audio.ps1"
  Add -IncludeArchive to dump the Archive's files too.
#>
param(
  [string]$Inbox = "H:\My Drive\Ventures\Active Ventures\makeyourmindup\Video Engine\Inbox",
  [string]$Archive = "H:\My Drive\Ventures\Active Ventures\makeyourmindup\Video Engine\Archive",
  [string]$Library = "H:\My Drive\Ventures\Side Hustles, Tools & Projects\Krish Clone - Assets",
  [switch]$IncludeArchive
)

# Continue, not Stop: Windows PowerShell 5.1 turns any line ffmpeg writes to stderr into a stopping error
# under Stop. Each step below checks its own result instead.
$ErrorActionPreference = "Continue"
$media = @(".mp4", ".mov", ".m4v", ".mkv", ".webm", ".m4a", ".mp3", ".wav", ".aac")

function Find-Tool([string]$name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  foreach ($root in @("$env:USERPROFILE\dev\krishanraja\toolchain", "$env:USERPROFILE\dev\makeyourmindup\toolchain")) {
    $hit = Get-ChildItem -Path $root -Filter "$name.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $hit.FullName }
  }
  throw "$name not found on PATH or in the toolchain folder. Install ffmpeg (winget install Gyan.FFmpeg) and run again."
}

function Safe([string]$text) { return ($text -replace '[\\/:*?"<>|~]', '-').Trim() }

$ffmpeg = Find-Tool "ffmpeg"
$ffprobe = Find-Tool "ffprobe"
if (-not (Test-Path -LiteralPath $Inbox)) { throw "The Inbox is not reachable at $Inbox. Is Google Drive running and signed in?" }
if (-not (Test-Path -LiteralPath $Library)) { throw "The library is not reachable at $Library." }
$out = Join-Path $Library "voice\raw-dump"
New-Item -ItemType Directory -Force -Path $out -ErrorAction Stop | Out-Null
$csv = Join-Path $out "raw-dump.csv"

$jobs = @()
foreach ($f in Get-ChildItem -LiteralPath $Inbox -File) {
  if ($media -contains $f.Extension.ToLowerInvariant()) { $jobs += [pscustomobject]@{ From = "inbox"; File = $f; Name = "inbox - " + (Safe $f.BaseName) + ".wav" } }
}
if ($IncludeArchive -and (Test-Path -LiteralPath $Archive)) {
  foreach ($f in Get-ChildItem -LiteralPath $Archive -File -Recurse) {
    if ($media -contains $f.Extension.ToLowerInvariant()) {
      $jobs += [pscustomobject]@{ From = "archive"; File = $f; Name = "archive - " + (Safe $f.Directory.Name) + " - " + (Safe $f.BaseName) + ".wav" }
    }
  }
}
Write-Host "$($jobs.Count) recordings to dump into $out"

$made = 0; $kept = 0; $failed = 0; $n = 0
foreach ($job in $jobs) {
  $n++
  $target = Join-Path $out $job.Name
  if (Test-Path -LiteralPath $target) { $kept++; Write-Host "[$n/$($jobs.Count)] already there: $($job.Name)"; continue }
  $streams = & $ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 $job.File.FullName 2>&1 | Where-Object { $_ -match "^\d+$" }
  if (-not $streams) { Write-Host "[$n/$($jobs.Count)] no audio, skipped: $($job.File.Name)"; continue }
  Write-Host "[$n/$($jobs.Count)] $($job.File.Name) ($([math]::Round($job.File.Length / 1MB)) MB)"
  $partial = $target + ".partial.wav"
  & $ffmpeg -nostdin -hide_banner -loglevel error -n -i $job.File.FullName -map 0:a:0 -vn -c:a pcm_s24le -ar 48000 $partial
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $partial)) {
    $failed++; Write-Host "   FAILED (ffmpeg exit $LASTEXITCODE)"
    if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial }
    continue
  }
  Move-Item -LiteralPath $partial -Destination $target -ErrorAction Stop
  $seconds = & $ffprobe -v error -show_entries format=duration -of csv=p=0 $target
  [pscustomobject]@{
    from = $job.From; source = $job.File.FullName; source_bytes = $job.File.Length
    source_modified = $job.File.LastWriteTime.ToString("s"); output = $job.Name; seconds = $seconds
  } | Export-Csv -LiteralPath $csv -Append -NoTypeInformation -Encoding UTF8
  $made++
}
Write-Host "`nDone: $made written, $kept already there, $failed failed. Folder: $out"
if ($failed) { exit 1 }
