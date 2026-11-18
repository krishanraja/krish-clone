"""clone faceprofile: everything a camera can measure about Krish's face, aggregated across his own photos.

Krish, 2026-11-17: "it should literally observe and aggregate everything possibly knowable about my face". This
module measures every photo it is given on his own machine (buffalo_l through onnxruntime, the same models as
`clone likeness`), keeps only the faces that are him (the dominant identity, then the identity floor), and
aggregates:

- geometry from the 68 landmarks, every length divided by the distance between his eye centres so the photo's
  size and distance drop out, angles measured after levelling the eye line;
- colour in CIELAB (L lightness 0 to 100, a green to red, b blue to yellow) of skin, beard, moustache, lips, eyes
  and the hair above the brow, so skin tone and beard density are numbers, not adjectives;
- expression (how open the mouth is, how far the corners lift), head pose and image quality;
- how each of those varies: the median and the middle half, so a generator is told what is fixed about him (his
  geometry) and what moves (beard length, expression).

Not measured: glasses. An edge test across the brow band (17 Nov 2026) scored two of his three glasses photos
lowest, because brows carry more edges than a thin frame, so it was removed; glasses are noted by eye instead.

The output is his biometric data. It is written only to the folder given with --out, which must lie outside this
repository (this repository is public); it never enters git and nothing here uploads it.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

GEOMETRY = (
    "face_width", "jaw_width", "chin_width", "nasion_to_chin", "nose_length", "nose_width", "nose_to_chin",
    "mouth_width", "upper_lip", "lower_lip", "philtrum", "chin_height", "intercanthal", "eye_width_left",
    "eye_width_right", "eye_open_left", "eye_open_right", "brow_height_left", "brow_height_right",
    "canthal_tilt_left", "canthal_tilt_right", "lower_face_ratio", "asymmetry",
)
COLOUR = ("skin", "forehead", "beard", "moustache", "lips", "eyes", "hair")
FRONTAL = 20.0  # degrees of yaw and pitch within which geometry is measured


def _d(p, a, b) -> float:
    return math.dist(p[a][:2], p[b][:2])


def _mean(p, idx) -> tuple[float, float]:
    xs = [p[i][0] for i in idx]
    ys = [p[i][1] for i in idx]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def level(points):
    """The 68 points rotated so the line between the eye centres is horizontal (roll removed)."""
    left, right = _mean(points, range(36, 42)), _mean(points, range(42, 48))
    angle = math.atan2(right[1] - left[1], right[0] - left[0])
    c, s = math.cos(-angle), math.sin(-angle)
    return [(x * c - y * s, x * s + y * c) for x, y, *_ in points]


def geometry(points) -> dict:
    """Ratios and angles from one face's 68 landmarks (iBUG layout). Left and right are as seen in the image."""
    p = level(points)
    eye_l, eye_r = _mean(p, range(36, 42)), _mean(p, range(42, 48))
    iod = math.dist(eye_l, eye_r)
    if iod <= 0:
        raise ValueError("the eyes coincide")
    r = lambda a, b: _d(p, a, b) / iod  # noqa: E731

    def tilt(inner, outer) -> float:
        # Positive when the outer corner sits higher than the inner one.
        dx = abs(p[outer][0] - p[inner][0])
        return math.degrees(math.atan2(p[inner][1] - p[outer][1], dx))

    mid_top, mid_bottom = p[27], p[8]
    axis = (mid_bottom[0] - mid_top[0], mid_bottom[1] - mid_top[1])
    norm = math.hypot(*axis) or 1.0
    ux, uy = axis[0] / norm, axis[1] / norm

    def mirror(pt):
        vx, vy = pt[0] - mid_top[0], pt[1] - mid_top[1]
        along = vx * ux + vy * uy
        px, py = mid_top[0] + along * ux, mid_top[1] + along * uy
        return 2 * px - pt[0], 2 * py - pt[1]

    pairs = [(0, 16), (2, 14), (4, 12), (6, 10), (17, 26), (19, 24), (21, 22), (36, 45), (39, 42), (31, 35), (48, 54)]
    asym = sum(math.dist(mirror(p[a]), p[b]) for a, b in pairs) / len(pairs) / iod
    return {
        "face_width": r(0, 16), "jaw_width": r(4, 12), "chin_width": r(6, 10), "nasion_to_chin": r(27, 8),
        "nose_length": r(27, 33), "nose_width": r(31, 35), "nose_to_chin": r(33, 8), "mouth_width": r(48, 54),
        "upper_lip": r(51, 62), "lower_lip": r(66, 57), "philtrum": r(33, 51), "chin_height": r(57, 8),
        "intercanthal": r(39, 42), "eye_width_left": r(36, 39), "eye_width_right": r(42, 45),
        "eye_open_left": (_d(p, 37, 41) + _d(p, 38, 40)) / 2 / max(_d(p, 36, 39), 1e-6),
        "eye_open_right": (_d(p, 43, 47) + _d(p, 44, 46)) / 2 / max(_d(p, 42, 45), 1e-6),
        "brow_height_left": (_mean(p, range(36, 42))[1] - _mean(p, range(17, 22))[1]) / iod,
        "brow_height_right": (_mean(p, range(42, 48))[1] - _mean(p, range(22, 27))[1]) / iod,
        "canthal_tilt_left": tilt(39, 36), "canthal_tilt_right": tilt(42, 45),
        "lower_face_ratio": _d(p, 33, 8) / max(_d(p, 27, 33), 1e-6), "asymmetry": asym,
    }


