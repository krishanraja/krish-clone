"""A listening panel for the blind A/B: one shuffled pair set per listener, their answers recorded back against the
key, and the scored record Krish approves.

The listener list names real people, so it lives only on Krish's machines or Drive, never in this public repository.
The panel and the record refer to listeners by id (L01, L02, ...) and carry the list's sha256, never a name.

1. `clone abpack` builds the pack and its key (evaluate.ab_pack).
2. `clone abpanel` gives every listener on the list their own folder: the same pairs in their own order, each pair's
   two clips as 1 and 2 in their own order, a sheet to fill in and the instructions. Their page is made from that
   folder later, through SendLinks, and only once Krish has approved the list (docs/EVALUATION.md).
3. `clone abrecord` reads one listener's filled sheet and appends their answers, mapped back to the pack's pairs and
   letters, to the panel's answers.csv.
4. `clone abscore --record` scores the answers and writes the record. Its sha256 is what Krish approves, and what the
   registry holds (krish_clone/registry.py).
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import json
import random
import re
import shutil
from pathlib import Path

from . import evaluate, registry

LISTENERS_FORMAT = "krish-clone.listeners/1"
PANEL_FORMAT = "krish-clone.ab-panel/1"
RECORD_FORMAT = "krish-clone.scored-pack/1"
MIN_LISTENERS = 10  # docs/EVALUATION.md: fewer cannot tell 60% from chance
MIN_PAIRS = 10
LISTENER_ID = re.compile(r"^L\d{2,3}$")
PANEL_KEY = "PANEL-KEY-do-not-share.json"
ANSWERS = "answers.csv"
SHEET = "sheet.csv"
CHOICES = ("1", "2")
HOW_TO = (
    "Each numbered pair has two clips of Krish, 1 and 2. One is a real recording and one is generated.\n"
    "Listen to both, then write 1 or 2 in sheet.csv for the one you think is generated. Every pair needs an\n"
    "answer: guess if unsure. Do not compare notes with anyone else; everyone hears the pairs in a different order.\n"
)


class Refused(Exception):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(data) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _digest(data) -> str:
    return hashlib.sha256(_canonical(data)).hexdigest()


def load_listeners(path: Path) -> dict:
    """The local listener list: ids, names, and Krish's approval of the list once he gives it. Adding his approval
    leaves the list's digest unchanged, so a panel built before it still matches."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as failed:
        raise Refused(f"cannot read the listener list {path}: {failed}") from None
    if not isinstance(data, dict) or data.get("format") != LISTENERS_FORMAT:
        raise Refused(f"{path}: format is not {LISTENERS_FORMAT}")
    people = data.get("listeners")
    if not isinstance(people, list) or len(people) < MIN_LISTENERS:
        raise Refused(f"{path}: at least {MIN_LISTENERS} listeners who know Krish (docs/EVALUATION.md)")
    ids = []
    for index, person in enumerate(people):
        if not isinstance(person, dict) or not LISTENER_ID.match(str(person.get("id", ""))):
            raise Refused(f"{path}: listeners[{index}] needs an id such as L01")
        if not str(person.get("name", "")).strip():
            raise Refused(f"{path}: listener {person['id']} has no name")
        ids.append(person["id"])
    if len(set(ids)) != len(ids):
        raise Refused(f"{path}: a listener id appears twice")
    approval = data.get("approval")
    if approval is not None:
        try:
            registry.check_words((approval or {}).get("words"), "approval.words")
            registry.check_date((approval or {}).get("on"), "approval.on")
        except registry.RegistryError as problem:
            raise Refused(f"{path}: {problem}") from None
    return {"ids": ids, "sha256": _digest(people), "approval": approval}


def _read_key(key_path: Path) -> tuple[list[dict], Path]:
    key = json.loads(Path(key_path).read_text(encoding="utf-8"))
    pairs = key["pairs"]
    pack = Path(key_path).parent / "pack"
    return pairs, pack


def _clip(pack: Path, pair: str, letter: str) -> Path:
    found = sorted(pack.glob(f"{pair}_{letter}.*"))
    if len(found) != 1:
        raise Refused(f"{pack}: expected one clip for {pair} {letter}, found {len(found)}")
    return found[0]


