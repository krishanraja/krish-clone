# krish-clone

Builds Krish's voice and likeness training library from his own recordings and photos, on his own machine, then hands it to ElevenLabs and HeyGen in the shape each one asks for, and judges the clones that come back. It measures the gaps instead of guessing them.

Nothing here uploads or spends a credit. Every upload, clone or generation is a manual step Krish approves when it happens.

## Commands

| Command | What it does |
|---|---|
| `clone doctor` | Checks ffmpeg, the extras, the face models, the approved source folders and the library folder. |
| `clone sources [approve\|reject ID --local-path P]` | Lists sources; Krish approves one at a time. |
| `clone inventory PATHS --source ID --out LIBRARY` | Measures everything; writes only `manifest.json` and `inventory.md`. |
| `clone harvest PATHS --source ID --out LIBRARY` | Also writes clean voice segments (48 kHz WAV) and chosen face stills. |
| `clone script PATHS --source ID --out FILE` | The reading script for the voice session, from his own scripts. |
| `clone export elevenlabs --library L --out DIR` | 30 minute MP3s at the PVC spec (192 kbps, about -20 LUFS, -3 dB peak). |
| `clone twincheck VIDEO --gallery PHOTOS` | Pre-flight for a HeyGen Digital Twin take: ready or reshoot, with reasons. |
| `clone evaluate --real ... --clone ...` | Speaker similarity of a clone against Krish's own spread. |
| `clone abpack` / `clone abscore` | Blind A/B pack for people who know him, and its score. |

## Install and first run (Windows home computer)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-krish-clone.ps1
powershell -ExecutionPolicy Bypass -File scripts\run-first-sources.ps1
```

Details: `docs/RUNBOOK.md`.

## Read next

- `docs/STRATEGY.md`: the gaps, what closed them, and what only Krish can supply.
- `docs/CAPTURE.md`: the voice session and the twin take, against each platform's current guidance.
- `docs/EVALUATION.md`: how "indistinguishable" is judged, with the calibration numbers.
- `docs/ARCHITECTURE.md`: stages, rerun behaviour and the decisions behind them.
- `NOW.md`: where it stands.

## Tests

```sh
python -m unittest discover -s tests -t . -v
```

Generated tones, noise and stub images only; no face or voice of Krish's enters this repository (it is public, and CI refuses media files).
