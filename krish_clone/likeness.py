"""Does a generated face stay Krish? Identity fidelity and consistency of generated stills and video.

The likeness counterpart of `clone evaluate`. Any generator's output (a HeyGen look, a talking-head
render, a still from another model) is judged the same way, on Krish's own machine: the largest face
in each real photo or sampled frame, and in each generated one, is embedded with ArcFace (buffalo_l,
the models the library already runs) and compared with real Krish. Nothing is uploaded and no
platform is called.

Three things are measured for each generated file:

1. Fidelity: its median identity reaches the 5th percentile of real Krish against real Krish,
   leaving one real file out, the same rule as the voice test.
2. Drift: its worst 5% of faces stay within 0.10 of that floor, so no stretch of a clip stops being
   him while ordinary frame-to-frame variation passes. The margin is provisional, set from the
   synthetic test (docs/GENERATORS.md: same-person variants within 0.04 of one another, lookalikes
   prompted toward the same description 0.2 or more below), and is to be recalibrated on the first
   real baseline. The library's absolute floor (0.55) is not used: it separates Krish from the real
   other people in his footage, but those generated lookalikes scored 0.54 to 0.68.
3. Presence: a generated video shows a face in at least 95% of sampled frames, the bar the twin
   pre-flight sets for a real take.

Across the generated files, how closely they agree with each other is reported but not judged:
a set of looks that are each "close enough" can still disagree with one another.
"""

from __future__ import annotations

from pathlib import Path

PRESENT = 0.95  # twin.FACE_PRESENT: share of sampled frames with a face
WORST = 5  # percentile of a file's own faces that must stay at or above the drift floor
DRIFT_MARGIN = 0.10  # provisional: how far below the fidelity floor a clip's worst faces may fall
MIN_REAL_FILES = 3


def _unit(vector):
    import numpy

    vector = numpy.asarray(vector, dtype=numpy.float32)
    return vector / numpy.linalg.norm(vector)


def _centroid(vectors):
    import numpy

    return _unit(numpy.mean([_unit(v) for v in vectors], axis=0))


def score(real: dict[str, list], clones: dict[str, dict]) -> dict:
    """Pure scoring over embeddings.

    real: file name -> the embeddings of its faces (one per photo, one per sampled frame).
    clones: file name -> {"embeddings": [...], "sampled": frames sampled (1 for a photo)}.
    Each real file weighs the same in a centroid, so one long video cannot outvote ten photos.
    """
    import numpy

    real = {name: vectors for name, vectors in real.items() if vectors}
    if len(real) < MIN_REAL_FILES:
        raise ValueError(f"need faces in at least {MIN_REAL_FILES} real files to measure Krish's own spread "
                         f"(found {len(real)})")
    file_centroids = {name: _centroid(vectors) for name, vectors in real.items()}

    real_files = {}
    for name, vectors in real.items():
        others = _centroid([c for other, c in file_centroids.items() if other != name])
        scores = [float(_unit(v) @ others) for v in vectors]
        real_files[name] = {"faces": len(scores), "median": round(float(numpy.median(scores)), 3),
                            "worst": round(float(numpy.percentile(scores, WORST)), 3)}
    medians = [entry["median"] for entry in real_files.values()]
    floor = float(numpy.percentile(medians, 5))
    drift_floor = floor - DRIFT_MARGIN
    everyone = _centroid(list(file_centroids.values()))

    judged, clone_centroids = {}, {}
    for name, found in clones.items():
        vectors = found.get("embeddings") or []
        sampled = max(1, int(found.get("sampled") or 1))
        present = len(vectors) / sampled
        entry = {"faces": len(vectors), "sampled": sampled, "present": round(min(1.0, present), 3)}
        checks = {"face present": present >= PRESENT}
        if vectors:
            scores = [float(_unit(v) @ everyone) for v in vectors]
            entry.update(median=round(float(numpy.median(scores)), 3), worst=round(float(numpy.percentile(scores, WORST)), 3),
                         min=round(min(scores), 3), spread=round(float(numpy.std(scores)), 3))
            checks["fidelity"] = entry["median"] >= round(floor, 3)
            checks["no drift"] = entry["worst"] >= round(drift_floor, 3)
            clone_centroids[name] = _centroid(vectors)
        else:
            checks["fidelity"] = checks["no drift"] = False
        entry["checks"] = checks
        entry["verdict"] = "pass" if all(checks.values()) else "fail"
        judged[name] = entry

    agreement = None
    names = sorted(clone_centroids)
    if len(names) > 1:
        pairs = [float(clone_centroids[a] @ clone_centroids[b]) for i, a in enumerate(names) for b in names[i + 1:]]
        agreement = {"pairs": len(pairs), "min": round(min(pairs), 3), "median": round(float(numpy.median(pairs)), 3)}

    return {
        "real_vs_real": {"files": len(real_files), "p5": round(floor, 3), "drift_floor": round(drift_floor, 3),
                         "median": round(float(numpy.median(medians)), 3),
                         "min": round(min(medians), 3), "per_file": real_files},
        "clones": judged,
        "clone_vs_clone": agreement,
        "verdict": "pass" if judged and all(e["verdict"] == "pass" for e in judged.values()) else "fail",
        "rule": (f"each generated file: its median identity at or above the 5th percentile of real Krish against real "
                 f"Krish (each real file scored against the others), its worst {WORST}% of faces no more than "
                 f"{DRIFT_MARGIN:.2f} below that, and a face in at least {PRESENT:.0%} of sampled frames"),
    }


def measure(paths: list[Path], detector, *, fps: float = 2.0) -> dict[str, dict]:
    """The largest face per photo or sampled frame, as embeddings, for each file. Reads only; writes nothing."""
    from . import face, media

    if detector.backend != "onnx":
        raise RuntimeError("likeness needs ArcFace identity (the onnx backend); install the face extra")
    measured = {}
    names = [p.name for p in paths]
    for path in paths:
        key = path.name if names.count(path.name) == 1 else str(path)
        if media.kind_of(path) == "photo":
            faces, sampled = face.faces_in_photo(path, detector), 1
        else:
            faces, info = face.faces_in_video(path, detector, fps=fps)
            sampled = info.get("frames", 0)
        usable = [f.embedding for f in faces if f.embedding is not None and f.det >= face.MIN_DET]
        measured[key] = {"embeddings": usable, "sampled": sampled}
    return measured


def likeness(real: list[Path], clone: list[Path], detector, *, fps: float = 2.0) -> dict:
    real_found = measure(real, detector, fps=fps)
    return score({name: found["embeddings"] for name, found in real_found.items()},
                 measure(clone, detector, fps=fps))