def expression(points) -> dict:
    """Mouth opening and how far the mouth corners sit above the lip centre (positive: a smile), both per eye gap."""
    p = level(points)
    iod = math.dist(_mean(p, range(36, 42)), _mean(p, range(42, 48)))
    centre = (p[62][1] + p[66][1]) / 2
    corners = (p[48][1] + p[54][1]) / 2
    return {"mouth_open": _d(p, 62, 66) / iod, "smile": (centre - corners) / iod}


def _patch(image, centre, radius):
    import numpy

    h, w = image.shape[:2]
    x, y, rr = int(round(centre[0])), int(round(centre[1])), max(2, int(round(radius)))
    if x - rr < 0 or y - rr < 0 or x + rr >= w or y + rr >= h:
        return None
    return image[y - rr:y + rr, x - rr:x + rr].reshape(-1, 3).astype(numpy.float32)


def colour(image, points) -> dict:
    """Median CIELAB of each region, or None where it falls outside the photo. Points are in image pixels."""
    import cv2
    import numpy

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    p = [(float(x), float(y)) for x, y, *_ in points]
    iod = math.dist(_mean(p, range(36, 42)), _mean(p, range(42, 48)))
    up = (p[27][0] - p[8][0], p[27][1] - p[8][1])
    n = math.hypot(*up) or 1.0
    up = (up[0] / n, up[1] / n)

    def at(base, ahead):
        return base[0] + up[0] * ahead * iod, base[1] + up[1] * ahead * iod

    def mid(a, b):
        return (p[a][0] + p[b][0]) / 2, (p[a][1] + p[b][1]) / 2

    brow = _mean(p, range(17, 27))
    regions = {
        "skin": [((p[2][0] + p[31][0] + p[41][0]) / 3, (p[2][1] + p[31][1] + p[41][1]) / 3),
                 ((p[14][0] + p[35][0] + p[46][0]) / 3, (p[14][1] + p[35][1] + p[46][1]) / 3)],
        "forehead": [at(brow, 0.35)],
        "beard": [at(p[8], 0.22), mid(5, 57), mid(11, 57)],
        "moustache": [mid(33, 51)],
        "lips": [mid(51, 57)],
        "eyes": [_mean(p, range(36, 42)), _mean(p, range(42, 48))],
        "hair": [at(brow, 1.05)],
    }
    radius = {"skin": 0.12, "forehead": 0.15, "beard": 0.1, "moustache": 0.05, "lips": 0.05, "eyes": 0.06, "hair": 0.12}
    out = {}
    for name, centres in regions.items():
        pixels = [px for c in centres if (px := _patch(lab, c, radius[name] * iod)) is not None]
        if not pixels:
            out[name] = None
            continue
        stack = numpy.concatenate(pixels)
        if name == "eyes":  # the iris and pupil are the darkest third of the eye patch
            stack = stack[stack[:, 0] <= numpy.percentile(stack[:, 0], 33)]
        med = numpy.median(stack, axis=0)
        out[name] = {"L": round(float(med[0]) * 100 / 255, 1), "a": round(float(med[1]) - 128, 1),
                     "b": round(float(med[2]) - 128, 1)}
    return out


def _stats(values: list[float]) -> dict:
    vals = sorted(v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v)))
    if not vals:
        return {"n": 0}

    def q(f):
        k = (len(vals) - 1) * f
        lo, hi = math.floor(k), math.ceil(k)
        return vals[lo] + (vals[hi] - vals[lo]) * (k - lo)

    med = q(0.5)
    spread = q(0.75) - q(0.25)
    return {"n": len(vals), "median": round(med, 3), "p25": round(q(0.25), 3), "p75": round(q(0.75), 3),
            "min": round(vals[0], 3), "max": round(vals[-1], 3),
            "variation": round(spread / abs(med), 3) if med else None}


