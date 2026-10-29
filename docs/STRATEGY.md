# Strategy: a clone people who know Krish cannot tell apart

Written 2026-10-29 from every folder Krish named, the code of the three repositories he pointed to, each platform's current guidance, and measured runs on real samples. Numbers are measured unless marked as an estimate.

## The gaps and where each stands

| Gap | Status |
|---|---|
| The episodes are finished edits with music beds; the clone would learn the music | **Handled in code.** Beds are detected in the pauses and rejected; separated audio is never promoted. The approved short measured 0 clean minutes. |
| Not enough clean voice (PVC: 30 min minimum, 1 to 3 hours best) | **Measured by `clone inventory`; closed by Krish's voice session.** Estimate before the first full run: 20 to 40 clean minutes. The reading script is built (`docs/CAPTURE.md`). |
| HeyGen's twin needs its own take, not old footage | **Smaller than first thought:** HeyGen now asks for about 30 seconds, one continuous take, plus a spoken consent code. `clone twincheck` pre-flights it. Closed by one short shoot. |
| No test for "indistinguishable" | **Closed.** Speaker similarity calibrated on real voices; blind A/B pack and scorer. |
| content-watcher's face code cannot pick training stills | **Closed.** ArcFace identity, pose, sharpness, exposure, cut-off, pose-spread selection. |
| insightface needs a compiler on Windows | **Closed.** The same models run on onnxruntime, with checked parity. |
| Tall and wide cuts would double count minutes | **Closed.** Repeats are found acoustically and skipped. |
| Identity needed photos from folders not yet approved | **Closed.** The gallery defaults to the dominant face in the approved source. |
| Thresholds were guesses | **Calibrated** on other voices and other faces (`docs/EVALUATION.md`). |

## A finding worth acting on

The workspace already holds a cloned voice called "Krish". Its free preview scores **0.41** against his real voice, where his own clips score 0.74 to 0.84 and ten other men -0.24 to 0.20. It is not him yet. The Professional Voice Clone from clean audio is the fix; the A/B test is how to know.

## The three repositories

| Repository | Verdict | Why |
|---|---|---|
| contentarchives | Its approach, reused | insightface buffalo_l (ArcFace) over his library with a 0.55 threshold measured on it. It never scored quality; this engine does. |
| cmusatyalab/openface | Replaced, two ideas kept | nn4.small2 (about 93% on LFW), no pose, dlib on Windows. Kept: the largest face is the subject; accept by distance to a gallery. |
| debpalash/VoiceStudio | Ideas only | AGPL. Its pipeline ideas informed this one; SpeechBrain ECAPA (Apache-2.0) does the speaker scoring here. |

## Phases and gates

1. **Inventory** (no spend). `clone inventory` on 3 Posts. Gate: Krish reads `inventory.md`.
2. **Library** (no spend). `clone harvest` into Krish Clone - Assets.
3. **Capture** (no spend). The voice session from `reading-script.md`; the twin take, passed by `clone twincheck`.
4. **Train and judge** (spend, each step approved when it happens). Upload the exported MP3s to a Professional Voice Clone; upload the twin take to HeyGen. Pass: `clone evaluate` passes and at most 60% of listeners pick the clone in the blind A/B.

## Still open, and why

- Only Krish can record the voice session and the twin take, and approve each upload.
- The first full run on 3 Posts happens on a home computer: Drive's connector cannot move videos over 10 MB into a cloud session.
- The North Star is his to set (`docs/NORTH_STAR.md`).
