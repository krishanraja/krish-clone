"""Generated media for tests: nothing of Krish's ever enters the repository."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

FFMPEG = shutil.which("ffmpeg")


def make_audio(target: Path, filter_graph: str, seconds: float, rate: int = 48_000) -> Path:
    subprocess.run([FFMPEG, "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", filter_graph, "-t", str(seconds),
                    "-ac", "1", "-ar", str(rate), "-c:a", "pcm_s16le", str(target)], check=True)
    return target


def speechlike(target: Path, *, bed_db: float | None = None, seconds: float = 12.0) -> Path:
    """Bursts of a 220 Hz tone (words) with gaps between (pauses), optionally over steady noise (a bed)."""
    words = "sin(2*PI*220*t)*0.4*(lt(mod(t,1),0.7))"
    floor = "0.0003*(random(0)-0.5)"  # room tone around -75 dB
    bed = f"+{10 ** (bed_db / 20):.5f}*(random(1)-0.5)*2" if bed_db is not None else ""
    return make_audio(target, f"aevalsrc='{words}+{floor}{bed}':s=48000", seconds)


class FakeHeard:
    """A transcript shaped like content-watcher's Heard: one word per second, one sentence per 4 seconds."""

    heard = "words"
    heard_class = None

    def __init__(self, seconds: float):
        self.words = [{"start": float(i), "end": i + 0.7, "word": f"w{i}"} for i in range(int(seconds))]
        self.segments = [{"start": float(i), "end": min(i + 3.7, seconds), "text": f"sentence {i // 4}"}
                         for i in range(0, int(seconds) - 3, 4)]
