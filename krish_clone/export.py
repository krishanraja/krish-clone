"""Hand the library to the platforms in the shape each one asks for. Builds files; uploads nothing.

ElevenLabs' Professional Voice Clone guide asks for: MP3 at 192 kbps or above, files of about 30
minutes, speech between -23 and -18 dB RMS with a true peak of -3 dB, one speaker, one style.
"""

from __future__ import annotations

import json
from pathlib import Path

from content_watcher import tools

from . import media

PVC_FILE_MINUTES = 30.0
PVC_LOUDNESS = -20.0  # LUFS, the middle of ElevenLabs' -23 to -18 dB RMS range for speech
PVC_TRUE_PEAK = -3.0
GAP = 0.4  # seconds of silence between segments: a breath, not a cut


def elevenlabs(library: Path, out: Path, *, include_review: bool = False) -> dict:
    manifest = json.loads((library / "manifest.json").read_text(encoding="utf-8"))
    tiers = ("clean", "review") if include_review else ("clean",)
    chosen = sorted(((name, entry) for name, entry in manifest.get("voice", {}).items() if entry["tier"] in tiers),
                    key=lambda item: (item[1].get("source", ""), item[1]["start"]))
    files = [(library / "voice" / entry["tier"] / name, entry) for name, entry in chosen]
    files = [(path, entry) for path, entry in files if path.exists()]
    if not files:
        raise ValueError("the library has no voice segments to export yet")
    groups, current, length = [], [], 0.0
    for path, entry in files:
        if current and length + entry["duration"] > PVC_FILE_MINUTES * 60:
            groups.append(current)
            current, length = [], 0.0
        current.append((path, entry))
        length += entry["duration"] + GAP
    if current:
        groups.append(current)
    out.mkdir(parents=True, exist_ok=True)
    targets = [out / f"elevenlabs-pvc-{n:02d}.mp3" for n in range(1, len(groups) + 1)]
    taken = [t for t in targets if t.exists()]
    if taken:
        raise FileExistsError(f"{taken[0]} already exists; export to a new folder")
    ffmpeg = tools.need("ffmpeg")
    report = {"files": [], "segments": len(files), "tiers": list(tiers)}
    for target, group in zip(targets, groups):
        listing = out / f".{target.stem}.txt"
        silence = out / ".gap.wav"
        if not silence.exists():
            tools.run([ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                       f"anullsrc=r={media.MASTER_RATE}:cl=mono", "-t", str(GAP), "-c:a", "pcm_s16le", silence], timeout=60)
        lines = []
        for path, _ in group:
            lines += [f"file '{path.as_posix()}'", f"file '{silence.as_posix()}'"]
        listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
        partial = target.with_name(target.stem + ".part.mp3")
        ran = tools.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                         "-i", listing, "-af", f"loudnorm=I={PVC_LOUDNESS}:TP={PVC_TRUE_PEAK}:LRA=11",
                         "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", partial], timeout=3600)
        listing.unlink()
        if ran.returncode != 0 or not partial.exists():
            raise RuntimeError(f"export failed for {target.name}: {ran.stderr.strip()[:300]}")
        partial.replace(target)
        report["files"].append({"file": target.name, "minutes": round(media.probe(target).duration / 60, 2),
                                "segments": [p.name for p, _ in group]})
    if silence.exists():
        silence.unlink()
    (out / "elevenlabs-export.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
