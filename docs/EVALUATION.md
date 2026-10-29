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