def build(key_path: Path, listeners_path: Path, out: Path, *, seed: int | None = None) -> dict:
    """One folder per listener with the pairs in their own order and each pair's clips as 1 and 2 in their own
    order. Nothing is sent: the folders wait for the page, and the page waits for Krish's yes on the list."""
    key_path, out = Path(key_path), Path(out)
    pairs, pack = _read_key(key_path)
    if len(pairs) < MIN_PAIRS:
        raise Refused(f"the pack has {len(pairs)} pairs; the test needs at least {MIN_PAIRS} (docs/EVALUATION.md)")
    listeners = load_listeners(listeners_path)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"{out} already holds a panel; choose a new --out")
    clips = {(p["pair"], letter): _clip(pack, p["pair"], letter) for p in pairs for letter in "AB"}
    rng = random.Random(seed)
    items: dict[str, list[dict]] = {}
    for listener in listeners["ids"]:
        order = [p["pair"] for p in pairs]
        rng.shuffle(order)
        folder = out / listener
        folder.mkdir(parents=True)
        plan = []
        for number, pair in enumerate(order, 1):
            first = rng.choice("AB")
            second = "B" if first == "A" else "A"
            for choice, letter in (("1", first), ("2", second)):
                source = clips[(pair, letter)]
                shutil.copyfile(source, folder / f"pair{number:02d}-{choice}{source.suffix.lower()}")
            plan.append({"item": number, "pair": pair, "1": first, "2": second})
        with (folder / SHEET).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["item", "choice"])
            for entry in plan:
                writer.writerow([entry["item"], ""])
        (folder / "HOW-TO.txt").write_text(HOW_TO, encoding="utf-8")
        items[listener] = plan
    panel = {
        "format": PANEL_FORMAT,
        "key_file": str(key_path.resolve()),
        "key_sha256": sha256_file(key_path),
        "listeners_file": str(Path(listeners_path).resolve()),
        "listeners_sha256": listeners["sha256"],
        "pairs": len(pairs),
        "items": items,
    }
    (out / PANEL_KEY).write_bytes(_canonical(panel))
    with (out / ANSWERS).open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(["listener", "pair", "choice"])
    panel["listeners_approved"] = listeners["approval"] is not None
    return panel


def _read_panel(panel_dir: Path) -> dict:
    path = Path(panel_dir) / PANEL_KEY
    try:
        panel = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as failed:
        raise Refused(f"cannot read the panel key {path}: {failed}") from None
    if panel.get("format") != PANEL_FORMAT:
        raise Refused(f"{path}: format is not {PANEL_FORMAT}")
    return panel


