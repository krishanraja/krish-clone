"""clone: sources, inventory and harvest."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from content_watcher import tools

from . import library as library_mod
from . import media, report, sources, voice

RUNTIME = Path.home() / ".krish-clone"


def _bucket(reason: str) -> str:
    return reason.split(" (")[0]


def _files(paths: list[Path]) -> list[Path]:
    found = []
    for path in paths:
        if path.is_dir():
            found += sorted(p for p in path.rglob("*") if p.is_file() and media.kind_of(p))
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


def _gallery(args, detector):
    from . import face

    if not args.gallery:
        return None
    gallery = face.Gallery.from_photos(_files([Path(p) for p in args.gallery]), detector)
    print(f"gallery: {gallery.size} reference faces, similarity to their own centroid {min(gallery.spread)} to {max(gallery.spread)}")
    return gallery


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
    detector = gallery = None
    if not args.no_face:
        from . import face

        detector = face.Detector(args.backend)
        print(f"face backend: {detector.backend}")
        gallery = _gallery(args, detector)
    verifier = _verifier(args)
    for path in paths:
        kind = media.kind_of(path)
        read: dict = {"rejected_reasons": []}
        key = tools.sha256_file(path)[:16]
        if kind in ("audio", "video") and media.has_audio_stream(path) and not args.no_voice:
            heard = voice.read(path, verifier=verifier)
            read.update(minutes={t: heard.minutes(t) for t in ("clean", "review")}, room_tone_db=heard.room_tone_db,
                        loudness=heard.loudness, heard=heard.heard, segments=len(heard.segments))
            read["rejected_reasons"] += [_bucket(r) for s in heard.segments if s.tier == "rejected" for r in s.reasons]
            keep = [s for s in heard.segments if s.tier in ("clean", "review")]
            if write_media and keep:
                master = media.voice_master(path, RUNTIME / "masters" / f"{key}.wav")
                for segment in keep:
                    lib.add_voice(key, master, segment)
            print(f"{path.name}: {heard.minutes('clean')} min clean, {heard.minutes('review')} min review, "
                  f"{sum(1 for s in heard.segments if s.tier == 'rejected')} segments rejected")
        if detector is not None and kind in ("video", "photo"):
            from . import face

            if kind == "photo":
                faces, info = face.faces_in_photo(path, detector, gallery), {}
            else:
                faces, info = face.faces_in_video(path, detector, gallery, fps=args.fps)
            chosen = face.select(faces, limit=args.max_stills)
            read["rejected_reasons"] += [_bucket(r) for f in faces if f.tier == "rejected" for r in f.reasons]
            read["faces"] = {"seen": len(faces), "kept": sum(f.tier == "keep" for f in faces), "chosen": len(chosen), **info}
            for f in chosen:
                if write_media:
                    lib.add_still(key, path, f)
                else:
                    lib.manifest["face"][f"{key}_{int((f.t or 0) * 1000):08d}"] = {**f.as_dict(), "source": key, "file": f.source}
            print(f"{path.name}: {len(faces)} faces measured, {len(chosen)} chosen")
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


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="clone", description=__doc__)
    top.add_argument("--config", default=str(sources.DEFAULT))
    sub = top.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sources", help="list sources, or approve/reject one")
    s.add_argument("action", nargs="?", choices=["list", "approve", "reject"], default="list")
    s.add_argument("id", nargs="?")
    s.add_argument("--local-path")
    for name, help_text in (("inventory", "measure only: manifest and inventory.md, no media copied"),
                            ("harvest", "measure and write the clean voice segments and chosen stills")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("paths", nargs="+")
        p.add_argument("--out", required=True, help="library folder (the synced Drive folder on a home computer)")
        p.add_argument("--source", help="an approved source id from config/sources.json")
        p.add_argument("--sample", action="store_true", help="a one-off test file outside any source")
        p.add_argument("--gallery", nargs="*", help="reference photos of Krish for the identity check")
        p.add_argument("--enrol", nargs="*", help="clean clips of Krish's voice for speaker verification")
        p.add_argument("--backend", default="auto", choices=["auto", "insightface", "haar"])
        p.add_argument("--fps", type=float, default=2.0)
        p.add_argument("--max-stills", type=int, default=40)
        p.add_argument("--no-face", action="store_true")
        p.add_argument("--no-voice", action="store_true")
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "sources":
            return _sources(args)
        return run(args, write_media=args.command == "harvest")
    except sources.NotApproved as refused:
        print(f"refused: {refused}")
        return 3


def entrypoint() -> None:
    sys.exit(main())
