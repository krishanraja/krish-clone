"""ffmpeg plumbing: probing, the full-rate voice master, 16 kHz samples and full-resolution frames."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from content_watcher import tools
from content_watcher.read.audio import decode_samples, has_audio_stream

VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
AUDIO_SUFFIXES = {".wav", ".m4a", ".mp3", ".aac", ".flac", ".ogg", ".opus"}
PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MASTER_RATE = 48_000


@dataclass
class Probe:
    duration: float
    width: int | None
    height: int | None
    has_audio: bool


def kind_of(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in PHOTO_SUFFIXES:
        return "photo"
    return None


def probe(path: Path) -> Probe:
    ffprobe = tools.need("ffprobe")
    ran = tools.run([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], timeout=60)
    if ran.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path.name}: {ran.stderr.strip()[:200]}")
    info = json.loads(ran.stdout or "{}")
    width = height = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video" and stream.get("disposition", {}).get("attached_pic") != 1:
            width, height = stream.get("width"), stream.get("height")
            rotation = 0
            for side in stream.get("side_data_list", []) or []:
                rotation = int(side.get("rotation", rotation) or 0)
            rotation = rotation or int(stream.get("tags", {}).get("rotate", 0) or 0)
            if abs(rotation) % 180 == 90:
                width, height = height, width
            break
    duration = float(info.get("format", {}).get("duration") or 0)
    return Probe(duration, width, height, any(s.get("codec_type") == "audio" for s in info.get("streams", [])))


def voice_master(path: Path, target: Path) -> Path:
    """The full-rate mono WAV every clean segment is cut from (never resampled down for training)."""
    if target.exists():
        return target
    ffmpeg = tools.need("ffmpeg")
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part.wav")
    ran = tools.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-map", "0:a:0",
                     "-vn", "-ac", "1", "-ar", str(MASTER_RATE), "-c:a", "pcm_s16le", partial], timeout=1800)
    if ran.returncode != 0 or not partial.exists():
        raise RuntimeError(f"could not extract audio from {path.name}: {ran.stderr.strip()[:200]}")
    partial.replace(target)
    return target


def cut_wav(master: Path, start: float, end: float, target: Path) -> Path:
    ffmpeg = tools.need("ffmpeg")
    target.parent.mkdir(parents=True, exist_ok=True)
    ran = tools.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-ss", f"{start:.3f}",
                     "-to", f"{end:.3f}", "-i", master, "-c:a", "pcm_s16le", target], timeout=300)
    if ran.returncode != 0:
        raise RuntimeError(f"could not cut {target.name}: {ran.stderr.strip()[:200]}")
    return target


def samples16k(path: Path):
    """16 kHz mono float32 as a numpy array (content-watcher's decoder)."""
    import numpy

    return numpy.frombuffer(decode_samples(path).tobytes(), dtype=numpy.float32)


def clip_events(path: Path, *, run: int = 3, level: float = 0.999) -> list[float]:
    """Times (seconds) where the original audio sits flat at full scale for `run` samples or more.

    Measured at the file's own rate on the first channel, streamed, because a resampled or downmixed
    decode overshoots past full scale on perfectly healthy audio.
    """
    import numpy
    import subprocess

    ffmpeg = tools.need("ffmpeg")
    process = subprocess.Popen(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(path), "-map", "0:a:0", "-af", "pan=mono|c0=c0",
         "-ar", str(MASTER_RATE), "-f", "s16le", "-acodec", "pcm_s16le", "-"],
        stdout=subprocess.PIPE,
    )
    events, offset, carry = [], 0, 0
    limit = int(32767 * level)
    try:
        while True:
            raw = process.stdout.read(MASTER_RATE * 2 * 10)
            if not raw:
                break
            chunk = numpy.frombuffer(raw[: len(raw) - len(raw) % 2], dtype=numpy.int16)
            hot = numpy.abs(chunk.astype(numpy.int32)) >= limit
            edges = numpy.flatnonzero(numpy.diff(numpy.concatenate(([0], hot.astype(numpy.int8), [0]))))
            starts, ends = edges[::2], edges[1::2]
            for a, b in zip(starts, ends):
                length = b - a + (carry if a == 0 else 0)
                if length >= run:
                    events.append(round((offset + a) / MASTER_RATE, 3))
            carry = int(ends[-1] - starts[-1]) if len(ends) and ends[-1] == len(chunk) else 0
            offset += len(chunk)
    finally:
        process.stdout.close()
        process.kill()
        process.wait()
    return events


def frames(path: Path, fps: float, width: int, height: int):
    """Yield (t, BGR frame) at full resolution, decoded once through a pipe."""
    import numpy
    import subprocess

    ffmpeg = tools.need("ffmpeg")
    size = width * height * 3
    process = subprocess.Popen(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf",
         f"fps={fps},scale={width}:{height}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE,
    )
    index = 0
    try:
        while True:
            raw = process.stdout.read(size)
            if len(raw) < size:
                break
            yield index / fps, numpy.frombuffer(raw, dtype=numpy.uint8).reshape(height, width, 3)
            index += 1
    finally:
        process.stdout.close()
        process.kill()
        process.wait()


__all__ = ["Probe", "kind_of", "probe", "voice_master", "cut_wav", "samples16k", "frames", "has_audio_stream", "MASTER_RATE"]
