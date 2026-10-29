"""insightface's buffalo_l models run directly through onnxruntime.

The insightface package needs a C++ compiler on Windows for Python 3.12, which Krish's home
computers do not have. Its two models that matter here (SCRFD det_10g for detection and five
landmarks, ArcFace w600k_r50 for the 512-number identity) are plain ONNX files, so this module
reproduces insightface 0.7.3's pre- and post-processing (tests/test_faceonnx.py checks parity
when insightface is installed) and needs only numpy, opencv and onnxruntime. Head pose comes
from the 1k3d68 landmark model fitted to insightface's mean face, as insightface computes it.
"""

from __future__ import annotations

import hashlib
import io
import os
import urllib.request
import zipfile
from pathlib import Path

MODEL_URL = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
MODELS = {  # sha256 of the files insightface 0.7.3 ships in buffalo_l.zip
    "det_10g.onnx": "5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91",
    "w600k_r50.onnx": "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43",
    "1k3d68.onnx": "df5c06b8a0c12e422b2ed8947b8869faa4105387f199c477af038aa01f9a45cc",
}
MEAN_SHAPE = Path(__file__).parent / "data" / "meanshape_68.json"
ARCFACE_DST = [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def model_dir(home: Path) -> Path:
    """Find buffalo_l, reusing insightface's own copy when present, else download it once (verified)."""
    for candidate in (home / "models" / "buffalo_l", Path.home() / ".insightface" / "models" / "buffalo_l"):
        if all((candidate / name).exists() and _sha256(candidate / name) == sha for name, sha in MODELS.items()):
            return candidate
    target = home / "models" / "buffalo_l"
    target.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(MODEL_URL, timeout=600) as response:  # noqa: S310 - fixed https URL
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    for name, sha in MODELS.items():
        member = next(m for m in archive.namelist() if m.endswith(name))
        data = archive.read(member)
        if hashlib.sha256(data).hexdigest() != sha:
            raise RuntimeError(f"{name} from {MODEL_URL} does not match its recorded sha256")
        (target / name).write_bytes(data)
    return target


def _umeyama(src, dst):
    """Similarity transform src -> dst (scale, rotation, translation), as skimage estimates it."""
    import numpy as np

    n = src.shape[0]
    src_mean, dst_mean = src.mean(axis=0), dst.mean(axis=0)
    src_c, dst_c = src - src_mean, dst - dst_mean
    cov = dst_c.T @ src_c / n
    d = np.ones(2)
    if np.linalg.det(cov) < 0:
        d[1] = -1
    u, s, vt = np.linalg.svd(cov)
    rank = np.linalg.matrix_rank(cov)
    t = np.eye(3)
    if rank == 1:
        if np.linalg.det(u) * np.linalg.det(vt) > 0:
            t[:2, :2] = u @ vt
        else:
            sign = d[1]
            d[1] = -1
            t[:2, :2] = u @ np.diag(d) @ vt
            d[1] = sign
    else:
        t[:2, :2] = u @ np.diag(d) @ vt
    scale = 1.0 / src_c.var(axis=0).sum() * (s @ d)
    t[:2, 2] = dst_mean - scale * (t[:2, :2] @ src_mean.T)
    t[:2, :2] *= scale
    return t[:2, :]


class OnnxFaces:
    def __init__(self, home: Path, det_size: int = 640, det_thresh: float = 0.5, nms_thresh: float = 0.4):
        import onnxruntime

        folder = model_dir(home)
        options = onnxruntime.SessionOptions()
        options.log_severity_level = 3
        threads = os.environ.get("KRISH_CLONE_THREADS")
        if threads:
            options.intra_op_num_threads = int(threads)
        providers = ["CPUExecutionProvider"]
        self.det = onnxruntime.InferenceSession(str(folder / "det_10g.onnx"), options, providers=providers)
        self.rec = onnxruntime.InferenceSession(str(folder / "w600k_r50.onnx"), options, providers=providers)
        self.lmk = onnxruntime.InferenceSession(str(folder / "1k3d68.onnx"), options, providers=providers)
        import json
        import numpy as np

        self.mean_shape = np.array(json.loads(MEAN_SHAPE.read_text(encoding="utf-8"))["points"], dtype=np.float32)
        self.det_size, self.det_thresh, self.nms_thresh = det_size, det_thresh, nms_thresh
        self.det_in = self.det.get_inputs()[0].name
        self.det_out = [o.name for o in self.det.get_outputs()]
        self.rec_in = self.rec.get_inputs()[0].name
        self.centres: dict = {}

    # Detection: SCRFD with five landmarks, 15 outputs over strides 8, 16, 32 and two anchors each.
    def _forward(self, image):
        import cv2
        import numpy as np

        blob = cv2.dnn.blobFromImage(image, 1.0 / 128.0, (image.shape[1], image.shape[0]),
                                     (127.5, 127.5, 127.5), swapRB=True)
        outs = self.det.run(self.det_out, {self.det_in: blob})
        height, width = blob.shape[2], blob.shape[3]
        scores_all, boxes_all, kps_all = [], [], []
        for index, stride in enumerate((8, 16, 32)):
            scores = outs[index].reshape(-1)
            boxes = outs[index + 3].reshape(-1, 4) * stride
            kps = outs[index + 6].reshape(-1, 10) * stride
            key = (height // stride, width // stride, stride)
            if key not in self.centres:
                grid = np.stack(np.mgrid[:key[0], :key[1]][::-1], axis=-1).astype(np.float32)
                grid = (grid * stride).reshape(-1, 2)
                self.centres[key] = np.stack([grid] * 2, axis=1).reshape(-1, 2)
            centres = self.centres[key]
            keep = np.where(scores >= self.det_thresh)[0]
            box = np.stack([centres[:, 0] - boxes[:, 0], centres[:, 1] - boxes[:, 1],
                            centres[:, 0] + boxes[:, 2], centres[:, 1] + boxes[:, 3]], axis=-1)
            points = np.stack([centres[:, i % 2] + kps[:, i] for i in range(10)], axis=-1).reshape(-1, 5, 2)
            scores_all.append(scores[keep])
            boxes_all.append(box[keep])
            kps_all.append(points[keep])
        return np.concatenate(scores_all), np.concatenate(boxes_all), np.concatenate(kps_all)

    def _nms(self, dets):
        import numpy as np

        x1, y1, x2, y2, scores = dets.T
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            w = np.maximum(0.0, np.minimum(x2[i], x2[order[1:]]) - np.maximum(x1[i], x1[order[1:]]) + 1)
            h = np.maximum(0.0, np.minimum(y2[i], y2[order[1:]]) - np.maximum(y1[i], y1[order[1:]]) + 1)
            overlap = w * h / (areas[i] + areas[order[1:]] - w * h)
            order = order[np.where(overlap <= self.nms_thresh)[0] + 1]
        return keep

    def detect(self, image):
        import cv2
        import numpy as np

        size = self.det_size
        ratio = image.shape[0] / image.shape[1]
        if ratio > 1:
            new_h, new_w = size, int(size / ratio)
        else:
            new_w, new_h = size, int(size * ratio)
        scale = new_h / image.shape[0]
        canvas = np.zeros((size, size, 3), dtype=np.uint8)
        canvas[:new_h, :new_w] = cv2.resize(image, (new_w, new_h))
        scores, boxes, kps = self._forward(canvas)
        order = scores.argsort()[::-1]
        dets = np.hstack((boxes / scale, scores[:, None])).astype(np.float32)[order]
        kps = (kps / scale)[order]
        keep = self._nms(dets)
        return dets[keep], kps[keep]

    def embed(self, image, landmarks):
        import cv2
        import numpy as np

        matrix = _umeyama(np.asarray(landmarks, dtype=np.float64), np.asarray(ARCFACE_DST, dtype=np.float64))
        aligned = cv2.warpAffine(image, matrix, (112, 112), borderValue=0.0)
        blob = cv2.dnn.blobFromImage(aligned, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True)
        vector = self.rec.run(None, {self.rec_in: blob})[0].reshape(-1)
        return vector / np.linalg.norm(vector)

    def pose(self, image, box) -> list[float]:
        """[pitch, yaw, roll] in degrees from 68 3D landmarks, exactly as insightface reports face.pose."""
        import cv2
        import math
        import numpy as np

        size = 192
        w, h = box[2] - box[0], box[3] - box[1]
        cx, cy = (box[2] + box[0]) / 2, (box[3] + box[1]) / 2
        scale = size / (max(w, h) * 1.5)
        matrix = np.array([[scale, 0, size / 2 - cx * scale], [0, scale, size / 2 - cy * scale]], dtype=np.float64)
        crop = cv2.warpAffine(image, matrix, (size, size), borderValue=0.0)
        blob = cv2.dnn.blobFromImage(crop, 1.0, (size, size), (0.0, 0.0, 0.0), swapRB=True)
        pred = self.lmk.run(None, {self.lmk.get_inputs()[0].name: blob})[0][0].reshape(-1, 3)[-68:].astype(np.float32)
        pred[:, 0:2] += 1
        pred[:, 0:2] *= size // 2
        pred[:, 2] *= size // 2
        inverse = cv2.invertAffineTransform(matrix)
        points = np.zeros_like(pred)
        points[:, 0:2] = pred[:, 0:2] @ inverse[:, :2].T + inverse[:, 2]
        points[:, 2] = pred[:, 2] * math.sqrt(inverse[0, 0] ** 2 + inverse[0, 1] ** 2)
        homogeneous = np.hstack((self.mean_shape, np.ones((68, 1), dtype=np.float32)))
        affine = np.linalg.lstsq(homogeneous, points, rcond=None)[0].T
        r1 = affine[0, :3] / np.linalg.norm(affine[0, :3])
        r2 = affine[1, :3] / np.linalg.norm(affine[1, :3])
        rotation = np.stack((r1, r2, np.cross(r1, r2)))
        sy = math.hypot(rotation[0, 0], rotation[1, 0])
        if sy > 1e-6:
            pitch, roll = math.atan2(rotation[2, 1], rotation[2, 2]), math.atan2(rotation[1, 0], rotation[0, 0])
        else:
            pitch, roll = math.atan2(-rotation[1, 2], rotation[1, 1]), 0.0
        yaw = math.atan2(-rotation[2, 0], sy)
        return [math.degrees(pitch), math.degrees(yaw), math.degrees(roll)]

    def get(self, image) -> list[dict]:
        dets, kps = self.detect(image)
        return [{"box": [int(v) for v in det[:4]], "det": float(det[4]), "embedding": self.embed(image, points),
                 "pose": self.pose(image, det[:4]), "kps": points.tolist()} for det, points in zip(dets, kps)]
