import importlib.util
import unittest

HAS_CV = importlib.util.find_spec("cv2") is not None and importlib.util.find_spec("numpy") is not None


def unit(vector):
    import numpy

    v = numpy.array(vector, dtype=numpy.float32)
    return v / numpy.linalg.norm(v)


def textured(h=1080, w=1080, seed=0):
    import numpy

    return numpy.random.default_rng(seed).integers(40, 220, (h, w, 3), dtype=numpy.uint8)


@unittest.skipUnless(HAS_CV, "OpenCV and numpy not installed")
class FaceTest(unittest.TestCase):
    def setUp(self):
        from krish_clone import face

        self.face = face
        self.krish = unit([1, 0.1, 0])
        self.gallery = face.Gallery([unit([1, 0, 0]), unit([1, 0.2, 0])])

    def found(self, box, embedding=None, pose=(0.0, 0.0, 0.0), det=0.9):
        return {"box": box, "det": det, "embedding": self.krish if embedding is None else embedding, "pose": list(pose)}

    def measure(self, found, image=None, t=1.0):
        return self.face.judge(self.face.score(textured() if image is None else image, found, source="v.mp4", t=t,
                                               gallery=self.gallery), need_identity=True)

    def test_a_large_sharp_frontal_krish_face_is_kept(self):
        kept = self.measure(self.found([300, 200, 700, 700]))
        self.assertEqual(kept.tier, "keep", kept.reasons)
        self.assertGreater(kept.identity, 0.9)

    def test_someone_else_is_rejected(self):
        guest = self.measure(self.found([300, 200, 700, 700], embedding=unit([0, 1, 0])))
        self.assertEqual(guest.tier, "rejected")
        self.assertTrue(any(r.startswith("not Krish") for r in guest.reasons))

    def test_small_soft_dark_turned_and_cut_off_faces_are_rejected(self):
        import numpy

        cases = {
            "face too small": (self.found([500, 500, 560, 580]), None),
            "soft": (self.found([300, 200, 700, 700]), numpy.full((1080, 1080, 3), 128, numpy.uint8)),
            "exposure": (self.found([300, 200, 700, 700]), numpy.full((1080, 1080, 3), 10, numpy.uint8)),
            "turned away": (self.found([300, 200, 700, 700], pose=(0.0, 70.0, 0.0)), None),
            "face cut off by the frame edge": (self.found([-200, 200, 300, 700]), None),
        }
        for reason, (found, image) in cases.items():
            with self.subTest(reason):
                result = self.measure(found, image)
                self.assertEqual(result.tier, "rejected")
                self.assertTrue(any(r.startswith(reason) for r in result.reasons), result.reasons)

    def test_identity_is_required_only_when_a_gallery_was_given(self):
        face = self.face
        unchecked = face.judge(face.score(textured(), self.found([300, 200, 700, 700], embedding=None) | {"embedding": None},
                                          source="p.jpg", t=None, gallery=None), need_identity=False)
        self.assertEqual(unchecked.tier, "keep")
        self.assertIn("identity not checked", unchecked.notes)

    def test_select_spreads_poses_and_drops_near_duplicates(self):
        face = self.face
        made = []
        for i, yaw in enumerate([0, 0, 0, 0, 30, 30, -30]):
            f = face.Face("v.mp4", float(i), [0, 0, 1, 1], 0.9, 0.5, 400, 300.0, 120.0, yaw=float(yaw), pitch=0.0,
                          hash=(i * 0x0F0F0F0F0F) & 0xFFFFFFFFFFFFFFFF, quality=1 - i * 0.01, tier="keep")
            made.append(f)
        made[1].hash = made[0].hash  # the same still twice
        chosen = face.select(made, limit=3, per_bin=1)
        self.assertEqual(len(chosen), 3)
        self.assertEqual({face.pose_bin(f) for f in chosen}, {face.pose_bin(made[0]), face.pose_bin(made[4]), face.pose_bin(made[6])})
        self.assertIn("near-duplicate of a chosen still", made[1].notes)

    def test_gallery_centroid(self):
        self.assertAlmostEqual(self.gallery.similarity(self.gallery.centroid), 1.0, places=5)
        with self.assertRaises(ValueError):
            self.face.Gallery([])


if __name__ == "__main__":
    unittest.main()
