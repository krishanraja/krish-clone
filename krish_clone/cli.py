"""clone: sources, inventory, harvest, the reading script and evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content_watcher import tools

from . import library as library_mod
from . import media, report, sources, voice

RUNTIME = Path.home() / ".krish-clone"
SKIP_PARTS = {"__macosx", ".tmp.drivedownload", ".tmp.driveupload"}


def _bucket(reason: str) -> str:
    return reason.split(" (")[0]


def _files(paths: list[Path]) -> list[Path]:
    found = []
    for path in paths:
        if path.is_dir():
            found += sorted(p for p in path.rglob("*") if p.is_file() and media.kind_of(p)
                            and not SKIP_PARTS & {part.lower() for part in p.parts})
        elif media.kind_of(path):
            found.append(path)
    return found


def _check_scope(paths: list[Path], source_id: str | None, sample: bool, config: Path) -> None:
    if sample:
        return
    if not source_id:
        raise sources.NotApproved("name an approved --source, or pass --sample for a one-off test file")
    source = sources.require_approved(source_id, config)
    root = Path(source.local_path).resolve()
    for path in paths:
        if not path.resolve().is_relative_to(root):
            raise sources.NotApproved(f"{path} is outside approved source {source_id!r} ({root})")


def _cached(kind: str, key: str):
    path = RUNTIME / "cache" / kind / f"{key}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _cache(kind: str, key: str, data) -> None:
    path = RUNTIME / "cache" / kind / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".part")
    partial.write_text(json.dumps(data), encoding="utf-8")
    partial.replace(path)


def _voice(path: Path, key: str, verifier) -> voice.VoiceRead:
    cached = _cached("voice", f"{key}-{'v' if verifier else 'n'}")
    if cached is not None:
        return voice.VoiceRead.from_dict(cached)
    heard = voice.read(path, verifier=verifier)
    _cache("voice", f"{key}-{'v' if verifier else 'n'}", heard.as_dict())
    return heard


def _faces(path: Path, key: str, kind: str, detector, fps: float):
    from . import face

    cached = _cached("face", f"{key}-{detector.backend}-{fps}")
    if cached is not None:
        return face.from_cache(cached["faces"]), cached["info"]
    if kind == "photo":
        faces, info = face.faces_in_photo(path, detector), {}
    else:
        faces, info = face.faces_in_video(path, detector, fps=fps)
    _cache("face", f"{key}-{detector.backend}-{fps}", {"faces": face.to_cache(faces), "info": info})
    return faces, info


def _verifier(args):
    if not args.enrol:
        return None
    from . import speaker

    if not speaker.available():
        print("speaker verification unavailable (install the speaker extra); segments stay unverified")
        return None
    return speaker.Verifier([Path(p) for p in args.enrol], RUNTIME / "models")


def run(args, *, write_media: bool) -> int:
    paths = _files([Path(p) for p in args.paths])
    if not paths:
        print("no media found")
        return 1
    _check_scope(paths, args.source, args.sample, Path(args.config))
    out = Path(args.out)
    lib = library_mod.Library(out)
    verifier = _verifier(args)
    detector = None
    if not args.no_face:
        from . import face

        detector = face.Detector(args.backend, RUNTIME)
        print(f"face backend: {detector.backend}")

    # Pass 1: measure every file (cached, so an interrupted run resumes where it stopped).
    measured = []
    for number, path in enumerate(paths, 1):
        kind = media.kind_of(path)
        key = tools.sha256_file(path)[:16]
        entry = {"path": path, "kind": kind, "key": key, "voice": None, "faces": [], "info": {}}
        try:
            if kind in ("audio", "video") and not args.no_voice and media.has_audio_stream(path):
                entry["voice"] = _voice(path, key, verifier)
            if detector is not None and kind in ("video", "photo"):
                entry["faces"], entry["info"] = _faces(path, key, kind, detector, args.fps)
        except Exception as failed:  # noqa: BLE001 - one bad file never stops the run; it is recorded
            entry["error"] = f"{type(failed).__name__}: {str(failed)[:200]}"
        print(f"[{number}/{len(paths)}] {path.name}: measured" + (f" (error: {entry['error']})" if "error" in entry else ""))
        measured.append(entry)

    # Who is Krish: reference photos if given, else the dominant identity across this source.
    gallery = None
    if detector is not None and detector.backend == "onnx":
        from . import face

        if args.gallery:
            gallery = face.Gallery.from_photos(_files([Path(p) for p in args.gallery]), detector)
            lib.manifest["gallery"] = {"kind": "photos", "size": gallery.size}
        else:
            candidates = [v for e in measured for v in face.gallery_candidates(e["faces"])]
            try:
                gallery, found = face.Gallery.dominant(candidates)
                lib.manifest["gallery"] = {"kind": "dominant identity in the source", "size": gallery.size, **found}
            except ValueError as unsure:
                print(f"identity: {unsure}; faces are kept unverified")
                lib.manifest["gallery"] = {"kind": "none", "size": 0, "why": str(unsure)}
        print(f"gallery: {lib.manifest['gallery']}")

    # Pass 2: judge, select and write. Cleanest voice first, so a repeat in a worse cut is the one skipped.
    def cleanliness(entry) -> float:
        kept = [s.snr_db or 0 for s in (entry["voice"].segments if entry["voice"] else []) if s.tier == "clean"]
        return sum(kept) / len(kept) if kept else -1.0

    kept_audio: dict = {}  # key -> loudness contour of files whose voice is already in the library
    for entry in sorted(measured, key=cleanliness, reverse=True):
        path, key, kind = entry["path"], entry["key"], entry["kind"]
        read: dict = {"rejected_reasons": []}
        if "error" in entry:
            read["error"] = entry["error"]
        heard = entry["voice"]
        if heard is not None:
            read.update(minutes={t: heard.minutes(t) for t in ("clean", "review")}, room_tone_db=heard.room_tone_db,
                        loudness=heard.loudness, heard=heard.heard, segments=len(heard.segments))
            read["rejected_reasons"] += [_bucket(r) for s in heard.segments if s.tier == "rejected" for r in s.reasons]
            keep = []
            for segment in (s for s in heard.segments if s.tier in ("clean", "review")):
                repeat = voice.repeat_of(segment, heard.envelope, kept_audio) if heard.envelope is not None else None
                if repeat is None:
                    keep.append(segment)
                else:
                    lib.note_duplicate(key, segment, repeat)
            read["repeated_segments"] = sum(1 for s in heard.segments if s.tier in ("clean", "review")) - len(keep)
            if keep and heard.envelope is not None:
                kept_audio[key] = heard.envelope
            if write_media and keep:
                master = media.voice_master(path, RUNTIME / "masters" / f"{key}.wav")
                for segment in keep:
                    lib.add_voice(key, master, segment)
            elif keep:  # inventory: count what would be kept, write nothing
                for segment in keep:
                    lib.manifest["voice"][f"{key}_{int(segment.start * 1000):08d}.wav"] = {"source": key, **segment.as_dict(),
                                                                                         "tier": segment.tier}
        if entry["faces"]:
            from . import face

            faces = face.identify(entry["faces"], gallery)
            chosen = face.select(faces, limit=args.max_stills)
            read["rejected_reasons"] += [_bucket(r) for f in faces if f.tier == "rejected" for r in f.reasons]
            read["faces"] = {"seen": len(faces), "kept": sum(f.tier == "keep" for f in faces), "chosen": len(chosen),
                             **entry["info"]}
            for f in chosen:
                if write_media:
                    lib.add_still(key, path, f)
                else:
                    lib.manifest["face"][f"{key}_{int((f.t or 0) * 1000):08d}"] = {**f.as_dict(), "source": key, "file": f.source}
        lib.add_source(path, source_id=args.source, kind=kind, read=read)
    lib.save()
    target = report.write(lib.manifest, out)
    print(f"manifest: {lib.manifest_path}\ninventory: {target}")
    return 0


def _sources(args) -> int:
    config = Path(args.config)
    if args.action in ("approve", "reject"):
        if not args.id:
            print("name a source id")
            return 2
        source = sources.set_status(args.id, "approved" if args.action == "approve" else "rejected", config,
                                    local_path=args.local_path)
        print(f"{source.id}: {source.status}" + (f" ({source.local_path})" if source.local_path else ""))
        return 0
    for source in sources.load(config):
        print(f"{source.status:9} {source.id:18} {source.kind:6} {source.name}\n{'':29}{source.note}")
    return 0


def _script(args) -> int:
    from . import script

    paths = [p for p in _files_text([Path(p) for p in args.paths])]
    _check_scope(paths, args.source, args.sample, Path(args.config))
    built = script.build(paths, minutes=args.minutes, wpm=args.wpm)
    Path(args.out).write_text(built.markdown, encoding="utf-8")
    print(f"reading script: {args.out} ({built.words} words, about {built.minutes:.0f} min at {args.wpm} wpm, "
          f"{len(built.sources)} source files)")
    return 0


def _files_text(paths: list[Path]) -> list[Path]:
    from . import script

    found = []
    for path in paths:
        if path.is_dir():
            found += sorted(p for p in path.rglob("*") if p.is_file() and script.is_script(p))
        elif path.is_file():
            found.append(path)
    return found


def _evaluate(args) -> int:
    from . import evaluate

    result = evaluate.voice([Path(p) for p in args.real], [Path(p) for p in args.clone], RUNTIME / "models")
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "pass" else 1


def _abpack(args) -> int:
    from . import evaluate

    key = evaluate.ab_pack([Path(p) for p in args.real], [Path(p) for p in args.clone], Path(args.out), seed=args.seed)
    print(f"pack: {args.out} ({len(key['pairs'])} pairs). Keep {key['key_file']} away from the listeners.")
    return 0


def _abscore(args) -> int:
    from . import evaluate

    result = evaluate.ab_score(Path(args.key), Path(args.answers))
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "pass" else 1


def _doctor(args) -> int:
    """Everything a run needs, checked before it starts. Nothing is written except the model download."""
    import importlib.util

    problems = 0

    def line(ok: bool, name: str, detail: str, required: bool = True) -> None:
        nonlocal problems
        status = "ok" if ok else ("MISSING" if required else "optional")
        problems += int(not ok and required)
        print(f"{status:9}{name:22}{detail}")

    line(bool(tools.which("ffmpeg")), "ffmpeg", tools.which("ffmpeg") or "winget install Gyan.FFmpeg")
    line(bool(tools.which("ffprobe")), "ffprobe", tools.which("ffprobe") or "comes with ffmpeg")
    for module, extra, required in (("faster_whisper", "voice", True), ("onnxruntime", "face", True),
                                    ("cv2", "face", True), ("speechbrain", "speaker", False)):
        found = importlib.util.find_spec(module) is not None
        line(found, module, "installed" if found else f'pip install -e ".[{extra}]"', required)
    if importlib.util.find_spec("onnxruntime") and importlib.util.find_spec("cv2"):
        try:
            from .faceonnx import model_dir

            line(True, "face models", str(model_dir(RUNTIME)))
        except Exception as failed:  # noqa: BLE001
            line(False, "face models", f"{type(failed).__name__}: {failed}")
    config = Path(args.config)
    for source in sources.load(config):
        if source.approved:
            ok = bool(source.local_path) and Path(source.local_path).is_dir()
            line(ok, f"source {source.id}", source.local_path or "no local_path")
    import json as _json

    library = _json.loads(config.read_text(encoding="utf-8")).get("library_local_path")
    line(bool(library) and Path(library).is_dir(), "library folder", library or "set library_local_path in config/sources.json")
    print("ready" if not problems else f"{problems} required piece(s) missing")
    return 0 if not problems else 1


def _export(args) -> int:
    from . import export

    result = export.elevenlabs(Path(args.library), Path(args.out), include_review=args.include_review)
    for item in result["files"]:
        print(f"{item['file']}: {item['minutes']} min, {len(item['segments'])} segments")
    print(f"Ready to upload by hand to ElevenLabs Professional Voice Cloning (nothing was uploaded): {args.out}")
    return 0


def _twin(args) -> int:
    from . import face, twin

    detector = face.Detector(args.backend, RUNTIME)
    gallery = face.Gallery.from_photos(_files([Path(p) for p in args.gallery]), detector) if args.gallery else None
    result = twin.check(Path(args.video), detector, gallery)
    for item in result["checks"]:
        print(f"{'pass' if item['pass'] else 'FAIL':5} {item['check']:24} {item['detail']}")
    print(f"verdict: {result['verdict']}")
    return 0 if result["verdict"] == "ready" else 1


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="clone", description=__doc__)
    top.add_argument("--config", default=str(sources.DEFAULT))
    sub = top.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sources", help="list sources, or approve/reject one")
    s.add_argument("action", nargs="?", choices=["list", "approve", "reject"], default="list")
    s.add_argument("id", nargs="?")
    s.add_argument("--local-path")
    sub.add_parser("doctor", help="check everything a run needs")
    for name, help_text in (("inventory", "measure only: manifest and inventory.md, no media copied"),
                            ("harvest", "measure and write the clean voice segments and chosen stills")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("paths", nargs="+")
        p.add_argument("--out", required=True, help="library folder (the synced Drive folder on a home computer)")
        p.add_argument("--source", help="an approved source id from config/sources.json")
        p.add_argument("--sample", action="store_true", help="a one-off test file outside any source")
        p.add_argument("--gallery", nargs="*", help="reference photos of Krish; default: the dominant identity in the source")
        p.add_argument("--enrol", nargs="*", help="clean clips of Krish's voice for speaker verification")
        p.add_argument("--backend", default="auto", choices=["auto", "onnx", "haar"])
        p.add_argument("--fps", type=float, default=2.0)
        p.add_argument("--max-stills", type=int, default=40)
        p.add_argument("--no-face", action="store_true")
        p.add_argument("--no-voice", action="store_true")
    sc = sub.add_parser("script", help="build the reading script for the voice session from Krish's own scripts")
    sc.add_argument("paths", nargs="+")
    sc.add_argument("--out", required=True)
    sc.add_argument("--source")
    sc.add_argument("--sample", action="store_true")
    sc.add_argument("--minutes", type=float, default=75)
    sc.add_argument("--wpm", type=float, default=150)
    ex = sub.add_parser("export", help="build ElevenLabs PVC upload files from the library (uploads nothing)")
    ex.add_argument("target", choices=["elevenlabs"])
    ex.add_argument("--library", required=True)
    ex.add_argument("--out", required=True)
    ex.add_argument("--include-review", action="store_true")
    tw = sub.add_parser("twincheck", help="pre-flight a HeyGen Digital Twin recording before upload")
    tw.add_argument("video")
    tw.add_argument("--gallery", nargs="*", help="reference photos or stills of Krish")
    tw.add_argument("--backend", default="auto", choices=["auto", "onnx", "haar"])
    ev = sub.add_parser("evaluate", help="score cloned clips against real ones (speaker similarity)")
    ev.add_argument("--real", nargs="+", required=True)
    ev.add_argument("--clone", nargs="+", required=True)
    ab = sub.add_parser("abpack", help="build a blind A/B listening pack and its answer key")
    ab.add_argument("--real", nargs="+", required=True)
    ab.add_argument("--clone", nargs="+", required=True)
    ab.add_argument("--out", required=True)
    ab.add_argument("--seed", type=int, default=None)
    sco = sub.add_parser("abscore", help="score listeners' answers against the key")
    sco.add_argument("--key", required=True)
    sco.add_argument("--answers", required=True, help="CSV: listener,pair,choice (A or B = which one is the clone)")
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    handlers = {"export": _export, "twincheck": _twin, "doctor": _doctor, "sources": _sources, "script": _script, "evaluate": _evaluate, "abpack": _abpack, "abscore": _abscore}
    try:
        if args.command in handlers:
            return handlers[args.command](args)
        return run(args, write_media=args.command == "harvest")
    except sources.NotApproved as refused:
        print(f"refused: {refused}")
        return 3


def entrypoint() -> None:
    sys.exit(main())
