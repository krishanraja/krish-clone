"""Write the training library: content-addressed files and one manifest. Never overwrites, never deletes."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from content_watcher import tools

from . import media

FORMAT = "krish-clone.library/1"


class Library:
    def __init__(self, root: Path):
        self.root = root
        self.manifest_path = root / "manifest.json"
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        else:
            self.manifest = {"format": FORMAT, "sources": {}, "voice": {}, "face": {}}

    def _place(self, target: Path, make) -> Path:
        """Create target with make(path) unless it already exists; a file is never replaced."""
        if target.exists():
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.stem + ".part" + target.suffix)
        if partial.exists():
            partial.unlink()  # our own unfinished write from an interrupted run, never a user file
        make(partial)
        partial.replace(target)
        return target

    def add_source(self, path: Path, *, source_id: str | None, kind: str, read: dict) -> str:
        sha = tools.sha256_file(path)
        self.manifest["sources"][sha[:16]] = {"file": path.name, "sha256": sha, "source": source_id, "kind": kind,
                                              "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                              **read}
        return sha[:16]

    def add_voice(self, key: str, master: Path, segment) -> str:
        name = f"{key}_{int(segment.start * 1000):08d}.wav"
        tier = "clean" if segment.tier == "clean" else "review"
        self._place(self.root / "voice" / tier / name, lambda p: media.cut_wav(master, segment.start, segment.end, p))
        self.manifest["voice"][name] = {"source": key, "tier": tier, **segment.as_dict()}
        return name

    def add_still(self, key: str, path: Path, face) -> str:
        if face.t is None:  # a photo: copy the original bytes, untouched
            name = f"{key}{path.suffix.lower()}"
            self._place(self.root / "face" / "photos" / name, lambda p: shutil.copyfile(path, p))
        else:
            name = f"{key}_{int(face.t * 1000):08d}.jpg"
            self._place(self.root / "face" / "stills" / name, lambda p: _grab(path, face.t, p))
        self.manifest["face"][name] = {**face.as_dict(), "source": key, "file": face.source}
        return name

    def save(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        partial = self.manifest_path.with_suffix(".part.json")
        partial.write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        partial.replace(self.manifest_path)
        return self.manifest_path


def _grab(path: Path, t: float, target: Path) -> None:
    """One full-resolution still at time t, as a high-quality JPEG."""
    ffmpeg = tools.need("ffmpeg")
    ran = tools.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-ss", f"{t:.3f}", "-i", path,
                     "-frames:v", "1", "-q:v", "2", target], timeout=120)
    if ran.returncode != 0 or not target.exists():
        raise RuntimeError(f"could not grab a still at {t}s from {path.name}: {ran.stderr.strip()[:200]}")
