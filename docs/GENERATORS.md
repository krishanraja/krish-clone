# Image and video generators: the bar a new one must clear

This repository judges clones; it never generates. Generation runs through the connected tools and content-engine, and every finished piece made with an approved clone still comes to Krish before it goes out (`docs/REGISTRY.md`). This file records the bar a new image or video generator must clear before it joins that route, and each generator evaluated against it.

## The current route (2026-11-15)

| Job | Route | Status |
|---|---|---|
| Krish presenting to camera | HeyGen avatar group "Krish Raja" (15 looks) with its voice "Krish Voice" | Approved on his own say-so, 2026-11-15 (`config/synthetic-approvals.json`) |
| His voice for narration | ElevenLabs "Krish v2" (`EWMCMyM8o9ZcYCijk7nx`) on model `eleven_v3`, delivery set with v3 audio tags, sped up 15% after rendering (below) | Approved 2026-11-17; his best so far. "Krish Remix" (`FOupAntbAMhJ9n9Q4dfC`, approved 2026-11-15) stays approved as the backup |
| Range: stills, storyboards, ad variants, several takes of one approved still | Higgsfield, connected | Placed by Krish (Heartside first, makeyourmindup and Full Time share); about 2.75 credits a GPT Image still and 210 a Seedance 2.5 clip (Control Center, observed 2026-10-22). Its placement rules out a moving mouth. |
| Controlled motion from one approved still | Runway, connected | Placed as Higgsfield |

## His narration voice: Krish v2, and how it is driven (2026-11-17)

Krish's notes on Krish Remix takes: "I don't enunciate my T's as much as this, and I am a bit more animated". Two routes were tried on the Tue 17 Nov voiceover lines.

- **Rejected: a voice designed from a text description** (ElevenLabs voice design, `eleven_ttv_v3`, his accent and both notes written out). All three previews were new people: "Now they just sound like completely different humans entirely. Remember that what we're working off of was trained on all of my voice inputs." A description never hears his recordings, so this route cannot keep him. None was saved.
- **Approved: Krish Remix itself on `eleven_v3`, default stability (Natural, 0.5), with audio tags** that set the delivery and leave his words unchanged: `[excited] You can't sack an AI. [casual] So when it screws up, who gets the boot? [playful] Probably you. [conversational] And honestly, that's fair, because loads of people are blaming the AI for their own mistakes right now.` Of two takes he said "take 2 is good" (ElevenLabs generation `NTGInE9H8lsyZUNsU7Z0`, 226 credits a take). `eleven_v4` did not sound like him on this voice.

Tags change mood, not accent, so they did not soften his T's. The surgical route keeps his identity and changes one attribute at a time: ElevenLabs Voice Remix on Krish Remix.

- **Approved, his best so far: "Krish v2" (`EWMCMyM8o9ZcYCijk7nx`, registry `krish-voice-elevenlabs-v2`).** Krish made two remixes of Krish Remix in the ElevenLabs app with the prompt "Same man, same accent and tone. Softer, glottal T's like relaxed London speech; keep everything else identical." ("Krish v1", `zBnYxhtZxkcWwYsi497n`, and "Krish v2"). Each read the same tagged lines on `eleven_v3`, two takes each. He picked "v2, take A - but needs to speak 15% faster" (generation `zqb21EXdvGqDbB6XQ8jo`), then of the take sped up 15%: "yes, 15% is right, go ahead - ensure the krish-clone repo and the other two sessions know that this is the best choice thus far in terms of voice ID and your usage of it".

### How to use it

1. Voice `EWMCMyM8o9ZcYCijk7nx` ("Krish v2"), model `eleven_v3`, default stability (Natural, 0.5). Not `eleven_v4`.
2. Write his approved words unchanged, with v3 audio tags before the beats that set the delivery: `[excited]` on the hook, `[casual]`, `[playful]` on the turn, `[conversational]` on the explanation.
3. Render two takes and keep the better one; v3 varies from take to take.
4. Speed the chosen take up 15% after rendering, keeping pitch: `ffmpeg -i take.mp3 -filter:a atempo=1.15 out.mp3`. The `eleven_v3` settings the connector exposes have no speed control, and speeding the finished take keeps the read he picked. On 17 Nov this took the take from 12.2 s to 10.6 s.
5. Each finished piece still comes to him before it goes out.

