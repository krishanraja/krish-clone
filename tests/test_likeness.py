"""clone likeness on generated embeddings only: no face of Krish's enters the repository."""

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

HAS_NUMPY = importlib.util.find_spec("numpy") is not None


def person(rng, base, noise, n):
    """n faces of one identity: its base direction plus noise, about 0.8 to the base at noise 0.03 in 512 dims."""
    import numpy

    faces = base + rng.normal(0, noise, (n, base.size))
    return [f / numpy.linalg.norm(f) for f in faces]


@unittest.skipUnless(HAS_NUMPY, "numpy not installed")
class LikenessTest(unittest.TestCase):
    def setUp(self):
        import numpy

        from krish_clone import likeness

        self.likeness = likeness
        self.rng = numpy.random.default_rng(7)
        base = self.rng.normal(0, 1, 512)
        self.krish = base / numpy.linalg.norm(base)
        other = self.rng.normal(0, 1, 512)
        self.stranger = other / numpy.linalg.norm(other)
        self.real = {f"photo{i}.jpg": person(self.rng, self.krish, 0.03, 1) for i in range(8)}

    def test_a_faithful_generated_video_passes(self):
        clip = {"embeddings": person(self.rng, self.krish, 0.03, 40), "sampled": 40}
        result = self.likeness.score(self.real, {"heygen.mp4": clip})
        self.assertEqual(result["verdict"], "pass", result["clones"])
        self.assertGreater(result["clones"]["heygen.mp4"]["median"], 0.7)

    def test_someone_else_fails_fidelity_and_drift(self):
        clip = {"embeddings": person(self.rng, self.stranger, 0.03, 20), "sampled": 20}
        entry = self.likeness.score(self.real, {"other.mp4": clip})["clones"]["other.mp4"]
        self.assertEqual(entry["verdict"], "fail")
        self.assertFalse(entry["checks"]["fidelity"])
        self.assertFalse(entry["checks"]["no drift"])

    def test_a_clip_that_drifts_away_for_a_stretch_fails_although_its_median_is_him(self):
        frames = person(self.rng, self.krish, 0.03, 32) + person(self.rng, self.stranger, 0.03, 8)
        entry = self.likeness.score(self.real, {"drift.mp4": {"embeddings": frames, "sampled": 40}})["clones"]["drift.mp4"]
        self.assertTrue(entry["checks"]["fidelity"], entry)
        self.assertFalse(entry["checks"]["no drift"], entry)
        self.assertEqual(entry["verdict"], "fail")

    def test_a_lookalike_stretch_above_the_library_floor_still_counts_as_drift(self):
        import numpy

        # Frames at about 0.65 to Krish: above the library's 0.55, below his own spread, like the prompted
        # lookalikes in the synthetic test.
        lookalike = []
        for v in person(self.rng, self.stranger, 0.01, 8):
            mixed = 0.65 * self.krish + numpy.sqrt(1 - 0.65 ** 2) * v
            lookalike.append(mixed / numpy.linalg.norm(mixed))
        frames = person(self.rng, self.krish, 0.03, 32) + lookalike
        result = self.likeness.score(self.real, {"swap.mp4": {"embeddings": frames, "sampled": 40}})
        entry = result["clones"]["swap.mp4"]
        self.assertGreater(entry["worst"], 0.55)
        self.assertTrue(entry["checks"]["fidelity"], entry)
        self.assertFalse(entry["checks"]["no drift"], entry)

    def test_a_video_that_loses_the_face_fails_presence(self):
        clip = {"embeddings": person(self.rng, self.krish, 0.03, 30), "sampled": 40}
        entry = self.likeness.score(self.real, {"lost.mp4": clip})["clones"]["lost.mp4"]
        self.assertEqual(entry["present"], 0.75)
        self.assertFalse(entry["checks"]["face present"])
        self.assertEqual(entry["verdict"], "fail")

    def test_a_generated_file_with_no_face_fails(self):
        entry = self.likeness.score(self.real, {"empty.png": {"embeddings": [], "sampled": 1}})["clones"]["empty.png"]
        self.assertEqual(entry["verdict"], "fail")

    def test_fewer_than_three_real_files_refuses(self):
        with self.assertRaises(ValueError):
            self.likeness.score(dict(list(self.real.items())[:2]), {"x.png": {"embeddings": [self.krish], "sampled": 1}})

    def test_one_long_real_video_does_not_outvote_the_photos(self):
        import numpy

        # A long real video of someone else would drag a frame-weighted centroid away from Krish;
        # each file weighs the same, so the photos still define him.
        real = dict(self.real) | {"long.mp4": person(self.rng, self.stranger, 0.03, 500)}
        result = self.likeness.score(real, {"k.png": {"embeddings": person(self.rng, self.krish, 0.03, 1), "sampled": 1}})
        frame_weighted = numpy.mean([v for vectors in real.values() for v in vectors], axis=0)
        frame_weighted /= numpy.linalg.norm(frame_weighted)
        self.assertLess(float(self.krish @ frame_weighted), 0.5)
        self.assertGreater(result["clones"]["k.png"]["median"], 0.6)
        self.assertLess(result["real_vs_real"]["per_file"]["long.mp4"]["median"], 0.55)

    def test_generated_files_that_disagree_with_each_other_are_reported(self):
        clones = {"a.png": {"embeddings": person(self.rng, self.krish, 0.03, 1), "sampled": 1},
                  "b.png": {"embeddings": person(self.rng, self.stranger, 0.03, 1), "sampled": 1}}
        result = self.likeness.score(self.real, clones)
        self.assertEqual(result["clone_vs_clone"]["pairs"], 1)
        self.assertLess(result["clone_vs_clone"]["min"], 0.3)
        self.assertEqual(result["verdict"], "fail")


@unittest.skipUnless(HAS_NUMPY, "numpy not installed")
class LikenessCommandTest(unittest.TestCase):
    def test_the_command_prints_the_result_and_exits_by_verdict(self):
        from krish_clone import cli, likeness

        for verdict, code in (("pass", 0), ("fail", 1)):
            with self.subTest(verdict), mock.patch("krish_clone.face.Detector") as detector, \
                    mock.patch.object(likeness, "likeness", return_value={"verdict": verdict}) as run, \
                    mock.patch.object(cli, "_files", side_effect=lambda paths: paths):
                out = io.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(cli.main(["likeness", "--real", "a.jpg", "b.jpg", "c.jpg", "--clone", "g.mp4"]), code)
                self.assertEqual(json.loads(out.getvalue())["verdict"], verdict)
                detector.assert_called_once()
                self.assertEqual(detector.call_args.args[0], "onnx")
                self.assertEqual(run.call_args.args[1], [Path("g.mp4")])


if __name__ == "__main__":
    unittest.main()
