# krish-clone: where it is right now

## What it is

The engine that builds Krish's voice and likeness training library from his own recordings and photos, on his own machine, exports it in each platform's format and judges the clones that come back. See `README.md`; the reasoning is in `docs/STRATEGY.md`.

## Where it is right now (as of 2026-11-14)

**North Star: not set** (`docs/NORTH_STAR.md`; a proposal waits on Krish).

- **Built and merged to main:** sources gate, voice and face measurement with caching, auto identity gallery, acoustic repeat detection, library, inventory, reading script, ElevenLabs export, HeyGen twin pre-flight, evaluation and blind A/B, and the raw audio dump (`scripts/dump-raw-audio.ps1`). 28 tests pass; CI runs them.
- **Approved sources:** `episodes`, the 3 Posts folder (Krish, 2026-10-29), and `inbox`, the Video Engine Inbox of raw takes (Krish, 2026-10-31). Everything else is pending.
- **The recordings and photos exist.** The library folder on Drive (`Krish Clone - Assets`, read by name and count on 2026-11-14, no file opened) holds:
  - `Video`: two phone takes (2026-10-31).
  - `voice/uncompressed`: the two "Krish Voice Clone" recordings and 31 WAVs, one per raw Inbox take (2026-10-31; the dump has run, its `raw-dump.csv` is in `voice/Krish Voice Corpus`).
  - `voice/compressed`: 33 M4A copies of those (2026-11-07).
  - `voice/archive`: one long raw WAV, about 400 MB (2026-11-06), and one interview MP3.
  - `voice/Krish Voice Corpus`: his written corpus and manifests for the reading script.
  - `Photos`: six headshots made on 2026-11-13 at the top, with three older photos; everything else in `Photos/All other photos` (rubric: `docs/CAPTURE.md` section 3).
- **Proved in a cloud session on real samples** (two audio files, three photos, a test video built from them): numbers in `docs/EVALUATION.md` and `docs/STRATEGY.md`.
- **Reading script built** from 13 of his long scripts and transcripts: 7,057 unique words, about 47 minutes, plus free talk to 75.
- **No credits spent.** The existing "Krish" voice on ElevenLabs scores 0.41 against his real voice (his own clips: 0.74 to 0.84).

## What is next

**Next action: the free local evaluation, on a home computer.** It reads face and voice media, so it runs only on Krish's machine; a cloud session never touches those files. The exact commands are in `docs/RUNBOOK.md`, "Next: the free local evaluation":

1. Install or update, then `clone doctor`.
2. Inventory, then harvest, the two approved sources (`episodes`, `inbox`).
3. `clone twincheck` on each of the two phone takes, against the headshots.
4. `clone evaluate`: his own spread from the harvested clips, and any clone audio judged against it.

The recordings that sit in the library itself (the two "Krish Voice Clone" recordings, the phone takes, the long raw WAV) are not inside an approved source, so inventory and harvest of them wait for that folder to be approved as a source, which only Krish does; `twincheck` and `evaluate` need no source.

Spend stays behind Krish's yes, asked for when it happens: the ElevenLabs Professional Voice Clone upload and the HeyGen likeness (twin or photo looks).

Also Krish's: the North Star.
