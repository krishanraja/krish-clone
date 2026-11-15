# Runbook

## Install (once per home computer)

Needs Python 3.12 (`py -3.12`) and ffmpeg (`winget install Gyan.FFmpeg`). Nothing else has to be cloned first. Paste into PowerShell:

```powershell
irm https://raw.githubusercontent.com/krishanraja/krish-clone/main/scripts/bootstrap.ps1 | iex
```

It follows the shared Make Your Mind Up layout (`config/studio.json`):

- the code goes to `%USERPROFILE%\dev\makeyourmindup\krish-clone`, beside content-engine and content-watcher (cloned with git, or downloaded as a zip without it; an existing clone is updated, never replaced);
- the venv, models and cache go to `%LOCALAPPDATA%\makeyourmindup\krish-clone\`;
- content-watcher comes from its clone at `%USERPROFILE%\dev\makeyourmindup\content-watcher` if there is one, otherwise straight from GitHub;
- CPU-only packages (no compiler); the face models download once, sha256 checked; it ends with `clone doctor`.

## First run: the approved episodes (3 Posts)

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\dev\makeyourmindup\krish-clone\scripts\run-first-sources.ps1"
```

1. `clone doctor`.
2. `clone inventory`: measures everything in `H:\My Drive\Ventures\Active Ventures\makeyourmindup\3 Posts`; writes only `manifest.json` and `inventory.md` to `H:\My Drive\Ventures\Side Hustles, Tools & Projects\Krish Clone - Assets`.
3. It stops and asks before `clone harvest` writes media.
4. `clone script` writes `reading-script.md` to the library.

Expect roughly an hour or two on a home computer for about 1.8 GB of video (speech transcription and 2 fps face analysis on the CPU). An interrupted run resumes from the cache; a finished one reruns in seconds and adds nothing.

Steps on their own: `-Step inventory`, `-Step harvest`, `-Step script`.

## Next: the free local evaluation

Everything here runs on the home computer and spends nothing. It reads face and voice media, so it never runs in a cloud session. In PowerShell:

```powershell
$clone   = "$env:LOCALAPPDATA\makeyourmindup\krish-clone\venv\Scripts\clone.exe"
$Library = "H:\My Drive\Ventures\Side Hustles, Tools & Projects\Krish Clone - Assets"
$Inbox   = "H:\My Drive\Ventures\Active Ventures\makeyourmindup\Video Engine\Inbox"

# 1. Install or update (an existing clone is updated, never replaced), then check.
irm https://raw.githubusercontent.com/krishanraja/krish-clone/main/scripts/bootstrap.ps1 | iex
& $clone doctor

# 2. Inventory, then harvest, both approved sources. Read inventory.md before each harvest.
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\dev\makeyourmindup\krish-clone\scripts\run-first-sources.ps1"
& $clone inventory $Inbox --source inbox --out $Library
& $clone harvest   $Inbox --source inbox --out $Library

# 3. Twin pre-flight on each phone take, against the headshots.
Get-ChildItem "$Library\Video\*.mp4" | ForEach-Object { & $clone twincheck $_.FullName --gallery (Get-ChildItem "$Library\Photos\*.png").FullName }

# 4. His own spread from the harvested clean clips, and any clone audio judged against it.
& $clone evaluate --real (Get-ChildItem "$Library\voice\clean\*.wav" | Select-Object -First 20).FullName --clone "<clone audio>"

# 5. The likeness baseline: a HeyGen video already made with the approved avatar "Krish Raja", judged against
#    the seed photos at the top of Photos (not "All other photos"). Use a video that already exists; making a
#    new one is a generation and waits for his yes. Any other generator's output is judged the same way later.
& $clone likeness --real (Get-ChildItem "$Library\Photos\*.png").FullName --clone "<an existing HeyGen video>.mp4"
```

`twincheck`, `evaluate` and `likeness` need no source.

The recordings kept in the library itself are the approved source `library` (Krish, 2026-11-14, decision 5.7), for inventory only: it measures them and writes only `manifest.json` and `inventory.md`, copies no media and spends nothing. Point it at the three raw folders, never the whole library, so it does not re-read its own output or the `voice/compressed` copies:

```powershell
& $clone inventory "$Library\Video" "$Library\voice\uncompressed" "$Library\voice\archive" --source library --out $Library
```

A harvest of these recordings, and any upload, waits for Krish's yes.

## Adding a source

Only Krish approves a source, one at a time:

```powershell
& "$env:LOCALAPPDATA\makeyourmindup\krish-clone\venv\Scripts\clone.exe" sources
& "$env:LOCALAPPDATA\makeyourmindup\krish-clone\venv\Scripts\clone.exe" sources approve camera --local-path "H:\My Drive\...\Camera"
```

Then run `inventory` and `harvest` with `--source camera` into the same library. Repeats of audio already kept are skipped.

## After the voice session

Drop the recording into an approved folder (or approve its folder), harvest it, then:

```powershell
clone export elevenlabs --library "<library>" --out "<library>\elevenlabs-upload"
```

The MP3s meet ElevenLabs' PVC spec (192 kbps, about -20 LUFS, -3 dB true peak, 30 minute files). Uploading them is a manual step Krish approves; nothing in this engine uploads.

## Before uploading a HeyGen twin recording

```powershell
clone twincheck "<recording>.mp4" --gallery "<library>\face\photos\*.jpg"
```

`ready` or `reshoot`, with the reason for each check. See `docs/CAPTURE.md`.

## Judging a clone

```powershell
clone evaluate --real <5+ real clips> --clone <clone clips>
clone likeness --real (Get-ChildItem "<library>\Photos\*.png").FullName --clone "<generated stills or video>"
clone abpack --real <real clips> --clone <clone clips> --out <folder>
clone abscore --key <folder>\KEY-do-not-share.json --answers answers.csv
```

See `docs/EVALUATION.md`.
