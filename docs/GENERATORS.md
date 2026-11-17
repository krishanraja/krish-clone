# Image and video generators: the bar a new one must clear

This repository judges clones; it never generates. Generation runs through the connected tools and content-engine, and every finished piece made with an approved clone still comes to Krish before it goes out (`docs/REGISTRY.md`). This file records the bar a new image or video generator must clear before it joins that route, and each generator evaluated against it.

## The current route (2026-11-15)

| Job | Route | Status |
|---|---|---|
| Krish presenting to camera | HeyGen avatar group "Krish Raja" (15 looks) with its voice "Krish Voice" | Approved on his own say-so, 2026-11-15 (`config/synthetic-approvals.json`) |
| His voice for narration | ElevenLabs "Krish Remix" (`FOupAntbAMhJ9n9Q4dfC`) on model `eleven_v3`, delivery set with v3 audio tags (below) | Approved, 2026-11-15; delivery approved 2026-11-17 |
| Range: stills, storyboards, ad variants, several takes of one approved still | Higgsfield, connected | Placed by Krish (Heartside first, makeyourmindup and Full Time share); about 2.75 credits a GPT Image still and 210 a Seedance 2.5 clip (Control Center, observed 2026-10-22). Its placement rules out a moving mouth. |
| Controlled motion from one approved still | Runway, connected | Placed as Higgsfield |

## His narration voice: how it is driven (2026-11-17)

Krish's notes on Krish Remix takes: "I don't enunciate my T's as much as this, and I am a bit more animated". Two routes were tried on the Tue 17 Nov voiceover lines.

- **Rejected: a voice designed from a text description** (ElevenLabs voice design, `eleven_ttv_v3`, his accent and both notes written out). All three previews were new people: "Now they just sound like completely different humans entirely. Remember that what we're working off of was trained on all of my voice inputs." A description never hears his recordings, so this route cannot keep him. None was saved.
- **Approved: Krish Remix itself on `eleven_v3`, default stability (Natural, 0.5), with audio tags** that set the delivery and leave his words unchanged: `[excited] You can't sack an AI. [casual] So when it screws up, who gets the boot? [playful] Probably you. [conversational] And honestly, that's fair, because loads of people are blaming the AI for their own mistakes right now.` Of two takes he said "take 2 is good" (ElevenLabs generation `NTGInE9H8lsyZUNsU7Z0`, 226 credits a take). `eleven_v4` did not sound like him on this voice.

Still open: tags change mood, not accent, so his softer T's are not fixed by them. The surgical route keeps his identity and changes one attribute at a time: ElevenLabs Voice Remix on Krish Remix (a new voice id, judged against take 2 on the same lines, and added to `config/synthetic-approvals.json` only on his say-so), and in the longer run the Professional Voice Clone from clean, animated recordings of him (`docs/STRATEGY.md`).

## The bar

A new generator joins only when all of these hold:

1. **It does a job the current route cannot**, or the same job measurably better or cheaper. A second gateway to models already reachable is not a new capability.
2. **It holds his identity.** `clone likeness`, run on Krish's own machine, shows its output for the job at least as close to him as the current route's output for the same job (`docs/EVALUATION.md`).
3. **His face and voice reach no new provider without his yes.** Any provider that would receive his photos, video or voice is a new processor of his biometric data; Krish approves it by name before the first upload (`AGENTS.md`).
4. **Every call is spend he approves when it happens**, with the expected credits stated.
5. **It adds no creative interface the route does not need.** The work is driven from content-engine and the connectors.

## Open Generative AI: evaluated 2026-11-15, not adopted

[Anil-matcha/Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI) at commit `fd7dd92` (MIT), read in full, run on synthetic faces only. Nothing of it is installed here.

