"""The registry of synthetic voices and likenesses Krish has approved.

One entry per approved clone: its name, whether it is a voice or a likeness, the platform's name, Krish's exact
words, the date he said them, and the sha256 of the scored A/B record he approved (`clone abscore --record`). Names
and hashes only: this repository is public, so an entry never holds a platform's voice or avatar id, a key, or
anything else that grants access, and a field the format does not name is refused.

Other repositories read it live from main (docs/REGISTRY.md). content-engine's `ve lint` row `voice.synthetic` refuses
any spec that uses a synthetic Krish voice or likeness without a matching, unwithdrawn entry.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

FORMAT = "krish-clone.synthetic-approvals/1"
DEFAULT = Path(__file__).resolve().parent.parent / "config" / "synthetic-approvals.json"
RAW_URL = "https://raw.githubusercontent.com/krishanraja/krish-clone/main/config/synthetic-approvals.json"
KINDS = ("voice", "likeness")
PLATFORMS = {"voice": ("elevenlabs",), "likeness": ("heygen",)}
NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ID_SHAPED = 16  # a name segment this long reads as a platform id, never a name
REQUIRED = ("name", "kind", "platform", "scored_pack_sha256", "approved_words", "approved_on")
OPTIONAL = ("score", "withdrawn")
SCORE_KEYS = {"listeners": int, "pairs": int, "picked_the_clone": float, "verdict": str}


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Approval:
    name: str
    kind: str
    platform: str
    scored_pack_sha256: str
    approved_words: str
    approved_on: str
    score: dict | None = None
    withdrawn: dict | None = None

    @property
    def active(self) -> bool:
        return self.withdrawn is None


def check_name(name: str) -> str:
    if not isinstance(name, str) or not NAME.match(name):
        raise RegistryError(f"name {name!r}: lowercase words joined by hyphens, such as krish-voice-1")
    if any(len(part) >= ID_SHAPED for part in name.split("-")):
        raise RegistryError(f"name {name!r} looks like a platform id; the registry holds names and hashes only")
    return name


def check_kind(kind: str, platform: str) -> None:
    if kind not in KINDS:
        raise RegistryError(f"kind {kind!r}: one of {', '.join(KINDS)}")
    if platform not in PLATFORMS[kind]:
        raise RegistryError(f"platform {platform!r}: a {kind} comes from {', '.join(PLATFORMS[kind])}")


def check_date(value, field: str) -> str:
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError
        datetime.date.fromisoformat(value)
    except ValueError:
        raise RegistryError(f"{field} {value!r}: a date, YYYY-MM-DD") from None
    return value


def check_words(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{field}: Krish's exact words, never empty")
    return value


def _entry(raw, where: str) -> Approval:
    if not isinstance(raw, dict):
        raise RegistryError(f"{where}: an object")
    unknown = sorted(set(raw) - set(REQUIRED) - set(OPTIONAL))
    if unknown:
        raise RegistryError(f"{where}: unknown field {', '.join(unknown)} (names and hashes only)")
    missing = [key for key in REQUIRED if key not in raw]
    if missing:
        raise RegistryError(f"{where}: missing {', '.join(missing)}")
    try:
        check_name(raw["name"])
        check_kind(raw["kind"], raw["platform"])
        if not isinstance(raw["scored_pack_sha256"], str) or not SHA256.match(raw["scored_pack_sha256"]):
            raise RegistryError("scored_pack_sha256: 64 lowercase hex characters")
        check_words(raw["approved_words"], "approved_words")
        check_date(raw["approved_on"], "approved_on")
        score = raw.get("score")
        if score is not None:
            if not isinstance(score, dict) or set(score) != set(SCORE_KEYS):
                raise RegistryError(f"score: exactly {', '.join(SCORE_KEYS)}")
            for key, kind in SCORE_KEYS.items():
                if not isinstance(score[key], (int, float) if kind is float else kind) or isinstance(score[key], bool):
                    raise RegistryError(f"score.{key}: a {kind.__name__}")
        withdrawn = raw.get("withdrawn")
        if withdrawn is not None:
            if not isinstance(withdrawn, dict) or set(withdrawn) != {"words", "on"}:
                raise RegistryError("withdrawn: exactly words and on")
            check_words(withdrawn["words"], "withdrawn.words")
            check_date(withdrawn["on"], "withdrawn.on")
            if withdrawn["on"] < raw["approved_on"]:
                raise RegistryError("withdrawn.on is before approved_on")
    except RegistryError as problem:
        raise RegistryError(f"{where}: {problem}") from None
    return Approval(**{key: raw.get(key) for key in REQUIRED + OPTIONAL})


def parse(text: str) -> list[Approval]:
    """Every entry, checked. Anything malformed refuses the whole registry: a reader never guesses."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as failed:
        raise RegistryError(f"not JSON: {failed}") from None
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise RegistryError(f"format is not {FORMAT}")
    entries = data.get("approvals")
    if not isinstance(entries, list):
        raise RegistryError("approvals: a list")
    approvals = [_entry(raw, f"approvals[{index}]") for index, raw in enumerate(entries)]
    for field in ("name", "scored_pack_sha256"):
        seen = [getattr(a, field) for a in approvals]
        twice = sorted({value for value in seen if seen.count(value) > 1})
        if twice:
            raise RegistryError(f"{field} appears twice: {', '.join(twice)} (one entry per approved clone)")
    return approvals