**Warning (17 Nov 2026):** this recipe held for one ten-second opening only. On a whole 90-second script it failed every time, and his accent drifted. Read the failure log below before relying on it for anything longer.

### Failure log: a whole 90-second script would not hold his voice (Tue 17 Nov 2026)

Krish asked for this log "in full excruciating detail" so the voice can be repaired surgically later. The approved recipe above held for one ten-second opening. Every attempt to voice the whole 90-second script after it failed, and on this piece he gave up on the synthetic voice: "For this one, I'll just record manually."

Everything below happened in one content-engine session (session_01JRhKytFcFVtUWn8teqtkUB) on the Tuesday off-day voiceover short "Which of your habits will cost you your job once AI is at work?" (content-engine piece `701a2c55-7400-4dc8-99cb-d6001147ae16`). The script is `docs/plans/2026-11-16-week/tue-habits-vo/script.md` in content-engine: about 240 words, seven paragraphs. Times are UTC. All generations ran through the ElevenLabs connector (creative tools), in flows `VIWrolAx0vnRiw4MlYrt` (rounds 1 to 4b) and `lyaAZ5OQj8bp08tbDKPJ` (rounds 5 and 6 sit in the same flow as his approved opening). Only the opening was ever judged good.

#### Round by round

| # | Time | Voice | Model, stability | Text | Takes (generation id, length) | Credits | Result |
|---|---|---|---|---|---|---|---|
| 1 | 10:04 | Five voices: Krish Remix `FOupAntbAMhJ9n9Q4dfC`, the unapproved clone "Krish" `7ApmIXLoWa0cKUtJqfHc`, stock Christopher Atkins `WrH8mCWis9c3KnjuevXI`, stock Alec Wilcock `H8DglpTKljBPHb5j9pP8`, stock Katie Crystal `E8FfddrREO3vtyNsTKnh` | `eleven_v4`, default | First two paragraphs of an earlier draft, no tags | One take each, about 16 to 17 s | 5 x 230 | Superseded before he judged them: he asked for a younger, more casual script read in Krish Remix |
| 2 | 10:09 | Krish Remix | `eleven_v4`, default | Whole script v3 (233 words), no tags | `tnYvpfQ8jI9mV3DDVfFq` 89.0 s; `YWqgXvGXWMTIqNQNSviY` 87.5 s | 2 x 1,256 | Failed. Krish: "Why does this not sound like that Krish Remix voice when I play it in ElevenLabs?" |
| 3 | 10:13 | Krish Remix | `eleven_v3` and `eleven_multilingual_v2`, default | Opening two sentences only | v3 `mTOmSZGaZXn7fBQzyZUS` 11.4 s; multilingual_v2 `aFiISQNAo8SCHcDFLWF1` 10.3 s | 2 x 180 | Test. Krish: "v3 sounds right" |
| 4 | 10:16 | Krish Remix | `eleven_v3`, default (Natural, 0.5) | Whole script, no tags | `opbaRFlEGj3TeeAZvZPu` 88.4 s; `HNc1PmtzXBH0l1Y1usyG` 90.7 s | 2 x 1,256 | Failed. Krish: "I don't enunciate my T's as much as this, and I am a bit more animated". This sent the work to the voice-design rounds that produced Krish v2 (above) |
| 4b | 10:45 | Krish Remix | `eleven_v3`, default | Whole script v4 with tags (listed below) | `8JRAxOVTj1YSbklpAlY3`; `zMigVLid5qbHwNhkq4Co` | 2 x 1,462 | Wasted, never judged. Started on an interim relay that named Krish Remix as the voice; Krish v2 replaced it two minutes later |
| 5 | 10:50 | Krish v2 `EWMCMyM8o9ZcYCijk7nx` | `eleven_v3`, default (Natural, 0.5) | Whole script v4 in one generation, with his four approved tags plus three he never approved: `[sarcastic]`, `[curious]`, `[surprised]` | `mLZSfpiRsbAeNNZ8dKST` 103.3 s; `Iytwgdc6X4Lr8tbr2zTw` 99.3 s (raw, not sped up) | 2 x 1,462 | Failed. Krish: "The voice has changed again from what I approved in the other session." |
| 6 | 10:55 | Krish v2 | `eleven_v3`, default (Natural, 0.5) | Six paragraphs, one generation each, only his four approved tags. The approved opening take `zqb21EXdvGqDbB6XQ8jo` stood as paragraph 1 | P2 `3XrDkRsEG0MQ8gMiDr9i` 11.0 s / `nNE8Gh7u93mKcawFnFUy` 11.1 s; P3 `91P6hirrfoQxIkdsXP8J` 12.2 s / `xpqRXieVkcRBeTtY7SVA` 13.0 s; P4 `uBVZoakXq4NK6NjHbfTZ` 18.8 s / `8G0ilAj0qxzCyFy1d0qH` 18.6 s; P5 `iFqFudXXmD3jgBU14Z8V` 9.0 s / `LtZuoDMil7LKR6wNFgVI` 9.2 s; P6 `rJ45Jbgcv2gYUPq6Tyjh` 19.5 s / `27FfK3vbNp2OBgFcLfxF` 21.0 s; P7 `Y4iihJcgejUIBqBUoH7b` 13.6 s / `bTARFbolFornO21ympBY` 13.7 s | 2,522 in all | Failed badly. Krish's verdict: the accent had drifted northern and posh, away from his own voice |
| 7 | 10:58 | Krish v2 | `eleven_v3`, **Robust (stability 1)**, set as `voice_settings.stability` on tts node `QGx0ZwRzpbJI2y2Fwper` | Paragraph 3 (the car) only, his tags | `9ACJgWbh1vzg9M5bhB0q` 11.2 s; `4u2mPcJMpsIWmBXClYxR` 11.5 s | 2 x 192 | Failed. Krish: "no". He then chose to record the piece himself |

