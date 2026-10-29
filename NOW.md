# krish-clone: where it is right now

## What it is

The engine that builds Krish's voice and likeness training library from his own recordings and photos, on his own machine, so ElevenLabs and HeyGen are trained on the best material he has and the gaps are measured. See `README.md`; the reasoning is in `docs/STRATEGY.md`.

## Where it is right now (as of 2026-10-29)

**North Star: not set** (`docs/NORTH_STAR.md`; a proposal is waiting on Krish).

- **Built** (first commit): sources gate, voice judge, face judge with ArcFace identity and pose, library writer, inventory report, `clone` command. 19 tests pass on generated media.
- **Run on real samples in a cloud session**: two audio files, three photos, one test video built from them. Results in `docs/STRATEGY.md`. Not yet run on any full source.
- **Every source is pending** in `config/sources.json`. Nothing has been read beyond the samples above.
- **No credits spent** on ElevenLabs or HeyGen.

## What is next and what is waiting on Krish

- **Waiting on Krish:** approve the first source (`clone sources approve episodes --local-path ...`) on a home computer, one at a time. Proposed order: episodes, photos-headshots, photos-faces; then decide on the three proposed raw phone folders.
- **Waiting on Krish:** the North Star.
- **Next action:** install on one home computer and run `clone inventory` on the episodes folder to replace the 20 to 40 clean-minute estimate with a number.
- **Then:** the capture kit (reading script, twin shot list), and vendoring VoiceStudio's Apache-2.0 eval kit for phase 4.
