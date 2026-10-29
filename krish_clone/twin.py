"""Pre-flight for a HeyGen Digital Twin recording, before any upload or credit.

HeyGen's guide (updated 20 October 2026) asks for about 30 seconds to camera, one continuous take
at 1080p and 30 fps or more, camera at eye level, the face visible, no cuts, soft even light, one
spot, and names head movement, blur and multiple scenes as the reasons uploads are rejected. Each
of those is measured here, so a weak take is reshot in minutes instead of failing after upload.
"""

from __future__ import annotations

from pathlib import Path

from content_watcher.read import visual

from . import face, media, voice

MIN_SECONDS = 30.0
MIN_SHORT_SIDE = 1080
MIN_FPS = 29.0
FACE_PRESENT = 0.95  # share of sampled frames with Krish's whole face in shot
MAX_DRIFT = 0.06  # standard deviation of the face centre, as a share of frame width: "stay in one spot"
MAX_YAW = 15.0  # median; eye level and looking at the lens


def check(path: Path, detector: face.Detector, gallery: face.Gallery | None) -> dict:
    import numpy

    info = media.probe(path)
    results = []

    def item(name: str, ok: bool, detail: str) -> None:
        results.append({"check": name, "pass": bool(ok), "detail": detail})

    short_side = min(info.width or 0, info.height or 0)
    item("length", info.duration >= MIN_SECONDS, f"{info.duration:.0f} s (at least {MIN_SECONDS:.0f})")
    item("resolution", short_side >= MIN_SHORT_SIDE, f"{info.width}x{info.height} (1080p or more)")
    item("frame rate", (info.fps or 0) >= MIN_FPS, f"{info.fps} fps (30 or more)")
    cut_times = visual.cuts(path)
    item("one continuous take", not cut_times, "no cuts" if not cut_times else f"cuts at {cut_times[:5]} s")

    faces, sampled = face.faces_in_video(path, detector, fps=2.0)
    face.identify(faces, gallery)
    frames = max(1, sampled.get("frames", 0))
    whole = [f for f in faces if f.cut_off <= face.MAX_CUT_OFF]
    item("face in shot", len(whole) / frames >= FACE_PRESENT, f"{len(whole)}/{frames} sampled frames")
    if whole:
        width = sampled.get("width") or 1
        centres = numpy.array([((f.box[0] + f.box[2]) / 2) / width for f in whole])
        item("stays in one spot", float(centres.std()) <= MAX_DRIFT, f"face centre moves {centres.std():.1%} of frame width")
        sharp = float(numpy.median([f.sharpness for f in whole]))
        item("sharp", sharp >= face.MIN_SHARPNESS, f"median sharpness {sharp:.0f} (at least {face.MIN_SHARPNESS:.0f})")
        light = float(numpy.median([f.brightness for f in whole]))
        item("lighting", face.EXPOSURE[0] <= light <= face.EXPOSURE[1], f"median face brightness {light:.0f}")
        yaws = [abs(f.yaw) for f in whole if f.yaw is not None]
        if yaws:
            yaw = float(numpy.median(yaws))
            item("eye level, to the lens", yaw <= MAX_YAW, f"median head turn {yaw:.0f} degrees")
        if gallery is not None:
            ident = float(numpy.median([f.identity for f in whole if f.identity is not None] or [0.0]))
            item("it is Krish", ident >= face.IDENTITY_FLOOR, f"identity {ident:.2f} against the gallery")
    if info.has_audio:
        heard = voice.read(path)
        clean = [s for s in heard.segments if s.tier == "clean"]
        beds = sum(1 for s in heard.segments if s.bed)
        item("quiet room", beds == 0 and heard.room_tone_db < -50,
             f"room tone {heard.room_tone_db} dB, {beds} segment(s) with sound under the pauses")
        item("speech", bool(clean), f"{heard.minutes('clean')} min of clean speech")
    else:
        item("speech", False, "no audio track")
    return {"file": path.name, "verdict": "ready" if all(r["pass"] for r in results) else "reshoot",
            "checks": results}
