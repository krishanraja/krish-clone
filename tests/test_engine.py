import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from krish_clone import evaluate, library, script, voice

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
HAS_CV = HAS_NUMPY and importlib.util.find_spec("cv2") is not None


def unit(values):
    import numpy

    v = numpy.array(values, dtype=numpy.float32)
    return v / numpy.linalg.norm(v)


@unittest.skipUnless(HAS_CV, "OpenCV and numpy not installed")
class GalleryTest(unittest.TestCase):
    def test_the_dominant_identity_becomes_krish(self):
        from krish_clone import face

        krish = [unit([1, 0.05 * i, 0]) for i in range(8)]
        guest = [unit([0, 1, 0.05 * i]) for i in range(3)]
        gallery, found = face.Gallery.dominant(krish + guest)
        self.assertEqual(found["largest"][:2], [8, 3])
        self.assertGreater(gallery.similarity(unit([1, 0.1, 0])), 0.9)
        self.assertLess(gallery.similarity(unit([0, 1, 0])), 0.3)

    def test_no_clear_winner_is_refused_not_guessed(self):
        from krish_clone import face

        with self.assertRaises(ValueError):
            face.Gallery.dominant([unit([1, 0, 0])] * 6 + [unit([0, 1, 0])] * 5)
        with self.assertRaises(ValueError):
            face.Gallery.dominant([unit([1, 0, 0])] * 3)

    def test_cache_round_trip_keeps_measures_and_drops_judgement(self):
        from krish_clone import face

        f = face.Face("v.mp4", 1.5, [0, 0, 10, 10], 0.9, 0.4, 300, 200.0, 120.0, yaw=5.0, pitch=1.0, roll=0.0,
                      hash=123456789, identity=0.9, tier="keep", embedding=unit([1, 2, 3]))
        back = face.from_cache(json.loads(json.dumps(face.to_cache([f]))))[0]
        self.assertEqual((back.t, back.sharpness, back.yaw, back.hash), (1.5, 200.0, 5.0, 123456789))
        self.assertIsNone(back.identity)
        self.assertAlmostEqual(float(back.embedding @ unit([1, 2, 3])), 1.0, places=3)


@unittest.skipUnless(HAS_CV, "OpenCV and numpy not installed")
class OnnxAlignmentTest(unittest.TestCase):
    def test_umeyama_recovers_a_similarity_transform(self):
        import numpy

        from krish_clone.faceonnx import ARCFACE_DST, _umeyama

        dst = numpy.array(ARCFACE_DST, dtype=numpy.float64)
        angle, scale, shift = 0.3, 2.5, numpy.array([40.0, -12.0])
        rotation = numpy.array([[numpy.cos(angle), -numpy.sin(angle)], [numpy.sin(angle), numpy.cos(angle)]])
        src = (dst - shift) @ numpy.linalg.inv(scale * rotation).T  # so that scale*R*src + shift == dst
        matrix = _umeyama(src, dst)
        mapped = src @ matrix[:, :2].T + matrix[:, 2]
        self.assertLess(float(numpy.abs(mapped - dst).max()), 1e-6)

    @unittest.skipUnless(importlib.util.find_spec("insightface") is not None, "insightface not installed")
    def test_parity_with_insightface_when_both_are_present(self):
        from insightface.app import FaceAnalysis
        import insightface

        from krish_clone.face import read_image
        from krish_clone.faceonnx import OnnxFaces

        image_path = Path(insightface.__file__).parent / "data" / "images" / "t1.jpg"
        reference = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"],
                                 allowed_modules=["detection", "recognition", "landmark_3d_68"])
        reference.prepare(ctx_id=-1, det_size=(640, 640))
        image = read_image(image_path)
        theirs = reference.get(image)
        ours = OnnxFaces(Path.home() / ".krish-clone").get(image)
        self.assertEqual(len(theirs), len(ours))
        for face in theirs:
            match = min(ours, key=lambda o: abs(o["box"][0] - face.bbox[0]) + abs(o["box"][1] - face.bbox[1]))
            self.assertGreater(float(face.normed_embedding @ match["embedding"]), 0.9999)
            self.assertLess(max(abs(a - b) for a, b in zip(face.pose, match["pose"])), 0.01)


