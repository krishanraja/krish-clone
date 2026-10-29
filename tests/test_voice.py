import tempfile
import unittest
from pathlib import Path

from krish_clone import media, voice

from .helpers import FFMPEG, FakeHeard, make_audio, speechlike


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class VoiceTest(unittest.TestCase):
    def test_clean_voice_is_kept_and_a_bed_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            clean = speechlike(Path(tmp) / "clean.wav")
            bedded = speechlike(Path(tmp) / "bed.wav", bed_db=-30)
            clean_read = voice.read(clean, heard=FakeHeard(12))
            bed_read = voice.read(bedded, heard=FakeHeard(12))
        self.assertTrue(clean_read.segments)
        self.assertTrue(all(s.tier == "clean" for s in clean_read.segments), [s.reasons for s in clean_read.segments])
        self.assertTrue(all("speaker not verified" in s.notes for s in clean_read.segments))
        self.assertTrue(all(s.tier == "rejected" for s in bed_read.segments))
        self.assertTrue(all(s.bed for s in bed_read.segments))
        self.assertTrue(all(any(r.startswith("something plays under the pauses") for r in s.reasons) for s in bed_read.segments))

    def test_a_bed_well_above_room_tone_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Room tone is the first 3 seconds of near-silence; then words over a -40 dB bed.
            path = make_audio(Path(tmp) / "x.wav",
                              "aevalsrc='if(lt(t,3),0.0003*(random(0)-0.5),sin(2*PI*220*t)*0.4*lt(mod(t,1),0.7)+0.02*(random(1)-0.5))':s=48000",
                              12)
            heard = FakeHeard(12)
            heard.segments = [s for s in heard.segments if s["start"] >= 4]
            read = voice.read(path, heard=heard)
        self.assertTrue(read.segments and all(s.bed for s in read.segments))

    def test_digital_silence_is_ignored_for_room_tone_and_noted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_audio(Path(tmp) / "gated.wav", "aevalsrc='sin(2*PI*220*t)*0.4*lt(mod(t,1),0.7)':s=48000", 12)
            read = voice.read(path, heard=FakeHeard(12))
        self.assertGreater(read.room_tone_db, voice.DIGITAL_SILENCE - 1)
        self.assertTrue(all("pauses are digital silence (gated or spliced)" in s.notes for s in read.segments))
        self.assertTrue(all(s.tier == "clean" for s in read.segments))

    def test_flat_topped_clipping_is_found_but_codec_overshoot_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            clipped = make_audio(Path(tmp) / "clip.wav", "aevalsrc='clip(2*sin(2*PI*100*t),-1,1)':s=48000", 1)
            healthy = make_audio(Path(tmp) / "ok.wav", "aevalsrc='0.89*sin(2*PI*100*t)':s=48000", 1)
            self.assertGreater(len(media.clip_events(clipped)), 50)
            self.assertEqual(media.clip_events(healthy), [])

    def test_group_joins_short_sentences_and_never_splits_one(self):
        pieces = [{"start": 0.0, "end": 2.0, "text": "a"}, {"start": 2.3, "end": 4.0, "text": "b"},
                  {"start": 4.2, "end": 9.0, "text": "c"}, {"start": 12.0, "end": 20.0, "text": "d"}]
        segments = voice.group(pieces)
        self.assertEqual([s.text for s in segments], ["a b c", "d"])
        self.assertEqual((segments[0].start, segments[0].end), (0.0, 9.0))

    def test_judge_rules(self):
        short = voice.judge(voice.Segment(0, 2, "x", snr_db=40))
        self.assertEqual(short.tier, "rejected")
        review = voice.judge(voice.Segment(0, 10, "x", snr_db=25))
        self.assertEqual(review.tier, "review")
        stranger = voice.Segment(0, 10, "x", snr_db=40, speaker=0.2)
        self.assertEqual(voice.judge(stranger, speaker_floor=0.45).tier, "rejected")
        krish = voice.Segment(0, 10, "x", snr_db=40, speaker=0.7)
        self.assertEqual(voice.judge(krish, speaker_floor=0.45).tier, "clean")


if __name__ == "__main__":
    unittest.main()
