# krish-clone

This repository builds the training library for Krish's voice clone (ElevenLabs) and likeness (HeyGen). `NOW.md` says where it stands; `docs/STRATEGY.md` says why it is shaped this way and what is still missing.

## North Star: read it first, every session

[`docs/NORTH_STAR.md`](docs/NORTH_STAR.md). It is not set yet: only Krish sets it. Say which part of it a task moves before starting, and close by noting what moved.

## Rules

- Local-first. Face and voice media never enter git, never go to a cloud service, and never leave Krish's machines except into his own Drive library folder.
- Read only sources Krish has approved in `config/sources.json`, one at a time. Never change a source's status on his behalf.
- No spend. Every ElevenLabs or HeyGen call (clone, upload, generation) needs Krish's approval immediately before it.
- Never overwrite or delete library files; the library is content-addressed and idempotent.
- No em dashes anywhere, code comments included.
- This repository is public. Only code and documentation are committed; the library, reading script, exports and caches stay on Krish's machines and Drive.

Run tests with:

```sh
python -m unittest discover -s tests -t . -v
```
