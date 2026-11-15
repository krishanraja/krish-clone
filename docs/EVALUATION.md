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

Pairs of one real and one cloned clip, shuffled into A and B, with the key written beside the pack, never inside it. People who know Krish mark which one is generated. Pass: they pick the clone in at most 60% of pairs. The score also reports the chance of doing that well by guessing, and each listener's rate.

Run it with at least 10 listeners and 10 pairs; fewer cannot tell 60% from chance.

## The listening panel (`clone abpanel`, `clone abrecord`, `clone abscore --record`)

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

`abrecord` refuses a sheet with a pair missing or answered other than 1 or 2, and a listener recorded twice. `abscore --record` refuses unless at least 10 listeners each answered every one of at least 10 pairs exactly once, the key and the list are the ones the panel was built from, and Krish approved the list. It never overwrites a record. It prints the record's sha256: that is what Krish approves, and what the registry holds (`docs/REGISTRY.md`).

## What Krish approves, in order

Each is asked for on its own, immediately before it happens, and an approval never carries to the next step.

1. **The listener list.** The names, and how each knows him. Ask: at least 10 people who know his voice well (for a likeness test, his face and voice), each to be sent one private page of shuffled pairs and asked to mark the generated clip in each. His exact words go in the list's `approval`. Approving the list sends nothing.
2. **Each training call, one at a time.** Each is spend, so each is asked for separately:
   - the ElevenLabs Professional Voice Clone upload: the exact MP3 files from `clone export elevenlabs` (names, minutes, sha256), the name the voice will carry, and its credit or plan cost;
   - the HeyGen Digital Twin upload: the take that passed `clone twincheck`, his consent recording, the name the avatar will carry, and its cost;
   - each generation of clone clips for the test: the sentences, which clone, how many clips, and the credits.
3. **Each page.** One SendLinks link per approved listener, minted and sent only on his yes for that send. SendLinks itself never sends.
4. **The scored record.** He reads the record's score and its sha256 and approves it in his own words. `clone registry add` writes those words, the date and the sha256 into `config/synthetic-approvals.json`, and only once that is on main may content-engine use the clone.
