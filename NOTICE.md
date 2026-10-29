# Attributions

- **content-watcher** (krishanraja/content-watcher, MIT): a dependency. Transcription (`read/audio.transcribe`, faster-whisper), loudness, 16 kHz decoding, `read/visual.cuts`, `timeline/moments.dhash` and `hamming`, ffmpeg helpers in `tools`.
- **contentarchives** (krishanraja/contentarchives, read at `c609162`): the buffalo_l detect and embed approach, the 0.55 cosine join threshold measured on Krish's library (`cluster_faces.py`), the greedy centroid grouping and the 0.12 subject share. No code copied.
- **insightface** (deepinsight/insightface 0.7.3, code MIT): `faceonnx.py` reimplements its SCRFD decoding, ArcFace alignment and 3D-landmark pose, and `krish_clone/data/meanshape_68.json` is its `meanshape_68.pkl`. The buffalo_l model weights are downloaded at run time, not shipped, and are licensed for non-commercial research: fine for Krish's own clone, to be replaced in any commercial product.
- **OpenFace** (cmusatyalab/openface, Apache-2.0, read at `99b7241`): the largest face is the subject; accept by distance to a reference gallery. No code copied.
- **VoiceStudio** (debpalash/VoiceStudio, AGPL-3.0, read at `4d4cb0b`): ideas only (separation, reference-slice choice, evaluation design). No code copied, so this repository is not AGPL.
- **SpeechBrain** `spkrec-ecapa-voxceleb` (Apache-2.0) for speaker similarity, and **faster-whisper** for transcription, both downloaded at run time.
- **Calibration audio**: ElevenLabs' public voice previews were used once to calibrate the speaker threshold. They are not stored in this repository.