def load(path: Path = DEFAULT) -> list[Approval]:
    return parse(Path(path).read_text(encoding="utf-8"))


def find(approvals: list[Approval], name: str, kind: str) -> Approval | None:
    """The active entry for this clone, or None. A withdrawn entry never matches."""
    for approval in approvals:
        if approval.name == name and approval.kind == kind and approval.active:
            return approval
    return None


def _write(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    parse(text)  # never write a registry a reader would refuse
    partial = Path(path).with_suffix(".part")
    partial.write_text(text, encoding="utf-8")
    partial.replace(path)


def add(path: Path, record_path: Path, words: str, on: str) -> Approval:
    """Record Krish's approval of one scored record: his exact words and the date he said them. Run only with his
    words in hand; the record must pass the bar (panel.read_record says why when it does not)."""
    from . import panel

    record, sha = panel.read_record(Path(record_path))
    check_words(words, "words")
    check_date(on, "on")
    if on < record["scored_on"]:
        raise RegistryError(f"on {on} is before the record was scored ({record['scored_on']})")
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    existing = parse(json.dumps(data))
    clone = record["clone"]
    if any(a.name == clone["name"] for a in existing):
        raise RegistryError(f"{clone['name']} is already in the registry; a new clone takes a new name")
    if any(a.scored_pack_sha256 == sha for a in existing):
        raise RegistryError(f"scored record {sha} is already approved")
    score = record["score"]
    entry = {
        "name": clone["name"], "kind": clone["kind"], "platform": clone["platform"], "scored_pack_sha256": sha,
        "approved_words": words, "approved_on": on,
        "score": {"listeners": score["listeners"], "pairs": score["pairs"],
                  "picked_the_clone": float(score["picked_the_clone"]), "verdict": score["verdict"]},
    }
    data["approvals"].append(entry)
    _write(Path(path), data)
    return _entry(entry, clone["name"])


def withdraw(path: Path, name: str, words: str, on: str) -> Approval:
    """Krish takes an approval back. The entry stays, so the history is kept, and never matches again."""
    check_words(words, "words")
    check_date(on, "on")
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    parse(json.dumps(data))
    for raw in data["approvals"]:
        if raw["name"] == name:
            if raw.get("withdrawn"):
                raise RegistryError(f"{name} is already withdrawn")
            raw["withdrawn"] = {"words": words, "on": on}
            _write(Path(path), data)
            return _entry(raw, name)
    raise RegistryError(f"{name} is not in the registry")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