**Tags in rounds 4b and 5.** The opening used `[excited]`, `[casual]`, `[playful]` and `[conversational]` exactly as approved. After it: `[conversational]` then `[sarcastic]` on "They just shrug and say, well, AI isn't very good, is it?"; `[curious]` on "And bosses already get this"; `[surprised]` on "only 29% even ranked judgment"; `[playful]` on "Because they are"; `[excited]` on "Now, three habits"; `[casual]` on the habits and on the close.

**Tags in round 6**, only from his approved four: `[conversational]` and `[casual]` on P2 and P3; `[conversational]` then `[playful]` on P4 and P5; `[excited]` then `[casual]` on P6; `[conversational]`, `[playful]` and `[casual]` on P7.

**Spend.** About 16,000 credits on this piece's voice after the approved opening, roughly $3.50 at the connector's quoted prices, none of it usable. The usage read (`account_get_usage`) was refused all session ("This connector requires additional permissions"), so the balance was never checked before spending.

#### What is established

- **The voice id was never the fault.** Every failed take's metadata names the intended voice: Krish Remix in rounds 2 to 4b, Krish v2 in rounds 5 to 7.
- **`eleven_v4` does not sound like Krish Remix.** Round 2, then round 3 against v3 and multilingual_v2, by his ear.
- **One approved take does not predict the next.** One approved ten-second take of Krish v2 on `eleven_v3` at Natural (`zqb21EXdvGqDbB6XQ8jo`, then sped up 15%) did not carry over. Twelve further short takes on the same voice, model, stability and tag set (round 6) drifted to an accent he does not have.
- **Robust stability did not fix it** on the one paragraph tried (round 7).
- **Shorter generations did not fix it either.** Splitting the script into paragraphs of 9 to 21 s (round 6) failed just as the single 100-second generation did (round 5).

