# Architecture

`krish-clone` is a stage conveyor. Each stage owns one decision, writes its result to one place, and can be rerun without changing what is already there.

```
config/sources.json ──> sources gate ──> measure (cached) ──> who is Krish ──> judge ──> library ──> export / evaluate
                         approved only    voice + face          gallery         tiers     Drive      MP3 / A/B pack
```

| Stage | Module | Input | Output | Rerun behaviour |
|---|---|---|---|---|
| sources | `sources.py` | `config/sources.json` | approved folders only | refuses pending, unknown, pathless or out-of-folder files |
| measure: voice | `voice.py`, `media.py` | audio track | sentence segments with pause level, SNR, bed flag, clipping runs, speaker similarity, loudness contour | cached under the runtime folder, `cache/voice` |
| measure: face | `face.py`, `faceonnx.py` | frames at 2 fps, photos | largest face per frame: box, size, sharpness, exposure, cut-off, pose, ArcFace embedding | cached under the runtime folder, `cache/face` |
| who is Krish | `face.Gallery` | all embeddings, or `--gallery` photos | centroid of the dominant identity (refuses when no clear winner) | recomputed each run |
| judge | `voice.judge`, `face.judge` | measures | clean / review / rejected and keep / rejected, each with reasons | pure |
| repeats | `voice.repeat_of` | loudness contours | segments whose audio is already kept from another cut are skipped | cleanest file first |
| library | `library.py` | judged segments and stills | `voice/clean`, `voice/review`, `face/stills`, `face/photos`, `manifest.json` | content-addressed, never overwrites |
| report | `report.py` | manifest | `inventory.md` | rewritten each run |
| script | `script.py` | scripts in the source | `reading-script.md` | rewritten each run |
| export | `export.py` | library | `elevenlabs-pvc-NN.mp3` at the PVC spec | refuses to overwrite |
| twin check | `twin.py` | one recording | ready / reshoot, per HeyGen rejection reason | pure |
| evaluate | `evaluate.py` | real and cloned clips | speaker-similarity verdict, blind A/B pack and score | pack refuses to overwrite |

## Decisions worth knowing

- **Faces run on onnxruntime, not the insightface package.** insightface 0.7.3 needs a C++ compiler on Windows for Python 3.12. `faceonnx.py` reproduces its detection, alignment, embedding and pose; `tests/test_engine.py` checks parity (identical embeddings, boxes within a pixel, pose within 0.01 degrees) wherever insightface is installed. The models (buffalo_l) download once and are sha256 checked.
- **A music bed is found in the pauses.** Segments are judged on what sits between words: room tone in a clean voiceover, music under an edit. Pauses louder than -45 dBFS mean a bed even when it runs under the whole file.
- **Clipping is flat-topped runs at the file's own rate.** Resampled decodes overshoot on healthy audio; counting samples near full scale there flags nothing real.
- **Repeats are found acoustically.** Tall and wide cuts share audio, but transcription splits it differently each time, so text matching misses repeats. Loudness contours correlate at 0.9 or above only for the same audio.
- **Identity defaults to the dominant face in the approved source**, so the gallery never reads a folder Krish has not approved. It refuses rather than guesses when two identities are close in size.
- **Separated audio is never clean.** Demucs is not used to rescue music-bedded speech: its artifacts would be learned as part of the voice.

## Runtime folders

krish-clone follows the shared Make Your Mind Up layout (`config/studio.json`, read through content-watcher's `layout`, with content-engine's copy winning when it sits beside this clone):

- the clone: `local_roots.repos` with `{repo}` = `krish-clone`, i.e. `C:\Users\krish\dev\makeyourmindup\krish-clone`, beside content-engine, content-watcher and the rest;
- the runtime: `local_roots.runtime` + `krish-clone`, i.e. `%LOCALAPPDATA%\makeyourmindup\krish-clone\`, holding `venv/`, `models/` (buffalo_l, ECAPA), `cache/` (measures per file) and `masters/` (48 kHz mono masters segments are cut from). `KRISH_CLONE_HOME` overrides it.

The library itself lives in the synced Drive folder.
