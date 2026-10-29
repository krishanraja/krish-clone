# krish-clone: where it is right now

## What it is

The engine that builds Krish's voice and likeness training library from his own recordings and photos, on his own machine, exports it in each platform's format and judges the clones that come back. See `README.md`; the reasoning is in `docs/STRATEGY.md`.

## Where it is right now (as of 2026-10-29)

**North Star: not set** (`docs/NORTH_STAR.md`; a proposal waits on Krish).

- **Built and merged to main:** sources gate, voice and face measurement with caching, auto identity gallery, acoustic repeat detection, library, inventory, reading script, ElevenLabs export, HeyGen twin pre-flight, evaluation and blind A/B. 28 tests pass; CI runs them.
- **Approved source:** `episodes`, the 3 Posts folder (Krish, 2026-10-29). Everything else is pending.
- **Proved in a cloud session on real samples** (two audio files, three photos, a test video built from them, rehearsed through an approved source twice): numbers in `docs/EVALUATION.md` and `docs/STRATEGY.md`. Not yet run on the full 3 Posts folder.
- **Reading script built** from 21 of his scripts: 8,043 unique words, about 54 minutes, plus free talk to 75.
- **No credits spent.** The existing "Krish" voice on ElevenLabs scores 0.41 against his real voice (his own clips: 0.74 to 0.84).

## What is next and what is waiting on Krish

- **Next action (Krish, home computer):** `scripts\install-krish-clone.ps1`, then `scripts\run-first-sources.ps1`; read `inventory.md` before saying yes to the harvest.
- **Waiting on Krish:** the voice session (`reading-script.md`) and the twin take (`docs/CAPTURE.md`).
- **Waiting on Krish:** the North Star, and whether to approve the next source (proposed: camera, the raw phone video).
