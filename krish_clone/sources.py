"""Which folders the engine may read. Every source starts pending; only Krish approves one."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "config" / "sources.json"
STATUSES = ("pending", "approved", "rejected")


class NotApproved(Exception):
    pass


@dataclass
class Source:
    id: str
    name: str
    drive_id: str
    kind: str
    status: str
    local_path: str | None
    note: str = ""

    @property
    def approved(self) -> bool:
        return self.status == "approved"


def load(path: Path = DEFAULT) -> list[Source]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [_source(entry) for entry in data["sources"]]


def _source(entry: dict) -> Source:
    return Source(**{k: entry.get(k, "" if k == "note" else None) for k in Source.__dataclass_fields__})


def set_status(source_id: str, status: str, path: Path = DEFAULT, *, local_path: str | None = None) -> Source:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for entry in data["sources"]:
        if entry["id"] == source_id:
            entry["status"] = status
            if local_path is not None:
                entry["local_path"] = local_path
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return _source(entry)
    raise KeyError(source_id)


def require_approved(source_id: str, path: Path = DEFAULT) -> Source:
    """The gate every harvest passes: an unknown or unapproved source is never read."""
    for source in load(path):
        if source.id == source_id:
            if not source.approved:
                raise NotApproved(f"source {source_id!r} is {source.status}; Krish approves it first")
            if not source.local_path:
                raise NotApproved(f"source {source_id!r} has no local_path on this machine")
            return source
    raise NotApproved(f"unknown source {source_id!r}")
