import json
import tempfile
import unittest
from pathlib import Path

from krish_clone import library, report, voice

from .helpers import FFMPEG, make_audio


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class LibraryTest(unittest.TestCase):
    def test_voice_segments_are_cut_at_full_rate_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            master = make_audio(root / "master.wav", "sine=frequency=220:sample_rate=48000", 10)
            lib = library.Library(root / "lib")
            segment = voice.judge(voice.Segment(2.0, 6.0, "hello", snr_db=40))
            name = lib.add_voice("abc", master, segment)
            written = root / "lib" / "voice" / "clean" / name
            before = written.read_bytes()
            lib.add_voice("abc", master, segment)  # a rerun changes nothing
            self.assertEqual(written.read_bytes(), before)
            lib.save()
            again = library.Library(root / "lib")
            self.assertEqual(again.manifest["voice"][name]["text"], "hello")
            from krish_clone import media

            probe = media.probe(written)
            self.assertAlmostEqual(probe.duration, 4.0, delta=0.05)
            self.assertFalse(list((root / "lib").rglob("*.part*")))

    def test_photos_are_copied_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            photo = root / "p.jpg"
            photo.write_bytes(b"\xff\xd8not really a jpeg")

            class Still:
                t = None
                source = "p.jpg"

                def as_dict(self):
                    return {"source": "p.jpg", "t": None, "tier": "keep"}

            lib = library.Library(root / "lib")
            name = lib.add_still("key", photo, Still())
            self.assertEqual((root / "lib" / "face" / "photos" / name).read_bytes(), photo.read_bytes())
            self.assertEqual(lib.manifest["face"][name]["source"], "key")


class ReportTest(unittest.TestCase):
    def test_inventory_states_minutes_against_the_targets(self):
        manifest = {"sources": {"k": {"file": "a.mp4", "kind": "video", "minutes": {"clean": 12.0, "review": 3.0},
                                      "rejected_reasons": ["noisy", "noisy", "too short"]}},
                    "voice": {"v": {"duration": 720.0, "tier": "clean"}, "r": {"duration": 180.0, "tier": "review"}},
                    "face": {"f": {"source": "k", "t": 1.0, "yaw": 0, "pitch": 0}}}
        text = report.render(manifest)
        self.assertIn("Clean: **12.0 min** against 30 min", text)
        self.assertIn("Shortfall to the minimum: **18.0 min**", text)
        self.assertIn("- noisy: 2", text)
        self.assertIn("| a.mp4 | video | 12.00 | 3.00 | 1 |", text)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(FFMPEG, "ffmpeg not installed")
class ExportTest(unittest.TestCase):
    def test_elevenlabs_export_meets_the_pvc_format(self):
        from krish_clone import export, media

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib = library.Library(root / "lib")
            master = make_audio(root / "m.wav", "aevalsrc='0.05*sin(2*PI*180*t)*lt(mod(t,1),0.7)':s=48000", 20)
            for start in (0.0, 8.0):
                lib.add_voice("k", master, voice.judge(voice.Segment(start, start + 6.0, f"s{start}", snr_db=40)))
            lib.save()
            result = export.elevenlabs(root / "lib", root / "out")
            target = root / "out" / "elevenlabs-pvc-01.mp3"
            self.assertEqual(len(result["files"]), 1)
            self.assertAlmostEqual(media.probe(target).duration, 12.8, delta=0.3)
            from content_watcher.read.audio import loudness

            level = loudness(target)
            self.assertAlmostEqual(level["integrated_lufs"], export.PVC_LOUDNESS, delta=1.5)
            self.assertLessEqual(level["true_peak_dbfs"], export.PVC_TRUE_PEAK + 0.5)
            with self.assertRaises(FileExistsError):
                export.elevenlabs(root / "lib", root / "out")
