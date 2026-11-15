# The registry of approved synthetic voices and likenesses

`config/synthetic-approvals.json` records each synthetic voice or likeness of Krish that he has approved: one entry per approved clone, holding his exact words, the date he said them and the sha256 of the scored A/B record he approved. Nothing else may use a synthetic Krish. content-engine's `ve lint` row `voice.synthetic` reads this file live and refuses any spec that uses a synthetic Krish voice or likeness without a matching entry.

This repository is public, so the registry holds names and hashes only: never a platform's voice or avatar id, a key, or anything that grants access. The reader refuses a field the format does not name, and a clone name shaped like a platform id.

## Format: `krish-clone.synthetic-approvals/1`

```json
{
  "format": "krish-clone.synthetic-approvals/1",
  "note": "...",
  "approvals": [
    {
      "name": "krish-voice-1",
      "kind": "voice",
      "platform": "elevenlabs",
      "scored_pack_sha256": "<64 lowercase hex>",
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
| `name` | Required. Lowercase words joined by hyphens (`krish-voice-1`), unique. A new clone takes a new name. No segment of 16 characters or more, which would read as a platform id. |
| `kind` | Required. `voice` or `likeness`. |
| `platform` | Required. A voice comes from `elevenlabs`, a likeness from `heygen`. The platform's name, never an id there. |
| `scored_pack_sha256` | Required, unique. The sha256 of the record `clone abscore --record` wrote (the file's bytes), which binds the pack's clips, the key, the panel, the answers and the score. |
| `approved_words` | Required. Krish's exact words approving that record, never a paraphrase. |
| `approved_on` | Required. The date he said them, never before the record was scored. |
| `score` | Optional. Copied from the record when it is added: `listeners`, `pairs`, `picked_the_clone`, `verdict`. |
| `withdrawn` | Optional. His words and the date he took the approval back. The entry stays as history and never matches again. |

Anything malformed refuses the whole registry: a reader never guesses which entries are good.

## Reading it from another repository

Read it live from main, never from a copy:

- **Raw GitHub at main** (what content-engine uses, with `curl -fsSL`, as its `scripts/post-pack/voice_score.mjs` reads ai-harness): `https://raw.githubusercontent.com/krishanraja/krish-clone/main/config/synthetic-approvals.json`. No token is needed because the repository is public. GitHub caches the raw file for up to five minutes (`cache-control: max-age=300`), so an approval merged to main reaches a reader within about five minutes.
- **The GitHub API** works too, uncached: `https://api.github.com/repos/krishanraja/krish-clone/contents/config/synthetic-approvals.json?ref=main`, whose `content` is the file in base64.

A reader must:

1. Refuse when the file cannot be read or is not this format. An unreadable registry refuses, it never passes.
2. Match a use on `name`, `kind` and `platform`, ignoring any entry with `withdrawn`.
3. Require the consumer's own approval record to carry the entry's `scored_pack_sha256`, `approved_words` and `approved_on` exactly. In content-engine that is the spec's `approvals` entry with `gate: "synthetic"`, `by: "Krish"`, `said`, `on` and `artifact_hash`.

The Python reader here is `krish_clone/registry.py` (`parse`, `load`, `find`); content-engine keeps its own small reader in `scripts/velib/lint.py`, because it cannot import this package.

## Adding and withdrawing

Only with Krish's words in hand, after he has read the record's score and its sha256:

```sh
clone registry add --record <record.json> --words "<his exact words>" --on YYYY-MM-DD
clone registry withdraw <name> --words "<his exact words>" --on YYYY-MM-DD
clone registry list
clone registry check
```

`add` refuses a record that does not meet the bar: a failing verdict, fewer than 10 listeners or 10 pairs, or a listener list he had not approved (`docs/EVALUATION.md`). The change is a commit to this repository; it counts once it is on main.