**What it is.** A web and desktop studio (Next.js, Vite, Electron; 14 tabbed studios) over [MuAPI](https://muapi.ai), a third-party aggregator API reached with an `x-api-key`. Its cloud catalogue reaches 600+ models: Seedance, Kling, MiniMax, Veo, Wan, Nano Banana, Flux, OmniHuman, InfiniteTalk, several lip-sync models and face swap. The desktop app adds two local engines: stable-diffusion.cpp (SD 1.5, SDXL and Z-Image, text to image) and Wan2GP, which the user installs on a CUDA or ROCm GPU (Wan 2.1 and 2.2 text to video, Wan 2.2 image to video at 480p from a start frame, Hunyuan, LTX-2, Flux, Qwen-Image).

| Priority | Finding |
|---|---|
| Identity fidelity | In the cloud, identity models exist (reference to video, OmniHuman, InfiniteTalk, Kling avatar), but only by uploading his photos to MuAPI and onward to whichever company runs the model. Locally, no model takes an identity reference; only Wan 2.2 image to video starts from a still, at 480p, with no speech or lip sync. The synthetic test below measures the local image path: it does not keep a face from one generation to the next. |
| Visual consistency | No identity or character store. Its "upload history" keeps file URLs in the browser's local storage. |
| Reliability | One aggregator for every cloud model, submit then poll. The local engine is pulled from the newest upstream release at install time, unpinned, and neither the engine nor the model weights are checked against a hash; this repository checks its face models by sha256 before use. |
| Controllability | Detailed per-model settings, but nothing for this job that the connected Higgsfield (Soul, Kling Omni, Seedance, motion control) and HeyGen (avatar video, look remix, lip sync) tools lack. |
| Cost | A new pay-per-generation MuAPI account on top of HeyGen, ElevenLabs and Higgsfield, which are already paid for and placed. MuAPI's per-model prices were not checked here. The local path is free per image but needs a CUDA GPU for video, and it cannot hold his face (below). |

**It duplicates what is connected.** Higgsfield's own catalogue (read 2026-11-15, the first 100 models that take a reference image) already reaches the same families: Seedance 2.0 and 2.5, Kling 3.0 and 4.0 with Omni, MiniMax H3, Veo 3.1, Wan 2.6 to 3.0, Gemini Omni Flash, Nano Banana, Flux Kontext, Sync Lipsync 3. HeyGen already covers presenter video, lip sync and new looks on the approved avatar. Adding it would mean a second gateway to the same models plus a creative interface, both of which the bar rules out.

**Privacy and consent.** Every cloud call sends media to MuAPI (`api.muapi.ai`, files to its S3 upload target) and on to the model's vendor: a new processor of his biometric data, which needs his approval by name before any upload. It advertises "no content filters, no guardrails" and ships face swap for images and video (`ai-image-face-swap`, `ai-video-face-swap`) with no consent step like HeyGen's spoken consent code. For a likeness people must trust is his, that is a weaker control than the current route. The API key is kept in the browser's local storage.

**Reused: nothing.** What it confirms, that a reference image is how identity is held, is already available through the connected tools under approvals that exist. What the evaluation exposed instead is a gap in this repository: it could measure a voice clone (`clone evaluate`) but not whether a generated face is still him. `clone likeness` closes that gap, and it is how any future candidate is judged against the current route.

### The synthetic test

Run on 2026-11-15 in a cloud session on synthetic faces only: no face of Krish's, no upload, no spend, no platform called.

- **Generator:** the weights the app's local engine offers for portraits, Dreamshaper 8 (`DreamShaper_8_pruned.safetensors`, sha256 `879db523c30d3b9017143d56705015e15a2cb5628762c11d086fed9538abd7fd`, from the URL in its catalogue).
- **Settings:** the app's local defaults: 512 by 512, 20 steps, guidance 7.5, Euler ancestral.
- **Runtime:** diffusers on 4 CPU cores. The app's stable-diffusion.cpp build could not be built in that session. Whether a face holds depends on the weights and on whether the model receives a reference image; the runtime does not change either.
- **Scoring:** `clone likeness` with the sha256-checked buffalo_l models.

| Set | Stands for | Identity against the synthetic person |
|---|---|---|
| One still (seed 1) and four light variations of it (image to image, strength 0.35) | real photos of him | 0.888 to 0.952, each against the others; floor 0.895 |
| Three stills made from that still (image to image, strength 0.5) | a generator given his photo | 0.876 to 0.913 |
| Six stills from the same words, new seeds, no reference | the app's local image path, describing him in words | 0.542 to 0.675 |
| A 10 second clip of the three stills made from his still | a steady generated clip | median 0.877, worst 5% 0.874 |
| The same clip with 2 of its 10 seconds swapped for a text-only face | a clip that drifts | median 0.873, worst 5% 0.627 |

The six text-only stills agree with one another at only 0.51 to 0.69, against 0.85 for the three made from a still. Given only a description, the local model draws a new man each time: the same type at a glance, a different person to the face model. Each took 117 to 141 seconds on the CPU; each image-to-image still took 49 to 70.

Two findings changed the code before it was committed:

- **The absolute floor was too low.** The library's identity floor of 0.55 was measured between Krish and real other people. Five of the six lookalikes score above it, and so does the swapped stretch of the drifting clip. Drift is now judged against his own floor less 0.10.
- **The synthetic "real" set is tighter than real photos.** It is near-copies of one picture, so the stills made from it miss its fidelity floor by up to 0.02. Real photos of him from different days have a wider spread. His first baseline run sets the real numbers and recalibrates the 0.10.

The made-from-a-still stills changed the scene only modestly. They test how well a reference holds a face; they do not show how a commercial reference-to-video model would do. That comparison happens on Krish's machine, against the HeyGen baseline, once he approves a sample generation.

### Rollback

Nothing of Open Generative AI entered this repository, its dependencies or Krish's machines. `clone likeness` adds one module (`krish_clone/likeness.py`), one command and its tests, with no new dependency, and writes nothing; to remove it, revert the commit that added it.
