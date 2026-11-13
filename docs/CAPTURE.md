# Capture: the two recordings the old footage cannot replace

Checked against the platforms' own guidance on 2026-10-29. Recheck before recording; both change often.

## 1. Voice session (ElevenLabs Professional Voice Clone)

ElevenLabs' PVC guide ([docs](https://elevenlabs.io/docs/eleven-creative/voices/voice-cloning/professional-voice-cloning/llms.txt)): at least 30 minutes, better 1 to 3 hours; one speaker; one consistent speaking style (the clone copies the style of its samples); speech around -23 to -18 dB RMS with a -3 dB true peak; a quiet, damped room, two fists from the microphone, with a pop filter; files of about 30 minutes, MP3 at 192 kbps or more.

- Script: `clone script` builds `reading-script.md` from Krish's own scripts in 3 Posts. On 2026-10-29 that was 7,057 unique words from 13 long scripts (the long version wins where an episode also has a 90 second cut), about 47 minutes, plus about 28 minutes of free talk to reach 75. Names and figures he uses come first, because clones slip on them.
- Record WAV on one microphone in one sitting. Keep the delivery the voice he wants the clone to have.
- Harvest it like any source, then `clone export elevenlabs`.
- Verification on ElevenLabs happens in the browser with the same microphone and tone; read each line once.

## 2. Digital Twin take (HeyGen, Avatar V)

HeyGen's guide ([blog, updated 20 Oct 2026](https://www.heygen.com/blog/how-to-create-digital-twin-avatar)): about 30 seconds to camera ("longer clean footage helps facial range"); one continuous take at 1080p and 30 fps or more, face visible, no cuts; camera mounted at eye level; face a window or soft light, no harsh shadow; stay in one spot; be more expressive than feels natural, with hand movement below the chest; no logos or busy patterns. Head movement, blur and multiple scenes are why uploads get rejected. Consent is the on-screen code read aloud by the same person; screen recordings and generated clips fail. One twin slot holds up to 500 looks.

Shot list:

1. Phone or camera on a tripod at eye level, 1080p 30 fps or 4K, landscape and portrait looks recorded separately.
2. Soft light from the front or a window in front; nothing bright behind.
3. Talk for 60 to 90 seconds (comfortably over 30), one take: the opening of a real episode, with natural hands.
4. Two or three looks (outfit or setting) as separate takes; they become looks in one slot.
5. Before any upload: `clone twincheck <take>.mp4 --gallery <library>\face\photos\*.jpg` must say `ready`.

HeyGen also clones the voice from the take. The plan is for the ElevenLabs PVC to be the voice; whether to drive the twin with ElevenLabs audio is a check to make in HeyGen when the twin exists (not verified here).

## 3. Photo looks (HeyGen photo avatar)

A photo look is the fast way to new outfits and settings; the twin take above stays the realism anchor. Checked on 2026-11-13 against HeyGen's guidance ([developer docs](https://developers.heygen.com/photo-avatar), [Avatar IV guide](https://community.heygen.com/public/resources/introducing-avatar-iv-create-talking-avatars-from-a-single-photo), [custom avatars](https://community.heygen.com/en/public/resources/custom-avatars-how-to-create-digital-twins-or-fully-ai-generated-avatars)): recent photos of only him, sharp and evenly lit, front-facing or a slight turn, neutral or subtle expression (a slightly open mouth animates better than a wide grin), no sunglasses, no hat over the forehead, half body or closer, and 10 to 15 photos to train a photo avatar group.

How the seeds in the Drive `Photos` folder were chosen:

1. Only photos from 2025 onward, so every look is his current face and beard.
2. Exact duplicates dropped; the largest original kept over crops and chat copies.
3. Measured: long side at least 1600 px, the face at least about 650 px tall, sharp on the face, one person.
4. Judged by eye against the guidance above, then one photo per distinct outfit and setting.

Ten seeds sit at the top of `Photos`: eight distinct looks plus two more angles of the plain-wall anchor, so the set doubles as the 10 to 15 photo training group. Everything else is flat in `Photos/All other photos`. The anchor photos also make a good identity gallery for `clone twincheck`.
