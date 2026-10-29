"""Where krish-clone keeps its runtime: the shared Make Your Mind Up layout, never a path written in code.

`config/studio.json` `local_roots.runtime` (read through content-watcher's layout, which prefers content-engine's
copy beside this clone) gives `%LOCALAPPDATA%\\makeyourmindup\\`; krish-clone uses `krish-clone\\` below it for the
venv, models, cache and voice masters. KRISH_CLONE_HOME overrides it (tests, or a one-off machine).
"""

from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def runtime() -> Path:
    chosen = os.environ.get("KRISH_CLONE_HOME")
    if chosen:
        return Path(chosen)
    try:
        from content_watcher import layout

        return layout.load(HERE).runtime_dir("krish-clone")
    except Exception:  # noqa: BLE001 - an older content-watcher without the layout still gets a home
        return Path.home() / ".makeyourmindup" / "krish-clone"
