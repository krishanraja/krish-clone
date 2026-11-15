# Evaluation: deciding "indistinguishable" by evidence

## Speaker similarity (`clone evaluate`)

ECAPA speaker embeddings (SpeechBrain, Apache-2.0). The bar is real Krish against real Krish (leave one out): the clone passes when its median similarity reaches the 5th percentile of that spread.

Calibration on 2026-10-29 (all scores are cosine similarity to Krish's centroid):

| Audio | Scores |
|---|---|
| Krish, clean segments (leave one out) | 0.74 to 0.84 |
| Krish under a music bed, 10 s chunks | 0.66 to 0.82 |
| Ten stock male voices (ElevenLabs previews, American, British, Australian, Turkish) | -0.24 to 0.20 |
| **The existing "Krish" voice already in his ElevenLabs workspace** | **0.41: fail** |

So the speaker floor used to reject other voices from the library (0.45) sits in the empty gap, and the clone already on the account measurably does not sound like him to a model. That is the baseline the Professional Voice Clone must beat.

## Face identity

ArcFace (buffalo_l). Calibration on 2026-10-29: three photos of Krish against their own centroid 0.85 to 0.89; seven strangers (insightface's sample photos) -0.07 to 0.06. The identity floor is 0.55, contentarchives' threshold measured on his own library.

## Blind A/B (`clone abpack`, `clone abscore`)

Optional. Krish approves a synthetic voice or likeness of himself on his own say-so; no listening panel is required (Ruling, Krish, 2026-11-15; "What Krish approves" below). The A/B and the panel stay as tools for when he wants evidence beyond his own ear.

Pairs of one real and one cloned clip, shuffled into A and B, with the key written beside the pack, never inside it. People who know Krish mark which one is generated. Pass: they pick the clone in at most 60% of pairs. The score also reports the chance of doing that well by guessing, and each listener's rate.

Run it with at least 10 listeners and 10 pairs; fewer cannot tell 60% from chance.

## The listening panel, optional (`clone abpanel`, `clone abrecord`, `clone abscore --record`)

Each listener gets their own page: the same pairs in their own order, each pair's two clips as 1 and 2 in their own order, so no two listeners can compare notes. The pages are made later, through SendLinks, one link per listener, and only once Krish has approved the listener list.

The listener list names real people, so it lives only on Krish's machines or Drive (beside the pack, in the runtime folder), never in this repository:

```json
{
  "format": "krish-clone.listeners/1",
  "listeners": [{"id": "L01", "name": "..."}, {"id": "L02", "name": "..."}],
  "approval": {"words": "<Krish's exact words>", "on": "YYYY-MM-DD"}
}
```

At least 10 listeners, each with an id `L01` upwards. `approval` stays out until he gives it; adding it later does not change the list's digest, so a panel built before it still matches. The panel, the answers and the record name listeners by id only.

```powershell
clone abpack --real <10+ real clips> --clone <10+ clone clips> --out <ab>
clone abpanel --key <ab>\KEY-do-not-share.json --listeners <listeners.json> --out <ab>\panel
# each listener's folder <ab>\panel\L01 ... becomes their page; they fill in sheet.csv (1 or 2 per pair)
clone abrecord --panel <ab>\panel --listener L01 --sheet <their filled sheet.csv>
clone abscore --key <ab>\KEY-do-not-share.json --answers <ab>\panel\answers.csv --record <ab>\record.json `
  --panel <ab>\panel --clone-name krish-voice-1 --kind voice --platform elevenlabs
```

`abrecord` refuses a sheet with a pair missing or answered other than 1 or 2, and a listener recorded twice. `abscore --record` refuses unless at least 10 listeners each answered every one of at least 10 pairs exactly once, the key and the list are the ones the panel was built from, and Krish approved the list. It never overwrites a record. It prints the record's sha256: on this route, that is what Krish approves, and what the registry holds as `approved_sha256` (`docs/REGISTRY.md`).

## What Krish approves

Each is asked for on its own, immediately before it happens, and an approval never carries to the next step.

1. **The clone, on his own say-so.** Krish approves a synthetic voice or likeness of himself on his own say-so; no listening panel is required (Ruling, Krish, 2026-11-15: "I will approve this by myself - I am me so my say so goes here"). Ask which clone, by the name his workspace shows and its id there. `clone registry add <name> --kind ... --platform ... --platform-name ... --platform-ref ... --words ... --on ...` writes his exact words, the date and the sha256 of exactly what he approved into `config/synthetic-approvals.json` (`docs/REGISTRY.md`), and only once that is on main may content-engine use the clone. On 2026-11-15 he approved the ElevenLabs voice "Krish Remix", the HeyGen avatar "Krish Raja" and its voice "Krish Voice"; the older ElevenLabs voice named "Krish" is not approved.
2. **Each training or generation call, one at a time.** Each is spend, so each is asked for separately: an upload to train or retrain a clone (the files, the name it will carry, its cost), and each generation (the words, which clone, how many, the credits).
3. **Each finished piece.** Every piece made with an approved clone still comes to him before it goes out (Ruling, Krish, 2026-11-15).

### The optional panel route

When he wants a scored blind test as well, these come in order:

1. **The listener list.** The names, and how each knows him. Ask: at least 10 people who know his voice well (for a likeness test, his face and voice), each to be sent one private page of shuffled pairs and asked to mark the generated clip in each. His exact words go in the list's `approval`. Approving the list sends nothing.
2. **Each generation of clone clips for the test**: the sentences, which clone, how many clips, and the credits.
3. **Each page.** One SendLinks link per approved listener, minted and sent only on his yes for that send. SendLinks itself never sends.
4. **The scored record.** He reads the record's score and its sha256 and approves it in his own words. `clone registry add --record` writes those words, the date and the sha256 into the registry with the basis `scored_record`.
