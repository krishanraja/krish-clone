"""clone faceprofile: geometry from synthetic landmarks, the aggregate, and the out-of-repository rule."""
import math
import unittest
from pathlib import Path

from krish_clone import faceprofile


def face(shift=0.0, scale=1.0, roll=0.0):
    """A plausible 68-point face (iBUG layout), symmetric about x = 0, eyes 60 apart."""
    pts = [(0, 0)] * 68
    jaw = [(-70, -10), (-69, 10), (-66, 30), (-61, 48), (-52, 64), (-40, 77), (-26, 87), (-13, 93), (0, 95)]
    for i, (x, y) in enumerate(jaw):
        pts[i] = (x, y)
        pts[16 - i] = (-x, y)
    for i, (x, y) in enumerate([(-55, -40), (-45, -46), (-34, -48), (-23, -46), (-12, -42)]):
        pts[17 + i] = (x, y)
        pts[26 - i] = (-x, y)
    for i, y in enumerate([-30, -18, -6, 6]):
        pts[27 + i] = (0, y)
    for i, (x, y) in enumerate([(-14, 16), (-7, 19), (0, 20), (7, 19), (14, 16)]):
        pts[31 + i] = (x, y)
    right = [(-45, -28), (-37, -33), (-27, -33), (-18, -28), (-27, -24), (-37, -24)]
    for i, (x, y) in enumerate(right):
        pts[36 + i] = (x, y)
    left = [(18, -28), (27, -33), (37, -33), (45, -28), (37, -24), (27, -24)]
    for i, (x, y) in enumerate(left):
        pts[42 + i] = (x, y)
    outer = [(-25, 45), (-15, 40), (-6, 38), (0, 39), (6, 38), (15, 40), (25, 45), (15, 52), (6, 55), (0, 56), (-6, 55), (-15, 52)]
    for i, p in enumerate(outer):
        pts[48 + i] = p
    inner = [(-20, 45), (-6, 43), (0, 43), (6, 43), (20, 45), (6, 48), (0, 48), (-6, 48)]
    for i, p in enumerate(inner):
        pts[60 + i] = p
    c, s = math.cos(roll), math.sin(roll)
    return [((x * c - y * s) * scale + shift, (x * s + y * c) * scale + shift, 0.0) for x, y in pts]


class FaceProfileTest(unittest.TestCase):
    def test_geometry_ignores_size_position_and_roll(self):
        a = faceprofile.geometry(face())
        b = faceprofile.geometry(face(shift=300, scale=2.5, roll=0.3))
        for key in faceprofile.GEOMETRY:
            self.assertAlmostEqual(a[key], b[key], places=4, msg=key)

    def test_a_symmetric_face_measures_symmetric(self):
        g = faceprofile.geometry(face())
        self.assertAlmostEqual(g["asymmetry"], 0.0, places=6)
        self.assertAlmostEqual(g["eye_width_left"], g["eye_width_right"], places=6)
        self.assertAlmostEqual(g["canthal_tilt_left"], g["canthal_tilt_right"], places=6)
        self.assertAlmostEqual(g["face_width"], 140 / (2 * 191 / 6), places=4)

    def test_aggregate_takes_geometry_only_from_frontal_faces(self):
        rec = {"geometry": faceprofile.geometry(face()), "expression": faceprofile.expression(face()),
               "colour": {"skin": {"L": 60, "a": 12, "b": 18}, "beard": {"L": 30, "a": 3, "b": 5}},
               "identity": 0.8, "pose": [0, 0, 0], "frontal": True}
        side = dict(rec, frontal=False, geometry={k: 99.0 for k in faceprofile.GEOMETRY})
        agg = faceprofile.aggregate([rec, side])
        self.assertEqual(agg["frontal"], 1)
        self.assertEqual(agg["geometry"]["face_width"]["n"], 1)
        self.assertEqual(agg["other"]["beard_darkness"]["median"], 30)

    def test_the_profile_is_refused_inside_the_repository(self):
        from krish_clone import cli
        repo = Path(cli.__file__).resolve().parents[1]
        args = type("A", (), {"out": str(repo / "profile"), "photos": [], "floor": 0.55})()
        self.assertEqual(cli._faceprofile(args), 2)


if __name__ == "__main__":
    unittest.main()
