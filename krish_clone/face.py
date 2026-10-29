"""Find frames and photos where Krish's face is sharp, well lit, large and plainly him.

Detection and identity come from insightface buffalo_l (ArcFace, 512 numbers per face), the
model contentarchives already runs over Krish's library, with its measured 0.55 cosine join
threshold. contentarchives never scored quality; this module adds sharpness, exposure, size and
head pose, then keeps a spread of poses rather than forty copies of the same angle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

from content_watcher.timeline.moments import dhash, hamming

from . import media

IDENTITY_FLOOR = 0.55  # contentarchives cluster_faces.py JOIN, measured on Krish's own library
MIN_SHARE = 0.12  # face height over frame height (contentarchives SUBJECT_SHARE)
MIN_FACE_PX = 160  # face height in pixels; smaller faces cannot teach skin or teeth
MIN_SHARPNESS = 60.0  # variance of the Laplacian on the face scaled to 256 px tall
MIN_DET = 0.6
EXPOSURE = (60.0, 200.0)  # mean face luminance outside this is too dark or blown
MAX_YAW, MAX_PITCH = 45.0, 30.0
SAME_PICTURE = 6  # dhash bits; closer than this is the same still
MAX_CUT_OFF = 0.01  # share of the face box allowed outside the frame; training stills need the whole head


@dataclass
class Face:
    source: str
    t: float | None
    box: list[int]
    det: float
    share: float
    face_px: int
    sharpness: float
    brightness: float
    cut_off: float = 0.0
    yaw: float | None = None
    pitch: float | None = None
    roll: float | None = None
    identity: float | None = None
    hash: int | None = None
    quality: float = 0.0
    tier: str = "rejected"
    reasons: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    embedding: object = field(default=None, repr=False)

    def as_dict(self) -> dict:
        data = asdict(self)
        data.pop("embedding")
        data["hash"] = f"{self.hash:016x}" if self.hash is not None else None
        return data


class Detector:
    """insightface when installed, else OpenCV's Haar detector with no identity and no pose."""

    def __init__(self, backend: str = "auto", det_size: int = 640):
        self.backend = None
        if backend in ("auto", "insightface"):
            try:
                from insightface.app import FaceAnalysis  # type: ignore

                self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"],
                                        allowed_modules=["detection", "recognition", "landmark_3d_68"])
                self.app.prepare(ctx_id=-1, det_size=(det_size, det_size))
                self.backend = "insightface"
            except Exception:  # noqa: BLE001 - any failure falls back, and the backend is recorded
                if backend == "insightface":
                    raise
        if self.backend is None:
            import cv2

            self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            self.backend = "haar"

    def detect(self, image) -> list[dict]:
        found = self._detect(image)
        if found:
            return found
        # A face that fills the frame defeats the detector's anchors: retry on a padded canvas.
        import cv2

        h, w = image.shape[:2]
        pad = int(max(h, w) * 0.3)
        padded = cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        found = self._detect(padded)
        for face in found:
            face["box"] = [face["box"][0] - pad, face["box"][1] - pad, face["box"][2] - pad, face["box"][3] - pad]
            face["padded"] = True
        return found

    def _detect(self, image) -> list[dict]:
        if self.backend == "insightface":
            found = []
            for face in self.app.get(image):
                pose = getattr(face, "pose", None)
                found.append({"box": [int(v) for v in face.bbox], "det": float(face.det_score),
                              "embedding": getattr(face, "normed_embedding", None),
                              "pose": [float(v) for v in pose] if pose is not None else None})
            return found
        import cv2

        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h = grey.shape[0]
        boxes = self.cascade.detectMultiScale(grey, scaleFactor=1.1, minNeighbors=5, minSize=(int(h * 0.08),) * 2)
        return [{"box": [int(x), int(y), int(x + w), int(y + hh)], "det": 1.0, "embedding": None, "pose": None}
                for x, y, w, hh in boxes]


class Gallery:
    """Krish's reference faces: the centroid every candidate is compared with."""

    def __init__(self, embeddings: list):
        import numpy

        if not embeddings:
            raise ValueError("a gallery needs at least one reference face")
        stack = numpy.stack(embeddings)
        centroid = stack.mean(axis=0)
        self.centroid = centroid / numpy.linalg.norm(centroid)
        self.size = len(embeddings)
        self.spread = [round(float(e @ self.centroid), 3) for e in stack]

    def similarity(self, embedding) -> float | None:
        if embedding is None:
            return None
        return round(float(embedding @ self.centroid), 3)

    @classmethod
    def from_photos(cls, paths: list[Path], detector: Detector) -> "Gallery":
        embeddings = []
        for path in paths:
            image = read_image(path)
            faces = detector.detect(image) if image is not None else []
            if faces and faces[0]["embedding"] is not None:
                largest = max(faces, key=lambda f: (f["box"][3] - f["box"][1]))
                embeddings.append(largest["embedding"])
        return cls(embeddings)


