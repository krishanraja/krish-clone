"""Is this Krish's voice? ECAPA speaker embeddings compared with enrolment clips he confirmed.

Optional: needs the `speaker` extra (speechbrain, torch). Without it, segments are marked
"speaker not verified" and nothing pretends otherwise.
"""

from __future__ import annotations

from pathlib import Path

MODEL = "speechbrain/spkrec-ecapa-voxceleb"


class Verifier:
    def __init__(self, enrolment: list[Path], cache: Path):
        import numpy
        from speechbrain.inference.speaker import EncoderClassifier  # type: ignore

        from . import media

        self.model = EncoderClassifier.from_hparams(source=MODEL, savedir=str(cache / "ecapa"), run_opts={"device": "cpu"})
        embeddings = [self.embed(media.samples16k(path)) for path in enrolment]
        if not embeddings:
            raise ValueError("speaker verification needs at least one enrolment clip")
        centroid = numpy.mean(embeddings, axis=0)
        self.centroid = centroid / numpy.linalg.norm(centroid)

    def embed(self, samples):
        import numpy
        import torch

        with torch.no_grad():
            vector = self.model.encode_batch(torch.from_numpy(numpy.ascontiguousarray(samples)).unsqueeze(0))
        vector = vector.squeeze().cpu().numpy()
        return vector / numpy.linalg.norm(vector)

    def similarity(self, samples, rate: int = 16_000) -> float | None:
        if len(samples) < rate:  # under a second is not enough voice to judge
            return None
        return round(float(self.embed(samples) @ self.centroid), 3)


def available() -> bool:
    try:
        import speechbrain  # noqa: F401
        import torch  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True