@unittest.skipUnless(HAS_NUMPY, "numpy not installed")
class DedupeTest(unittest.TestCase):
    def contour(self, seed, seconds):
        import numpy

        rng = numpy.random.default_rng(seed)
        frames = int(seconds / voice.FRAME)
        words = numpy.repeat(rng.uniform(-35, -12, frames // 10 + 1), 10)[:frames]  # syllable-sized steps
        gaps = rng.random(frames) < 0.25
        return voice.envelope(numpy.where(gaps, -75.0, words))

    def test_the_same_audio_in_another_cut_is_found_despite_noise_and_offset(self):
        import numpy

        episode = self.contour(1, 120)
        other_cut = numpy.concatenate((self.contour(9, 7), episode[1000:3000] + numpy.random.default_rng(2).normal(0, 1.5, 2000)))
        other_cut = voice.envelope(other_cut)
        segment = voice.Segment(7 + 4.0, 7 + 12.0, "x")  # inside the shared stretch of the other cut
        self.assertEqual(voice.repeat_of(segment, other_cut, {"episode": episode}), "episode")
        fresh = voice.Segment(0.5, 6.5, "x")  # the other cut's own opening, never heard before
        self.assertIsNone(voice.repeat_of(fresh, other_cut, {"episode": episode}))
        self.assertIsNone(voice.repeat_of(segment, other_cut, {"unrelated": self.contour(5, 120)}))


class ScriptTest(unittest.TestCase):
    def test_stage_directions_meta_and_repeats_are_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "long video-script.md").write_text(
                "# Title\n\nThe video script (about 3 minutes). Square brackets say what is on screen.\n\n"
                "[Chart of prices]\n\nGoogle doubled the price of its newest AI on the first of December, and nobody noticed.\n\n"
                "KRISH: OpenAI cut its price, but only until November, so budget at the full price.\n\n"
                "## Changes from version 1\n\nDropped the section labels because nobody knows what they mean out loud.\n",
                encoding="utf-8")
            (root / "short video-script.md").write_text(
                "Google doubled the price of its newest AI on the first of December, and nobody noticed.\n", encoding="utf-8")
            (root / "youtube-and-substack-words.txt").write_text("Title: Why AI prices keep changing and more words", encoding="utf-8")
            files = sorted(p for p in root.iterdir() if script.is_script(p))
            built = script.build(files, minutes=1, wpm=150)
        self.assertNotIn("youtube", " ".join(built.sources))
        self.assertNotIn("Square brackets", built.markdown)
        self.assertNotIn("Chart of prices", built.markdown)
        self.assertNotIn("section labels", built.markdown)
        self.assertNotIn("KRISH:", built.markdown)
        # The short cut repeats the long one, so it is read once.
        self.assertEqual(built.markdown.count("Google doubled the price"), 1)
        self.assertEqual(built.markdown.count("OpenAI cut its price"), 1)
        self.assertIn("## Free talk", built.markdown)


class AbTest(unittest.TestCase):
    def test_pack_hides_the_key_and_scoring_applies_the_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = [root / f"real{i}.wav" for i in range(4)]
            clone = [root / f"clone{i}.wav" for i in range(4)]
            for path in real + clone:
                path.write_bytes(path.name.encode())
            key = evaluate.ab_pack(real, clone, root / "ab", seed=7)
            pack = root / "ab" / "pack"
            self.assertFalse(any("KEY" in p.name for p in pack.iterdir()))
            self.assertEqual(len(list(pack.glob("pair_*"))), 8)
            for pair in key["pairs"]:
                clone_file = next(pack.glob(f"{pair['pair']}_{pair['clone']}.*"))
                self.assertTrue(clone_file.read_bytes().startswith(b"clone"))
            answers = root / "answers.csv"
            with answers.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["listener", "pair", "choice"])
                for listener in ("ana", "ben"):
                    for i, pair in enumerate(key["pairs"]):
                        right = pair["clone"]
                        writer.writerow([listener, pair["pair"], right if i < 2 else ("A" if right == "B" else "B")])
            result = evaluate.ab_score(Path(key["key_file"]), answers)
            self.assertEqual(result["picked_the_clone"], 0.5)
            self.assertEqual(result["verdict"], "pass")
            with self.assertRaises(FileExistsError):
                evaluate.ab_pack(real, clone, root / "ab")


if __name__ == "__main__":
    unittest.main()
