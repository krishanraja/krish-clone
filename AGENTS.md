# krish-clone

This repository builds the training library for Krish's voice clone (ElevenLabs) and likeness (HeyGen). `NOW.md` says where it stands; `docs/STRATEGY.md` says why it is shaped this way and what is still missing.

<!-- north-star:start -->
## North Star: read it first, every session

[`docs/NORTH_STAR.md`](docs/NORTH_STAR.md). It is not set yet: only Krish sets it. Say which part of it a task moves before starting, and close by noting what moved. The state line, the first line under "Where it is right now" in `NOW.md`, says U4 until he sets a number ([the harness contract](https://github.com/krishanraja/ai-harness/blob/main/contract/north-star-metric.md)).
<!-- north-star:end -->

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

Close out: before a session that changed the repository ends, write `now-notes/YYYY-MM-DD-<slug>.md` with `Status:`, `Next:` and the line `North Star check (YYYY-MM-DD): holds.` with nothing in front of it; it folds into `NOW.md` on main.
