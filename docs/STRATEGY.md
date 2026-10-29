# Strategy: a clone people who know Krish cannot tell apart

Written 2026-10-29 from a read of every folder Krish named, the code of the three repositories he pointed to, and a measured run on samples. Numbers below are measured unless marked as an estimate.

## The gaps, plainly

1. **The episode folders hold finished edits, not raw footage.** 22 MP4s, about 1.8 GB, across 11 episodes, cut 16x9 and 9x16, with music beds, jump cuts, b-roll, captions and overlays. On the sample run, `Friday-short-approved.m4a` (the approved mix) gave **0 clean minutes**: every pause sits at -24 to -35 dBFS where a quiet room sits below -55. A clone trained on that learns the music as part of the voice. Separating it with Demucs leaves artifacts the clone also learns, so separated audio is never promoted to clean.
2. **HeyGen's Digital Twin is not trained from stills or old clips.** It needs a purpose-shot recording: two minutes or more talking to camera, steady framing and light, plus a spoken consent statement. Old footage and photos set the reference look and can feed a Photo Avatar, which is visibly less real. **This is the biggest gap, and it closes with one 15 minute shoot, not more software.**
3. **Clean voice minutes are short of what a Professional Voice Clone needs.** ElevenLabs' Professional Voice Clone needs about 30 minutes of clean single-speaker audio and does best with one to three hours. Estimate before measuring: 20 to 40 usable minutes across all the edits, most from the voiceover review renders and the "quality evidence" audio. `clone inventory` replaces the estimate with the number. The remedy is one reading session of 60 to 90 minutes: one room, one mic, natural pace, across his range.
4. **"Indistinguishable" has no test yet.** Without one it is an opinion. Phase 4 adds speaker similarity, a face-identity score and a blind A/B pack for 10 people who know him.
5. **content-watcher's face code cannot pick training stills** (Haar on 320 px frames, no identity, no pose, no sharpness). This repository adds those.

## The three repositories

| Repository | Verdict | Why |
|---|---|---|
| contentarchives | Reuse its approach | Already runs insightface `buffalo_l` (ArcFace) over Krish's library, with a 0.55 cosine threshold measured on it and a named Krish cluster. It never scored quality; this engine adds that. |
| cmusatyalab/openface | Replace, borrow two ideas | Still nn4.small2 (about 93% on LFW), no pose or expression, dlib build on Windows. Too weak to tell Krish from a lookalike or to score an avatar. |
| debpalash/VoiceStudio | Patterns and its eval kit, not its code | AGPL app. Its Demucs separation, reference-slice rule and loudnorm are reimplemented ideas; its Apache-2.0 `omnivoice/eval` (speaker similarity, UTMOS, WER) is the phase 4 evaluation kit. |

## Phases, each with a gate

1. **Inventory** (no spend). `clone inventory` on each approved source. Output: clean minutes, face stills and poses, reasons for rejection. Gate: Krish sees the shortfall.
2. **Library** (no spend). `clone harvest` into the Drive library folder.
3. **Capture kit** (no spend). A reading script from his own scripts and vocabulary, and a shot list for the twin recording drawn from what his best stills show about light, angle and framing. Krish records once.
4. **Train and evaluate** (spend, each call approved when it happens). Instant Voice Clone first, then Professional Voice Clone, then the HeyGen Digital Twin. Pass: at most 60% of listeners and viewers pick the clone correctly, and similarity scores sit inside the spread of real Krish against real Krish.

## What the sample run proved (2026-10-29)

On two real audio files, three real photos and one test video built from them, in a cloud session (videos over 10 MB cannot come through the Drive connector, so full runs happen on the home computers):

- Voice: the approved mix was rejected entirely as music-bedded; the candidate WAV gave 0.54 clean minutes (5 segments, pauses gated to digital silence, noted). Speaker similarity to an enrolment clip: 0.53 to 0.78 on Krish's own segments, -0.04 on noise.
- Face: all three photos detected (a padded retry catches faces that fill the frame), identity to the gallery 0.85 to 0.89; on the test video, frames with the face cut off by the edge were rejected and three whole-head stills kept across distinct poses.

## Still to prove

- The 0.45 speaker floor needs a real other-speaker control (a guest clip) on the home computer.
- The face identity floor (0.55) needs a guest frame from a real episode.
- Head-pose and sharpness floors are first settings; check them against the first real harvest.
