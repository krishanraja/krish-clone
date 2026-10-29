"""inventory.md: what the library holds against what the platforms need, in numbers."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

PVC_MINIMUM, PVC_GOOD = 30.0, 120.0  # minutes of clean single-speaker audio (ElevenLabs Professional Voice Clone)


def render(manifest: dict) -> str:
    voice = manifest.get("voice", {}).values()
    clean = sum(v["duration"] for v in voice if v["tier"] == "clean") / 60
    review = sum(v["duration"] for v in voice if v["tier"] == "review") / 60
    faces = list(manifest.get("face", {}).values())
    stills = [f for f in faces if f.get("t") is not None]
    photos = [f for f in faces if f.get("t") is None]
    sources = manifest.get("sources", {})
    rejected = Counter()
    for source in sources.values():
        for reason in source.get("rejected_reasons", []):
            rejected[reason] += 1
    lines = [
        "# Training library inventory", "",
        f"Sources read: {len(sources)}.", "",
        "## Voice (ElevenLabs Professional Voice Clone)", "",
        f"- Clean: **{clean:.1f} min** against {PVC_MINIMUM:.0f} min to start and {PVC_GOOD:.0f} min to do well.",
        f"- Review (usable after a listen): {review:.1f} min.",
        f"- Shortfall to the minimum: **{max(0.0, PVC_MINIMUM - clean):.1f} min**; to good: {max(0.0, PVC_GOOD - clean):.1f} min.",
        "",
        "## Face (HeyGen)", "",
        f"- Stills from video: {len(stills)}. Photos kept: {len(photos)}.",
        f"- Distinct head poses covered: {len({(round((f.get('yaw') or 0) / 15), round((f.get('pitch') or 0) / 20)) for f in faces})}.",
        "- A Digital Twin is trained from a purpose-shot recording with a spoken consent statement, not from these.",
        "  These stills set the reference look and feed a Photo Avatar; the twin still needs one shoot.",
        "",
        "## Per source", "",
        "| File | Kind | Clean min | Review min | Faces kept | Note |",
        "|---|---|---|---|---|---|",
    ]
    for key, source in sources.items():
        minutes = source.get("minutes", {})
        kept = sum(1 for f in faces if f.get("source") == key)
        lines.append(f"| {source['file']} | {source['kind']} | {minutes.get('clean', 0):.2f} | "
                     f"{minutes.get('review', 0):.2f} | {kept} | {source.get('note', '')} |")
    if rejected:
        lines += ["", "## Why material was rejected", ""]
        lines += [f"- {reason}: {count}" for reason, count in rejected.most_common(12)]
    return "\n".join(lines) + "\n"


def write(manifest: dict, root: Path) -> Path:
    target = root / "inventory.md"
    target.write_text(render(manifest), encoding="utf-8")
    return target