def read_image(path: Path):
    import cv2
    import numpy

    data = numpy.fromfile(str(path), dtype=numpy.uint8)  # survives non-ASCII Windows paths
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def score(image, found: dict, *, source: str, t: float | None, gallery: Gallery | None) -> Face:
    import cv2

    h, w = image.shape[:2]
    bx1, by1, bx2, by2 = found["box"]
    x1, y1, x2, y2 = max(0, bx1), max(0, by1), min(w, bx2), min(h, by2)
    whole = max(1, (bx2 - bx1) * (by2 - by1))
    cut_off = round(1 - max(0, x2 - x1) * max(0, y2 - y1) / whole, 3)
    crop = image[y1:y2, x1:x2]
    face_px = max(0, y2 - y1)
    if crop.size == 0:
        return Face(source, t, [x1, y1, x2, y2], found["det"], 0.0, 0, 0.0, 0.0, reasons=["face outside frame"])
    grey = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(grey, (max(1, int(grey.shape[1] * 256 / grey.shape[0])), 256))
    face = Face(
        source=source, t=t, box=[x1, y1, x2, y2], det=round(found["det"], 3), share=round(face_px / h, 3),
        face_px=face_px, sharpness=round(float(cv2.Laplacian(scaled, cv2.CV_64F).var()), 1),
        brightness=round(float(grey.mean()), 1), cut_off=cut_off, hash=dhash(scaled), embedding=found["embedding"],
    )
    if found["pose"] is not None:
        face.pitch, face.yaw, face.roll = (round(v, 1) for v in found["pose"])
    if gallery is not None:
        face.identity = gallery.similarity(found["embedding"])
    return face


def judge(face: Face, *, need_identity: bool) -> Face:
    r = face.reasons
    if face.det < MIN_DET:
        r.append(f"weak detection ({face.det})")
    if face.cut_off > MAX_CUT_OFF:
        r.append(f"face cut off by the frame edge ({face.cut_off:.0%})")
    if face.share < MIN_SHARE:
        r.append(f"face too small in frame ({face.share:.0%})")
    if face.face_px < MIN_FACE_PX:
        r.append(f"face too few pixels ({face.face_px}px)")
    if face.sharpness < MIN_SHARPNESS:
        r.append(f"soft ({face.sharpness})")
    if not EXPOSURE[0] <= face.brightness <= EXPOSURE[1]:
        r.append(f"exposure ({face.brightness})")
    if face.yaw is not None and (abs(face.yaw) > MAX_YAW or abs(face.pitch) > MAX_PITCH):
        r.append(f"turned away (yaw {face.yaw}, pitch {face.pitch})")
    if face.identity is not None and face.identity < IDENTITY_FLOOR:
        r.append(f"not Krish (identity {face.identity})")
    if face.identity is None:
        (r if need_identity else face.notes).append("identity not checked")
    if face.yaw is None:
        face.notes.append("pose not measured")
    face.tier = "rejected" if r else "keep"
    # Quality ranks keepers: sharpness and size matter most, then how frontal the face is.
    frontal = 1.0 - min(1.0, (abs(face.yaw or 0) / MAX_YAW + abs(face.pitch or 0) / MAX_PITCH) / 2)
    face.quality = round(min(face.sharpness, 600) / 600 * 0.45 + min(face.share, 0.6) / 0.6 * 0.3
                         + frontal * 0.15 + face.det * 0.1, 4)
    return face


def pose_bin(face: Face) -> tuple[int, int]:
    if face.yaw is None:
        return (0, 0)
    return (int((face.yaw + 45) // 15), int((face.pitch + 30) // 20))


def select(faces: list[Face], *, limit: int = 60, per_bin: int | None = None) -> list[Face]:
    """Best keepers first, spread across head poses, near-duplicates dropped."""
    keepers = sorted((f for f in faces if f.tier == "keep"), key=lambda f: f.quality, reverse=True)
    bins: dict[tuple[int, int], list[Face]] = {}
    for face in keepers:
        if any(face.hash is not None and other.hash is not None and hamming(face.hash, other.hash) < SAME_PICTURE
               for chosen in bins.values() for other in chosen):
            face.notes.append("near-duplicate of a chosen still")
            continue
        bins.setdefault(pose_bin(face), []).append(face)
    per_bin = per_bin or max(3, limit // max(1, len(bins)))
    chosen: list[Face] = []
    for rank in range(per_bin):  # round-robin across bins so no single angle dominates
        for key in sorted(bins):
            if rank < len(bins[key]) and len(chosen) < limit:
                chosen.append(bins[key][rank])
    return sorted(chosen, key=lambda f: f.quality, reverse=True)


def faces_in_photo(path: Path, detector: Detector, gallery: Gallery | None) -> list[Face]:
    image = read_image(path)
    if image is None:
        return []
    found = detector.detect(image)
    if not found:
        return []
    largest = max(found, key=lambda f: f["box"][3] - f["box"][1])  # openface's rule: the subject is the largest face
    return [judge(score(image, largest, source=path.name, t=None, gallery=gallery), need_identity=gallery is not None)]


def faces_in_video(path: Path, detector: Detector, gallery: Gallery | None, *, fps: float = 2.0,
                   max_side: int = 1920) -> tuple[list[Face], dict]:
    info = media.probe(path)
    if not info.width or not info.height:
        return [], {"duration": info.duration, "frames": 0}
    scale = min(1.0, max_side / max(info.width, info.height))
    width, height = int(info.width * scale) // 2 * 2, int(info.height * scale) // 2 * 2
    faces, seen = [], 0
    for t, frame in media.frames(path, fps, width, height):
        seen += 1
        found = detector.detect(frame)
        if not found:
            continue
        largest = max(found, key=lambda f: f["box"][3] - f["box"][1])
        face = judge(score(frame, largest, source=path.name, t=round(t, 2), gallery=gallery),
                     need_identity=gallery is not None)
        faces.append(face)
    return faces, {"duration": info.duration, "frames": seen, "width": width, "height": height}
