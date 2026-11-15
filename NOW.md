---
repo: krishanraja/krish-clone
product: krish-clone (voice and likeness training library)
as_of: 2026-11-15
head: 507670c
lifecycle: building
production_url: none (runs on Krish's own machines)
state_doc: README.md
history_log: docs/history/now-notes/
truth_files: [docs/NORTH_STAR.md, config/sources.json, docs/STRATEGY.md]
authority_order: [docs/NORTH_STAR.md, AGENTS.md, docs/STRATEGY.md, README.md]
steward: https://github.com/krishanraja/ai-harness/blob/main/docs/steward/RUNBOOK.md
---

# krish-clone: where it is right now

## What it is

The engine that builds Krish's voice and likeness training library from his own recordings and photos, on his own machine, exports it in each platform's format and judges the clones that come back. See `README.md`; the reasoning is in `docs/STRATEGY.md`.

## Where it is right now (as of 2026-11-15)

<!-- north-star-state {"week_of":"2026-11-09","week_target":null,"current":null,"current_as_of":null,"current_source":null,"urgency":4,"urgency_reason":"North Star not set; Krish sets it"} --> **North Star number: U4, not measured.** The North Star is not set (`docs/NORTH_STAR.md`; a proposal waits on Krish), so there is no number yet.

- Open Generative AI (Anil-matcha, commit fd7dd92) was evaluated and not adopted: it is a studio over the MuAPI aggregator reaching the same model families Higgsfield already does, any identity work would send his face to a new processor, and its local engines hold no identity (`docs/GENERATORS.md`). The gap it exposed is closed in code: `clone likeness` judges any generator's stills or video against his own photos for fidelity, drift within a clip and the face staying in shot, uploads nothing, and was tested on synthetic faces only. Nothing installed from it, no ElevenLabs or HeyGen call, no upload, no spend; 57 tests pass. (2026-11-15)
- `config/synthetic-approvals.json` is the registry of synthetic voices and likenesses Krish has approved, and it holds three, each approved on his own say-so on 2026-11-15 with his exact words: `krish-voice-elevenlabs` (the ElevenLabs voice "Krish Remix", not the older voice named "Krish"), `krish-avatar-heygen` (the HeyGen avatar group "Krish Raja") and `krish-voice-heygen` (its voice "Krish Voice"). Krish approves a synthetic voice or likeness of himself on his own say-so, so no listening panel is required (Ruling, Krish, 2026-11-15); each finished piece made with these still comes to him before it goes out. Each entry names its basis (`own_say_so`, or `scored_record` for the optional panel route), the platform's own name and its id in `platform_ref`, a reference and never a secret, held to the shape of that platform's ids; clone names still refuse an id shape. `approved_sha256` is the sha256 of a canonical description of exactly what he approved, which any reader can recompute (`docs/REGISTRY.md`). `clone registry add` takes either route. The listening panel (`clone abpanel`, `clone abrecord`, `clone abscore --record`) stays as an optional tool (`docs/EVALUATION.md`). No ElevenLabs or HeyGen call, nothing trained, uploaded, sent or spent; 47 tests pass. (2026-11-15)
- the branch sweep takes an approved list (branch@sha) on a hand run and deletes each named branch only at that exact commit, skipping and logging anything else; the weekly run is unchanged. Copied from ai-harness's canonical script and workflow. (2026-11-15)
- A weekly branch sweep (`.github/workflows/branch-sweep.yml`, Sunday 03:17 UTC, and by hand) deletes every remote branch whose work is already on main and lists each branch it keeps with why: unmerged work, an open pull request, protected (Ruling, Krish, 2026-11-15). The script is `.github/scripts/branch_sweep.py`, copied unchanged from ai-harness, which holds the canonical copy. (2026-11-15)
- `config/sources.json` holds a new approved source, `library`, the library folder's own recordings, with Krish's words of 2026-11-14 ("I approve 5.7, add the library source"). Inventory only: nothing uploaded, cloned or spent, no ElevenLabs or HeyGen call. No other source changed. (2026-11-14)
- closeout notes now fold into NOW.md on the default branch (.github/workflows/closeout-fold.yml runs the harness's own fold, after checking the hook is the ai-harness copy by sha256). (2026-11-14)
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

## What changed recently

- 2026-11-15 the likeness test is how any new image or video generator is now judged against the current HeyGen route before it joins it.
- 2026-11-14 Krish approved the library folder's own recordings as a source (decision 5.7), inventory only; the runbook gives the inventory command.
- 2026-11-14 Stranded work landed (the raw audio dump of 31 Oct, the photo-seed rubric of 13 Nov); NOW.md and the runbook say what the library holds and give the exact home-computer commands.
- 2026-11-13 Photo seeds for HeyGen looks: ten current, sharp, single-subject photos at the top of `Photos`, judged against HeyGen's photo guidance (`docs/CAPTURE.md` section 3).
- 2026-10-29 First build, and the first source (`episodes`, the 3 Posts folder) approved by Krish.
- The closeout notes behind these lines are kept verbatim in `docs/history/now-notes/`.

## What is next and what is waiting on Krish

- Next (2026-11-15): on a home computer, run `clone likeness` on an existing HeyGen video of the "Krish Raja" avatar against the seed photos (`docs/RUNBOOK.md`, step 5) to set the current route's baseline.
**Next action: the free local evaluation, on a home computer.** It reads face and voice media, so it runs only on Krish's machine; a cloud session never touches those files. The exact commands are in `docs/RUNBOOK.md`, "Next: the free local evaluation":

1. Install or update, then `clone doctor`.
2. Inventory, then harvest, the two approved sources (`episodes`, `inbox`).
3. `clone twincheck` on each of the two phone takes, against the headshots.
4. `clone evaluate`: his own spread from the harvested clips, and any clone audio judged against it.

The recordings that sit in the library itself (the two "Krish Voice Clone" recordings, the phone takes, the long raw WAV) are not inside an approved source, so inventory and harvest of them wait for that folder to be approved as a source, which only Krish does; `twincheck` and `evaluate` need no source.

Spend stays behind Krish's yes, asked for when it happens: the ElevenLabs Professional Voice Clone upload and the HeyGen likeness (twin or photo looks).

Also Krish's: the North Star.

- North Star check (2026-11-15): holds.
