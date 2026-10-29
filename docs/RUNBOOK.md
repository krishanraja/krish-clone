# Runbook

## Install (once per home computer)

Needs Python 3.12 (`py -3.12`), ffmpeg (`winget install Gyan.FFmpeg`), and content-watcher cloned beside krish-clone.

```powershell
cd <your repos folder>\krish-clone
powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1 -CheckOnly
powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1
```

It creates `%LOCALAPPDATA%\krish-clone\venv`, installs CPU-only packages (no compiler), downloads the face models once (sha256 checked) and ends with `clone doctor`.

## First run: the approved episodes (3 Posts)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-first-sources.ps1
```

1. `clone doctor`.
2. `clone inventory`: measures everything in `H:\My Drive\Ventures\Active Ventures\makeyourmindup\3 Posts`; writes only `manifest.json` and `inventory.md` to `H:\My Drive\Ventures\Side Hustles, Tools & Projects\Krish Clone - Assets`.
3. It stops and asks before `clone harvest` writes media.
4. `clone script` writes `reading-script.md` to the library.

Expect roughly an hour or two on a home computer for about 1.8 GB of video (speech transcription and 2 fps face analysis on the CPU). An interrupted run resumes from the cache; a finished one reruns in seconds and adds nothing.

Steps on their own: `-Step inventory`, `-Step harvest`, `-Step script`.

## Adding a source

Only Krish approves a source, one at a time:

```powershell
& "$env:LOCALAPPDATA\krish-clone\venv\Scripts\clone.exe" sources
& "$env:LOCALAPPDATA\krish-clone\venv\Scripts\clone.exe" sources approve camera --local-path "H:\My Drive\...\Camera"
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
clone abpack --real <real clips> --clone <clone clips> --out <folder>
clone abscore --key <folder>\KEY-do-not-share.json --answers answers.csv
```

See `docs/EVALUATION.md`.