def aggregate(records: list[dict]) -> dict:
    """Medians and middle halves across the photos that are him; geometry only from near-frontal faces."""
    frontal = [r for r in records if r.get("frontal")]
    out = {"photos": len(records), "frontal": len(frontal), "geometry": {}, "colour": {}, "expression": {}, "other": {}}
    for key in GEOMETRY:
        out["geometry"][key] = _stats([r["geometry"][key] for r in frontal])
    for region in COLOUR:
        for ch in ("L", "a", "b"):
            out["colour"][f"{region}_{ch}"] = _stats([(r["colour"].get(region) or {}).get(ch) for r in records])
    for key in ("mouth_open", "smile"):
        out["expression"][key] = _stats([r["expression"][key] for r in frontal])
    beard = [((r["colour"].get("skin") or {}).get("L") or 0) - ((r["colour"].get("beard") or {}).get("L") or 0)
             for r in records if r["colour"].get("skin") and r["colour"].get("beard")]
    out["other"]["beard_darkness"] = _stats(beard)
    out["other"]["identity"] = _stats([r["identity"] for r in records])
    out["other"]["yaw"] = _stats([r["pose"][1] for r in records])
    stable = sorted((k for k, v in out["geometry"].items() if v.get("variation") is not None and v["variation"] <= 0.06),
                    key=lambda k: out["geometry"][k]["variation"])
    out["stable_geometry"] = stable
    return out


def profile(paths: list[Path], detector, *, floor: float) -> dict:
    """Measure every photo, keep the faces that are him, and aggregate."""
    from . import face

    found = []
    for path in paths:
        image = face.read_image(path)
        if image is None:
            found.append({"file": path.name, "skipped": "unreadable"})
            continue
        faces = detector.detect(image)
        if not faces or faces[0].get("embedding") is None:
            found.append({"file": path.name, "skipped": "no face"})
            continue
        largest = max(faces, key=lambda f: (f["box"][3] - f["box"][1]) * (f["box"][2] - f["box"][0]))
        found.append({"file": path.name, "image": image, "face": largest, "others": len(faces) - 1})
    with_face = [f for f in found if "face" in f]
    gallery, report = face.Gallery.dominant([f["face"]["embedding"] for f in with_face], minimum=3)
    records, skipped = [], [f for f in found if "skipped" in f]
    for f in with_face:
        identity = gallery.similarity(f["face"]["embedding"])
        if identity is None or identity < floor:
            skipped.append({"file": f["file"], "skipped": f"not him or unclear (identity {identity})"})
            continue
        image, box = f["image"], f["face"]["box"]
        points = detector.app.landmarks68(image, box).tolist()
        pitch, yaw, roll = f["face"]["pose"]
        rec = {"file": f["file"], "identity": identity, "pose": [round(pitch, 1), round(yaw, 1), round(roll, 1)],
               "face_px": int(box[3] - box[1]), "other_faces": f["others"],
               "frontal": abs(yaw) <= FRONTAL and abs(pitch) <= FRONTAL,
               "geometry": {k: round(v, 4) for k, v in geometry(points).items()},
               "expression": {k: round(v, 4) for k, v in expression(points).items()},
               "colour": colour(image, points)}
        records.append(rec)
    return {"identity_groups": report, "floor": floor, "aggregate": aggregate(records), "per_photo": records,
            "skipped": skipped}


def markdown(result: dict) -> str:
    """A plain summary for Krish and for a generator brief."""
    agg = result["aggregate"]
    lines = [f"# Face profile: {agg['photos']} photos of Krish ({agg['frontal']} near-frontal)", "",
             "Lengths are per eye-centre distance; angles in degrees; colours in CIELAB (L 0 to 100).", "",
             "## Geometry (near-frontal photos)", "", "| Measure | Median | Middle half | Variation |", "|---|---|---|---|"]
    for k, v in agg["geometry"].items():
        if v.get("n"):
            lines.append(f"| {k} | {v['median']} | {v['p25']} to {v['p75']} | {v['variation']} |")
    lines += ["", "Most stable (vary least across photos): " + ", ".join(agg["stable_geometry"][:10]), "",
              "## Colour", "", "| Region | L | a | b |", "|---|---|---|---|"]
    for region in COLOUR:
        vals = [agg["colour"][f"{region}_{c}"] for c in ("L", "a", "b")]
        if vals[0].get("n"):
            lines.append(f"| {region} | " + " | ".join(f"{v['median']} ({v['p25']} to {v['p75']})" for v in vals) + " |")
    o = agg["other"]
    lines += ["", "## Other", "",
              f"- Beard darkness (skin L minus beard L): {o['beard_darkness'].get('median')} "
              f"(middle half {o['beard_darkness'].get('p25')} to {o['beard_darkness'].get('p75')})",
              f"- Smile index: {agg['expression']['smile'].get('median')}; mouth open: {agg['expression']['mouth_open'].get('median')}",
              f"- Identity against his own centroid: {o['identity'].get('median')} (floor {result['floor']})",
              "", f"Skipped: {len(result['skipped'])} photos (no face, unreadable, or not him)."]
    return "\n".join(lines) + "\n"
