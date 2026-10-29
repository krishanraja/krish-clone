<#
.SYNOPSIS
  One paste: puts krish-clone where the rest of the Make Your Mind Up machinery lives and installs it.

.DESCRIPTION
  Uses the shared local layout (config/studio.json local_roots.repos): the clone goes to
  %USERPROFILE%\dev\makeyourmindup\krish-clone, beside content-engine and content-watcher. Clones with git when
  git is installed, else downloads the code as a zip. Updates an existing clone instead of replacing it. Then
  runs scripts\install-krish-clone.ps1. Nothing is deleted.

  Paste into PowerShell:
    irm https://raw.githubusercontent.com/krishanraja/krish-clone/main/scripts/bootstrap.ps1 | iex
#>
$ErrorActionPreference = "Stop"
$root = Join-Path $env:USERPROFILE "dev\makeyourmindup"
$target = Join-Path $root "krish-clone"
New-Item -ItemType Directory -Force -Path $root | Out-Null

if (Test-Path (Join-Path $target ".git")) {
  Write-Host "Updating $target"
  git -C $target pull --ff-only
} elseif (Test-Path $target) {
  Write-Host "$target exists but is not a git clone; using it as it is."
} elseif (Get-Command git -ErrorAction SilentlyContinue) {
  git clone https://github.com/krishanraja/krish-clone $target
} else {
  Write-Host "git not found; downloading the code as a zip."
  $zip = Join-Path $env:TEMP "krish-clone-main.zip"
  Invoke-WebRequest https://github.com/krishanraja/krish-clone/archive/refs/heads/main.zip -OutFile $zip
  Expand-Archive $zip -DestinationPath $root -Force
  Rename-Item (Join-Path $root "krish-clone-main") $target
  Remove-Item $zip
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $target "scripts\install-krish-clone.ps1")
Write-Host "`nNext: powershell -ExecutionPolicy Bypass -File `"$target\scripts\run-first-sources.ps1`""
