# Capture: the two recordings the old footage cannot replace

Checked against the platforms' own guidance on 2026-10-29. Recheck before recording; both change often.

## 1. Voice session (ElevenLabs Professional Voice Clone)

ElevenLabs' PVC guide ([docs](https://elevenlabs.io/docs/eleven-creative/voices/voice-cloning/professional-voice-cloning/llms.txt)): at least 30 minutes, better 1 to 3 hours; one speaker; one consistent speaking style (the clone copies the style of its samples); speech around -23 to -18 dB RMS with a -3 dB true peak; a quiet, damped room, two fists from the microphone, with a pop filter; files of about 30 minutes, MP3 at 192 kbps or more.

- Script: `clone script` builds `reading-script.md` from Krish's own scripts in 3 Posts. On 2026-10-29 that was 8,043 unique words, about 54 minutes, plus about 21 minutes of free talk to reach 75. Names and figures he uses come first, because clones slip on them.
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
