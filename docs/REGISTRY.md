# The registry of approved synthetic voices and likenesses

`config/synthetic-approvals.json` records each synthetic voice or likeness of Krish that he has approved: one entry per approved clone, holding his exact words, the date he said them and the sha256 of exactly what he approved. Nothing else may use a synthetic Krish. content-engine's `ve lint` row `voice.synthetic` reads this file live and refuses any spec that uses a synthetic Krish voice or likeness without a matching entry.

Krish approves a synthetic voice or likeness of himself on his own say-so; no listening panel is required (Ruling, Krish, 2026-11-15: "I will approve this by myself - I am me so my say so goes here"). That is the `own_say_so` basis. The blind A/B listening panel stays as an optional route, the `scored_record` basis (`docs/EVALUATION.md`). Either way each finished piece made with a clone still comes to him before it goes out.

## What it holds now

| Name | Kind | Platform | The platform's name | `platform_ref` | Approved |
|---|---|---|---|---|---|
| `krish-voice-elevenlabs` | voice | elevenlabs | Krish Remix | `FOupAntbAMhJ9n9Q4dfC` | 2026-11-15, own say-so |
| `krish-avatar-heygen` | likeness | heygen | Krish Raja (the avatar group, 15 looks) | `fa0069900c1049acbadc045c7866cdc5` | 2026-11-15, own say-so |
| `krish-voice-heygen` | voice | heygen | Krish Voice (the avatar's default voice) | `76d9dedcfa2d4f628beb43090e74e473` | 2026-11-15, own say-so |
| `krish-voice-elevenlabs-v2` | voice | elevenlabs | Krish v2 | `EWMCMyM8o9ZcYCijk7nx` | 2026-11-17, own say-so; his best narration voice so far |
| `krish-still-higgsfield-1` | likeness | higgsfield | Headshot 1, colour-corrected (round 2 bank) | `b1684a272ba1c0151202f5a3799aba9241a09fcfd02ac9843458b4796fdb63c9` | 2026-11-18, own say-so |
| `krish-still-higgsfield-3` | likeness | higgsfield | Headshot 3, colour-corrected (round 2 bank) | `04ba73f8fb1432188657c9362051231d01d4a1e74828e6d462ecc28dc7aad8ce` | 2026-11-18, own say-so |
| `krish-still-higgsfield-4` | likeness | higgsfield | Headshot 4, colour-corrected (round 2 bank) | `f92390dc5ae042d46a61f83bf210f79d5aee1bc28b3331fb0a7269a962346bff` | 2026-11-18, own say-so |
| `krish-still-higgsfield-6` | likeness | higgsfield | Headshot 6, colour-corrected (round 2 bank) | `c977de98edcf92de9a959061479c274c869f7732bb9344a48366349119295e08` | 2026-11-18, own say-so |
| `krish-still-higgsfield-5` | likeness | higgsfield | Headshot 5, loft window, three-quarter (round 4, variant A) | `2a312e8f7469017d1585928d715a198d287a2f9d8f1216cb341dcc83f99eb377` | 2026-11-18, own say-so |
| `krish-still-higgsfield-1-shoulders` | likeness | higgsfield | Headshot 1 with broader shoulders, in between (round 5) | `272152829a05fac72b01579a190608f94642116fdb0fdb5d788c3dd65d8fbcaf` | 2026-11-18, own say-so |

For covers, `krish-still-higgsfield-1-shoulders` is the version of headshot 1 to use (Krish, 2026-11-18: "Image 1 could also benefit from broader shoulders"); the original `-1` stays approved and is not withdrawn.


**His best narration voice so far is `krish-voice-elevenlabs-v2`, "Krish v2"** (Krish, 2026-11-17: "this is the best choice thus far in terms of voice ID and your usage of it"). It is an ElevenLabs Voice Remix of Krish Remix for softer, glottal T's, used on `eleven_v3` with audio tags and sped up 15% after rendering (`docs/GENERATORS.md`). Krish Remix stays approved and is not withdrawn; his workspace now names it "Backup - Krish Remix", and the entry keeps the name he approved.

The older cloned voice named "Krish" in his ElevenLabs workspace is not approved (it scores 0.41 against his real voice, `docs/EVALUATION.md`); the approved ElevenLabs voice is the one with id `FOupAntbAMhJ9n9Q4dfC`, named "Krish Remix" there (Ruling, Krish, 2026-11-15).

## Platform ids are references, not secrets

This repository is public. A platform's voice or avatar id does nothing without the account's own key, so it may be recorded, in its own field, `platform_ref`, and only there. Keys, tokens and anything else that grants access never enter the registry. The reader holds every `platform_ref` to the shape of that platform's ids, which no key has: an ElevenLabs voice id is 20 letters and digits, a HeyGen avatar group or voice id 32 lowercase hex characters. A clone's registry `name` is never shaped like an id: no segment of it may be 16 characters or more.

## Format: `krish-clone.synthetic-approvals/1`

```json
{
  "format": "krish-clone.synthetic-approvals/1",
  "note": "...",
  "approvals": [
    {
      "name": "krish-voice-elevenlabs",
      "kind": "voice",
      "platform": "elevenlabs",
      "basis": "own_say_so",
      "platform_name": "Krish Remix",
      "platform_ref": "FOupAntbAMhJ9n9Q4dfC",
      "approved_sha256": "e2e0cbaea9545a5e455cc60e4d77f3b8906b4c9c7a977efb330a579f5de4f9d1",
      "approved_words": "<Krish's exact words>",
      "approved_on": "2026-11-15"
    },
    {
      "name": "krish-voice-1",
      "kind": "voice",
      "platform": "elevenlabs",
      "basis": "scored_record",
      "approved_sha256": "<64 lowercase hex: the scored record's bytes>",
      "approved_words": "<Krish's exact words>",
      "approved_on": "YYYY-MM-DD",
      "score": {"listeners": 12, "pairs": 10, "picked_the_clone": 0.52, "verdict": "pass"},
      "withdrawn": {"words": "<Krish's exact words>", "on": "YYYY-MM-DD"}
    }
  ]
}
```

| Field | Rule |
|---|---|
| `name` | Required. The registry's own name for the clone: lowercase words joined by hyphens (`krish-voice-elevenlabs`), unique. A new clone takes a new name. No segment of 16 characters or more, which would read as a platform id. |
| `kind` | Required. `voice` or `likeness`. |
| `platform` | Required. A voice comes from `elevenlabs` or `heygen`, a likeness from `heygen` or `higgsfield`. A `higgsfield` likeness is one generated still: its `platform_ref` is the sha256 of that exact file, so a changed or re-encoded still is not approved. |
| `basis` | Required. `own_say_so` (his say-so on the clone itself) or `scored_record` (his approval of a scored listening-panel record). |
| `approved_sha256` | Required, unique, 64 lowercase hex. The sha256 of exactly what he approved: for `own_say_so`, the canonical description below; for `scored_record`, the bytes of the record `clone abscore --record` wrote, which binds the pack's clips, the key, the panel, the answers and the score. |
| `approved_words` | Required. Krish's exact words approving it, never a paraphrase. |
| `approved_on` | Required. The date he said them; for a scored record, never before it was scored. |
| `platform_name` | Required with `own_say_so`, and only there. The platform's own name for the clone, as its workspace shows it. |
| `platform_ref` | Required with `own_say_so`, and only there. The platform's id for the clone: a reference, not a secret (above). |
| `score` | Optional with `scored_record`, and only there. Copied from the record when it is added: `listeners`, `pairs`, `picked_the_clone`, `verdict`. |
| `withdrawn` | Optional. His words and the date he took the approval back. The entry stays as history and never matches again. |

Anything malformed refuses the whole registry: a reader never guesses which entries are good.

### The canonical description (`own_say_so`)

What he approved is described as a JSON object of exactly four keys, `kind`, `platform`, `platform_name` and `platform_ref`, sorted, with no spaces, in UTF-8; `approved_sha256` is its sha256. Any reader can recompute it from the entry, and the reader here refuses an entry whose hash does not match. For the ElevenLabs voice:

```sh
printf '%s' '{"kind":"voice","platform":"elevenlabs","platform_name":"Krish Remix","platform_ref":"FOupAntbAMhJ9n9Q4dfC"}' | sha256sum
# e2e0cbaea9545a5e455cc60e4d77f3b8906b4c9c7a977efb330a579f5de4f9d1
```

In Python it is `registry.subject(kind, platform, platform_name, platform_ref)` and `registry.subject_sha256(...)`.

## Reading it from another repository

Read it live from main, never from a copy:

- **Raw GitHub at main** (what content-engine uses, with `curl -fsSL`, as its `scripts/post-pack/voice_score.mjs` reads ai-harness): `https://raw.githubusercontent.com/krishanraja/krish-clone/main/config/synthetic-approvals.json`. No token is needed because the repository is public. GitHub caches the raw file for up to five minutes (`cache-control: max-age=300`), so an approval merged to main reaches a reader within about five minutes.
- **The GitHub API** works too, uncached: `https://api.github.com/repos/krishanraja/krish-clone/contents/config/synthetic-approvals.json?ref=main`, whose `content` is the file in base64.

A reader must:

1. Refuse when the file cannot be read or is not this format. An unreadable registry refuses, it never passes.
2. Match a use on `name`, `kind` and `platform`, ignoring any entry with `withdrawn`.
3. Require the consumer's own approval record to carry the entry's `approved_sha256`, `approved_words` and `approved_on` exactly. In content-engine that is the spec's `approvals` entry with `gate: "synthetic"`, `by: "Krish"`, `said`, `on` and `artifact_hash`.
4. Require no `score` and no scored record: an `own_say_so` entry has neither.

The Python reader here is `krish_clone/registry.py` (`parse`, `load`, `find`); content-engine keeps its own small reader in `scripts/velib/lint.py`, because it cannot import this package.

## Adding and withdrawing

Only with Krish's words in hand. On his own say-so, naming the clone exactly as its platform shows it:

```sh
clone registry add <name> --kind voice --platform elevenlabs --platform-name "<the platform's name>" \
  --platform-ref <the platform's id> --words "<his exact words>" --on YYYY-MM-DD
```

Or, on the optional route, after he has read a scored record's score and its sha256:

```sh
clone registry add --record <record.json> --words "<his exact words>" --on YYYY-MM-DD
```

And:

```sh
clone registry withdraw <name> --words "<his exact words>" --on YYYY-MM-DD
clone registry list
clone registry check
```

`add --record` refuses a record that does not meet the bar: a failing verdict, fewer than 10 listeners or 10 pairs, or a listener list he had not approved (`docs/EVALUATION.md`). Either `add` refuses a name already in the registry and a hash already approved. Nothing here calls ElevenLabs or HeyGen: the ids are recorded as he gave them. The change is a commit to this repository; it counts once it is on main.