def _answer_rows(path: Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def record_answers(panel_dir: Path, listener: str, sheet: Path) -> int:
    """Append one listener's filled sheet to the panel's answers.csv, mapped back to the pack's pairs and letters.
    Refused when the listener was already recorded, or any pair is missing or not answered 1 or 2."""
    panel = _read_panel(panel_dir)
    plan = panel["items"].get(listener)
    if plan is None:
        raise Refused(f"{listener} is not on this panel")
    answers = Path(panel_dir) / ANSWERS
    if any(row.get("listener") == listener for row in _answer_rows(answers)):
        raise Refused(f"{listener}'s answers are already recorded")
    given: dict[int, str] = {}
    for row in _answer_rows(sheet):
        try:
            item = int(str(row.get("item", "")).strip())
        except ValueError:
            raise Refused(f"{sheet}: item {row.get('item')!r} is not a pair number") from None
        if item in given:
            raise Refused(f"{sheet}: pair {item} is answered twice")
        given[item] = str(row.get("choice", "")).strip()
    numbers = [entry["item"] for entry in plan]
    missing = [n for n in numbers if given.get(n) not in CHOICES]
    extra = sorted(set(given) - set(numbers))
    if missing:
        raise Refused(f"{sheet}: pairs {', '.join(map(str, missing))} need 1 or 2")
    if extra:
        raise Refused(f"{sheet}: pairs {', '.join(map(str, extra))} are not on this listener's sheet")
    with answers.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for entry in plan:
            writer.writerow([listener, entry["pair"], entry[given[entry["item"]]]])
    return len(plan)


def _pack_files(pack: Path) -> dict[str, str]:
    return {p.name: sha256_file(p) for p in sorted(pack.iterdir()) if p.is_file()}


def write_record(key_path: Path, answers_path: Path, panel_dir: Path, out: Path, *, name: str, kind: str,
                 platform: str, today: str | None = None) -> tuple[dict, str]:
    """Score the panel's answers and write the record Krish approves. Refused below the bar's size (10 listeners,
    10 pairs, every listener answering every pair once), when the answers or key are not this panel's, or when Krish
    has not approved the listener list. Never overwrites a record."""
    key_path, answers_path, out = Path(key_path), Path(answers_path), Path(out)
    try:
        registry.check_name(name)
        registry.check_kind(kind, platform)
    except registry.RegistryError as problem:
        raise Refused(str(problem)) from None
    if out.exists():
        raise FileExistsError(f"{out} already exists; a record is never overwritten")
    panel = _read_panel(panel_dir)
    if sha256_file(key_path) != panel["key_sha256"]:
        raise Refused("the key is not the one this panel was built from")
    listeners = load_listeners(Path(panel["listeners_file"]))
    if listeners["sha256"] != panel["listeners_sha256"]:
        raise Refused("the listener list changed since the panel was built; build a new panel")
    if listeners["approval"] is None:
        raise Refused("Krish has not approved the listener list (its approval: his words and the date)")
    pairs, pack = _read_key(key_path)
    key = {p["pair"]: p["clone"] for p in pairs}
    heard: dict[str, list[str]] = {}
    for row in _answer_rows(answers_path):
        who, pair, choice = row.get("listener", ""), row.get("pair", ""), str(row.get("choice", "")).strip().upper()
        if who not in panel["items"]:
            raise Refused(f"answers name {who!r}, who is not on this panel")
        if pair not in key or choice not in ("A", "B"):
            raise Refused(f"answers: {who} {pair} {choice!r} is not a pair and A or B")
        heard.setdefault(who, []).append(pair)
    for who, answered in heard.items():
        if sorted(answered) != sorted(key):
            raise Refused(f"{who} did not answer every pair exactly once")
    if len(heard) < MIN_LISTENERS or len(key) < MIN_PAIRS:
        raise Refused(f"{len(heard)} listeners and {len(key)} pairs; the bar needs at least {MIN_LISTENERS} of each")
    score = evaluate.ab_score(key_path, answers_path)
    score["pairs"] = len(key)
    record = {
        "format": RECORD_FORMAT,
        "clone": {"name": name, "kind": kind, "platform": platform},
        "scored_on": today or datetime.date.today().isoformat(),
        "pack": {"sha256": _digest(_pack_files(pack)), "files": _pack_files(pack)},
        "key_sha256": panel["key_sha256"],
        "panel_sha256": sha256_file(Path(panel_dir) / PANEL_KEY),
        "answers_sha256": sha256_file(answers_path),
        "listeners": {"count": len(heard), "sha256": listeners["sha256"], "approved_on": listeners["approval"]["on"]},
        "score": score,
    }
    data = _canonical(record)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return record, hashlib.sha256(data).hexdigest()


def read_record(path: Path) -> tuple[dict, str]:
    """A record and the sha256 of its bytes, refused unless it is one Krish can approve: this format, a passing
    verdict, at least 10 listeners and 10 pairs, and a listener list he approved."""
    data = Path(path).read_bytes()
    try:
        record = json.loads(data)
    except json.JSONDecodeError as failed:
        raise Refused(f"{path}: not JSON: {failed}") from None
    if record.get("format") != RECORD_FORMAT:
        raise Refused(f"{path}: format is not {RECORD_FORMAT}")
    clone, score = record.get("clone") or {}, record.get("score") or {}
    try:
        registry.check_name(clone.get("name"))
        registry.check_kind(clone.get("kind"), clone.get("platform"))
        registry.check_date(record.get("scored_on"), "scored_on")
    except registry.RegistryError as problem:
        raise Refused(f"{path}: {problem}") from None
    if score.get("verdict") != "pass":
        raise Refused(f"{path}: the clone failed the blind A/B ({score.get('picked_the_clone')} picked it)")
    if score.get("listeners", 0) < MIN_LISTENERS or score.get("pairs", 0) < MIN_PAIRS:
        raise Refused(f"{path}: fewer than {MIN_LISTENERS} listeners or {MIN_PAIRS} pairs")
    if not (record.get("listeners") or {}).get("approved_on"):
        raise Refused(f"{path}: no approved listener list")
    return record, hashlib.sha256(data).hexdigest()