#### Suspected, not proven (no test isolated any of these)

1. **The designed voice has no fixed accent.** Krish v2 is a Voice Remix of Krish Remix, which is itself a designed voice ("more of a posh london accent with an aussie twang"). Neither was trained on his recordings directly. So each `eleven_v3` generation may re-interpret the accent from a voice that came from a description, and the approved opening may have been one good draw rather than a stable property. Round 6 is the strongest evidence: same settings, different text, different accent.
2. **The text pulls the accent.** The opening is short, casual and British-coded ("who gets the boot? Probably you"). Lines with numbers, "HR chiefs", "judgment" and "resignation letter" may pull v3 toward a formal, posher read. Untested: the same paragraph with and without the formal words.
3. **The tags pull the accent.** `[excited]` and `[playful]` raise energy, and v3 may express that as a different accent on a designed voice. Round 6 used only his approved tags and still drifted, so tags alone do not explain it.
4. **The 15% speed-up was never tested on a whole take.** Raw length was not the cause on its own (round 6), but nobody has heard a 90-second Krish v2 take sped up 15%, because none was ever good enough to speed up.

#### What a later surgical fix should try, in order

1. **Train a voice on his own recordings instead of describing one.** This is the Professional Voice Clone in `docs/STRATEGY.md`, from clean, animated recordings. Test it on this exact script, all seven paragraphs and not just the opening, before he hears it.
2. **Speech-to-speech from his own read.** He records the script himself, as he is doing for this piece, and ElevenLabs Voice Changer (`eleven_multilingual_sts_v2`, in the creative flow's model list) maps it onto the approved voice, keeping his timing and accent. Untested on this account.
3. **If a designed voice is kept, measure before he listens.** Test accent stability across this fixed seven-paragraph script, four takes per paragraph, with `clone evaluate` scoring each take against his real voice (`docs/EVALUATION.md`). Only takes that pass go to him.
4. **Never approve a voice on its opening alone.** The approval test for a narration voice must be a full script, numbers and formal words included.
5. **Fix the usage read first,** and price a full-script run before it starts.

Still open: the Professional Voice Clone from clean, animated recordings of him (`docs/STRATEGY.md`) remains the longer-run route.

## His likeness in stills: closing the last 10% (2026-11-17)

Krish, on six generated headshots for face-led covers: "they all look 90% there but need surgical 10%. can you involve the krish-clone repo to encode how we close the final 10% gap?" This section is that encoding, built the way the voice work above was: measure first, change one thing at a time, and record every round so a later session repairs it surgically.

### What was made (content-engine session_01JRhKyq6QmG4sLbWkSRVepS)

- **References.** Only the files at the top of his Drive folder "Photos" (`1PQDSg4_kD6zwVerqvxaiQE5Ocjnsd6xB`), never its subfolders (Krish: "only use my reference images from ... folder, NOT the subfolders"). He later allowed its subfolder "All other photos" for this work, never the DO-NOT-USE folder inside it. Six were sent to Higgsfield as references, at his request in that session: the denim-jacket cutout, the bespectacled cutout, the natural cutout, the pale blue Oxford headshot, the restored portrait with natural shoulders and the natural headshot on off-white.
- **Generator.** Higgsfield `gpt_image_2_6`, 3:4, three to four references per still, 0.25 credits a still by the connector's own preflight (`get_cost`) on 2026-11-17. Six looks: navy knit on charcoal; glasses, blazer and white shirt on off-white; skeptical brow, black tee on grey; glasses, overshirt on dark green; big smile, blue Oxford on the series yellow; glasses, navy jacket on near-black. Higgsfield job ids: `673105f2-8967-4365-a416-db1cef668422`, `2c0d9216-a4d5-48ba-9761-7788f58a2530`, `f58249ff-dd7c-4df7-9f55-8e647301d0d1`, `671c8e62-aa8a-4640-8d95-616aae81d938`, `d9a0c5da-3481-434d-b90c-bfb2a68a0f92`, `e9070f3b-eb63-4bca-b227-063c5084f058`.

### What the measurement says

`clone likeness --real <the nine top-level photos> --clone <the six stills>`, run in that cloud session at Krish's request rather than on his machine:

| | Identity (ArcFace, cosine to the real photos) |
|---|---|
| Real Krish against real Krish | median 0.763, 5th percentile 0.698 (the floor) |
| The six generated stills | 0.784, 0.734, 0.787, 0.787, 0.771, 0.764: all pass |
| His own screenshot (`Screenshot 2026-05-26 170626.png`) against the rest | 0.675, the weakest real file |

So every still is already him to the identity model, scoring as high as his own photos do against each other. **The last 10% is not identity.** It is what ArcFace cannot see: skin texture and age, hairline and hair texture, beard density and edge, teeth and smile, the shape of the glasses, skin tone under the lighting, and the polished studio finish no real photo of him has. Only his eye can name those, so the loop below starts with his words, not a score.

### His face profile: everything measurable about it (`clone faceprofile`)

Krish, 2026-11-17: "ensure krish-clone's image section is already powerful in terms of encoding my facial features ... it should literally observe and aggregate everything possibly knowable about my face". A generator is told what is fixed about his face only if something has measured it, so the loop below starts from a profile:

- **Sources.** The top of his Drive folder "Photos" and its subfolder "All other photos", never the DO-NOT-USE folder inside it (his words, same day). content-engine's home pass publishes the second set as "Likeness references" (`scripts/post-pack/photos.py`, `fetch --references`), never for a cover.
- **Who is counted.** Every face in every photo is embedded; the dominant identity is him, and a face below the identity floor (0.55) is skipped as someone else or unclear, so group photos and other people never enter the profile.
- **Geometry** from the 68 landmarks, near-frontal faces only (yaw and pitch within 20 degrees), every length per eye-centre distance and every angle after levelling the eye line: face, jaw and chin width; nasion to chin; nose length and width; nose to chin; mouth width; upper and lower lip; philtrum; chin height; the gap between the inner eye corners; each eye's width, openness and tilt; each brow's height; the lower-face ratio; and left-right asymmetry.
- **Colour** in CIELAB: cheek skin, forehead, beard, moustache, lips, eyes (the darkest third of the eye patch) and the hair above the brow. Beard darkness is the cheek's lightness minus the beard's.
- **Expression:** mouth opening and how far the corners lift above the lip centre.
- **Spread, not just the middle:** each measure's median, middle half and variation, so the brief says what never moves about him (the most stable geometry first) and what does (expression, beard, light).
- **Not measured, by design or by failure:** glasses (an edge test failed calibration on 17 Nov and was removed), hairline height (no forehead landmarks), skin texture and fine detail. These are observed by eye and written into the profile's observation notes, photo by photo, before a brief is written.
- **Where it lives.** `clone faceprofile <photos> --out <folder>` writes `face-profile.json` and `face-profile.md` only to a folder outside this repository (it refuses one inside), on his machine or in his Drive library. It is his biometric data; it never enters git, and nothing here uploads it.

First run (17 Nov 2026, the nine top-level photos, in content-engine's cloud session at his request): all nine counted as him (identity median 0.817 to his own centroid), seven near-frontal. The most stable measures, the ones a generated still must hit, were face width, chin width, nose width, jaw width, eye width, nose length and the inner-eye gap, each varying under 4% across his photos. Expression and lips varied most. The figures themselves stay in the private profile.

**A second opinion: Faceplugin's open-source SDK** (`github.com/Faceplugin-ltd/Open-Source-Face-Recognition-SDK`, evaluated 2026-11-17; Krish: "you can leverage this without license"). It does what buffalo_l already does (68-point landmarks from a MobileFaceNet, an IR-50 embedding, pose), from models trained separately, so it is useful only as a cross-check: a measurement both models agree on is a fact about his face, not a habit of one model. Two cautions: the repository carries no licence file, only a badge (he has said to use it), and it ships a closed native library (`face_util/FaceUtil.so`, `.dll`) that cannot be read. A cross-check loads only its Python landmark and embedding models, never that library, and needs PyTorch, which this repository does not install. Not wired in yet.

### The surgical loop

1. **Start from the profile.** Put his most stable measures in the brief for every still, and score each still's geometry against the profile's middle half as well as its identity; a still outside the middle half on a stable measure is the 10% to fix first.
2. **He names the gap, still by still, in his own words.** Ask one question per still: "What is the 10% on this one?", offering these attributes to point at: eyes and glasses; hairline and hair texture; beard density and edge; skin texture and age; teeth and smile; nose; ears; skin tone; build and shoulders; overall polish. His words go into the round log below, verbatim. Never guess the attribute for him.
3. **Edit, never regenerate.** Feed the still he liked best plus the one real photo that shows the named attribute most clearly, and ask for that attribute only: "Keep this exact image. Change only the <attribute> to match the second reference photo. Do not change anything else." One attribute per pass. A fresh generation re-rolls everything and loses what was already right, which is the image counterpart of the voice failure above (one good draw does not predict the next).
4. **Measure each edit.** `clone likeness` on the edited still against the same real set. An edit that drops identity below the still it came from is discarded, however it looks.
5. **Keep the reference set clean.** Drop the screenshot (0.675) from the references; it is the least like the rest of him. Prefer photos with his natural skin and real light over the retouched ones, so the generator copies his texture, not a studio finish.
6. **Stop at his yes.** A still is approved only in his own words, recorded with `clone registry add` (kind likeness, the still's sha256, his words and the date) before content-engine uses it; each finished cover still comes to him before it goes out.
7. **If the loop stalls after two rounds on one still**, train a reusable identity instead: Higgsfield Soul ID from 10 to 20 top-level photos (the connector's `show_characters` train), then generate with `soul_2` and that id, and run the same loop. It costs more and needs his approval by name, so it is the second route, not the first.

### Round log

Gate every still on `clone likeness` against all his real photos before showing it to him: on 18 Nov its pass line matched his own verdict on six stills out of six, so a still below it is not worth his look. Measure colour before regenerating anything: a generator's skin-tone bias is fixed free, locally, and only geometry or features need a new generation.


| Round | Date | Stills | What Krish said | Change made | Identity after |
|---|---|---|---|---|---|
| 1 | 2026-11-17 | the six above | "they all look 90% there but need surgical 10%" | none yet: step 1 asks him to name each still's 10% | 0.734 to 0.787 |
| 2 | 2026-11-18 | the bank of six (round 1 edits of five, the original glasses still) | none yet; measured against his face profile from all 59 photos | geometry was inside his normal range on every still; the one fault every still shared was skin too red (skin a* 24 to 31 against his 16.5 to 21; forehead worst). A local LAB pull of a* on skin-hued pixels only, no generation and no spend, brought skin into range on five of six and halved the forehead excess | 0.775 to 0.858 against his own centroid (unchanged by the fix) |
| 3 | 2026-11-18 | the six colour-corrected stills | "1. Image 1 looks good and could pass for me. 2. Image 2: my chin is too small. 3. Image 3 is good and could pass for me. 4. Image 4 is good and could pass for me. 5. Image 5 looks nothing like me. 6. Image 6 is good and could pass for me." | stills 1, 3, 4 and 6 recorded as approved (`krish-still-higgsfield-1`, `-3`, `-4`, `-6`, each pinned by its file's sha256); still 5 dropped; still 2 given one edit, chin longer and stronger, two variants (about 0.5 credits). The chin measures longer on both (chin height 0.66 to 0.70) | `clone likeness` against all 59 real photos (pass line 0.711, the 5th percentile of him against himself) agreed with his verdict on all six: 0.757, 0.773, 0.755, 0.762 pass; still 2 0.678 and still 5 0.637 fail. Chin edits 0.678 and 0.690, still below the line |

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
