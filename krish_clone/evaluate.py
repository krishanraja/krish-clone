"""Is the clone indistinguishable? Two tests that do not depend on anyone's opinion of it.

1. Speaker similarity: ECAPA embeddings of cloned clips compared with real ones. The bar is the
   spread of real Krish against real Krish (leave one out), not an arbitrary number.
2. A blind A/B pack: real and cloned clips paired and shuffled, with the key kept apart, so people
   who know him pick which one is the clone. Pass when they do no better than 60%.
"""

from __future__ import annotations

import csv
import json
import math
import random
import shutil
from pathlib import Path

PASS_SHARE = 0.60


def voice(real: list[Path], clone: list[Path], models: Path) -> dict:
    import numpy

    from . import media, speaker

    if len(real) < 3:
        raise ValueError("need at least three real clips to measure Krish's own spread")
    verifier = speaker.Verifier(real[:1], models)  # loads the model; centroids are rebuilt below
    real_vectors = [verifier.embed(media.samples16k(p)) for p in real]
    clone_vectors = [verifier.embed(media.samples16k(p)) for p in clone]

    def centroid(vectors):
        mean = numpy.mean(vectors, axis=0)
        return mean / numpy.linalg.norm(mean)

    real_scores = [float(v @ centroid(real_vectors[:i] + real_vectors[i + 1:])) for i, v in enumerate(real_vectors)]
    everyone = centroid(real_vectors)
    clone_scores = [float(v @ everyone) for v in clone_vectors]
    floor = float(numpy.percentile(real_scores, 5))
    median = float(numpy.median(clone_scores))
    return {
        "real_vs_real": {"min": round(min(real_scores), 3), "p5": round(floor, 3), "median": round(float(numpy.median(real_scores)), 3)},
        "clone_vs_real": {"min": round(min(clone_scores), 3), "median": round(median, 3), "scores": [round(s, 3) for s in clone_scores]},
        "verdict": "pass" if median >= floor else "fail",
        "rule": "the clone's median similarity sits at or above the 5th percentile of real Krish against real Krish",
    }


def ab_pack(real: list[Path], clone: list[Path], out: Path, *, seed: int | None = None) -> dict:
    """Pairs of (real, clone) shuffled into A and B. The key goes beside the pack, never inside it."""
    if not real or not clone:
        raise ValueError("need real and cloned clips")
    rng = random.Random(seed)
    pack = out / "pack"
    if pack.exists() and any(pack.iterdir()):
        raise FileExistsError(f"{pack} already holds a pack; choose a new --out")
    pack.mkdir(parents=True, exist_ok=True)
    pairs = []
    for number, (r, c) in enumerate(zip(real, clone), 1):
        clone_is = rng.choice("AB")
        a, b = (c, r) if clone_is == "A" else (r, c)
        name = f"pair_{number:02d}"
        shutil.copyfile(a, pack / f"{name}_A{a.suffix.lower()}")
        shutil.copyfile(b, pack / f"{name}_B{b.suffix.lower()}")
        pairs.append({"pair": name, "clone": clone_is, "real_file": r.name, "clone_file": c.name})
    key_file = out / "KEY-do-not-share.json"
    key = {"pairs": pairs, "key_file": str(key_file)}
    key_file.write_text(json.dumps(key, indent=2), encoding="utf-8")
    with (pack / "answers.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["listener", "pair", "choice"])
        for pair in pairs:
            writer.writerow(["your name", pair["pair"], "A or B: which one is the clone?"])
    (pack / "HOW-TO.txt").write_text(
        "Each pair has one real recording of Krish and one generated. Listen to both, then write A or B in\n"
        "answers.csv for the one you think is generated. Guess if unsure. Do not compare notes.\n", encoding="utf-8")
    return key


def _binomial_tail(k: int, n: int, p: float = 0.5) -> float:
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def ab_score(key_path: Path, answers_path: Path) -> dict:
    key = {p["pair"]: p["clone"] for p in json.loads(key_path.read_text(encoding="utf-8"))["pairs"]}
    total = correct = 0
    listeners: dict[str, list[int]] = {}
    with answers_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            choice = (row.get("choice") or "").strip().upper()[:1]
            if row.get("pair") not in key or choice not in ("A", "B"):
                continue
            hit = int(choice == key[row["pair"]])
            total += 1
            correct += hit
            listeners.setdefault(row.get("listener", "?"), []).append(hit)
    if not total:
        raise ValueError("no usable answers")
    share = correct / total
    return {
        "answers": total, "listeners": len(listeners), "picked_the_clone": round(share, 3),
        "chance_of_doing_this_well_by_guessing": round(_binomial_tail(correct, total), 4),
        "per_listener": {name: round(sum(h) / len(h), 2) for name, h in listeners.items()},
        "verdict": "pass" if share <= PASS_SHARE else "fail",
        "rule": f"people who know Krish pick the clone in at most {PASS_SHARE:.0%} of pairs",
    }
