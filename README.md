# krish-clone

Builds a voice and likeness training library from Krish's own recordings and photos, on his own machine, so an ElevenLabs Professional Voice Clone and a HeyGen avatar can be trained from the best material he already has, and the gaps are measured rather than guessed.

Nothing is sent to ElevenLabs or HeyGen by this engine. Training calls come later, each behind Krish's approval at the moment of the call (`docs/STRATEGY.md`, phase 4).

## What it does

| Stage | Module | What it decides |
|---|---|---|
| sources | `krish_clone/sources.py`, `config/sources.json` | Which Drive folders may be read. Every source starts `pending`; only Krish approves one. |
| voice | `krish_clone/voice.py` | Sentence-bounded segments of 3 to 30 s, judged on what sits in their own pauses: a music bed, noise, clipping, length, and (with the `speaker` extra) whether it is Krish's voice. Tiers: clean, review, rejected, each with reasons. |
| face | `krish_clone/face.py` | Frames and photos where Krish's face is large, sharp, well lit, whole, facing roughly forward and verified as him (ArcFace, insightface `buffalo_l`); then a spread of head poses with near-duplicates dropped. |
| library | `krish_clone/library.py` | Writes `voice/clean`, `voice/review`, `face/stills`, `face/photos` and `manifest.json`. Content-addressed names; never overwrites, never deletes. |
| report | `krish_clone/report.py` | `inventory.md`: clean minutes against 30 and 120, face stills, poses covered, why material was rejected. |

It reuses content-watcher (transcription, loudness, frame hashing, ffmpeg helpers) rather than copying it. Attributions are in `NOTICE.md`.

## Use

```sh
pip install -e ../content-watcher
pip install -e ".[voice,face,speaker]"

clone sources                                   # what may be read, and its status
clone sources approve episodes --local-path "G:/My Drive/.../Content"   # Krish only
clone inventory "G:/My Drive/.../Content" --source episodes --out "G:/My Drive/.../Clone library" \
  --gallery photos/krish-*.jpg --enrol clips/krish-clean.wav
clone harvest   ... same arguments ...          # also writes the segments and stills
```

`inventory` measures and writes only `manifest.json` and `inventory.md`. `harvest` also writes the media. `--sample` reads a one-off test file outside any source.

## Tests

```sh
python -m unittest discover -s tests -t . -v
```

Tests use generated tones, noise and synthetic images with stub detectors, so no face or voice of Krish's ever enters the repository. `.gitignore` refuses media files.
