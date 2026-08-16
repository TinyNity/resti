"""Persistence for saved icon layouts.

Snapshots are kept in ``%APPDATA%\\Resti\\snapshots.json``
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime

def default_path() -> str:
    directory = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "Resti"
    )
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "snapshots.json")


@dataclass(frozen=True)
class Snapshot:
    """One saved desktop layout."""

    name: str
    saved_at: str
    icons: list[dict]

    @property
    def icon_count(self) -> int:
        return len(self.icons)

    @property
    def date(self) -> str:
        """The ISO timestamp trimmed to just the day."""
        return self.saved_at[:10]

    @property
    def targets(self) -> dict[str, tuple[int, int]]:
        """Icon positions keyed by lower-cased label, ready for ``restore_icons``.

        Desktop labels are case-insensitive and unique per folder, so folding the
        case here matches how Windows itself compares them.
        """
        return {icon["name"].lower(): (icon["x"], icon["y"]) for icon in self.icons}


class SnapshotStore:
    """The collection of saved layouts, backed by a JSON file.

    Every mutation writes straight through to disk: the file is small, and the
    alternative is losing a layout to a crash between saving and closing.
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = path or default_path()
        self._snapshots = self._read()

    def _read(self) -> dict[str, Snapshot]:
        try:
            with open(self.path, encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, ValueError):
            # A missing file is the normal first-run case; a corrupt one is not
            # worth blocking start-up over, since it is rewritten on next save.
            return {}

        return {
            name: Snapshot(
                name=name,
                saved_at=entry.get("saved_at", ""),
                icons=entry.get("icons", []),
            )
            for name, entry in raw.items()
        }

    def _write(self) -> None:
        payload = {
            snapshot.name: {"saved_at": snapshot.saved_at, "icons": snapshot.icons}
            for snapshot in self._snapshots.values()
        }
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def __len__(self) -> int:
        return len(self._snapshots)

    def __contains__(self, name: str) -> bool:
        return name in self._snapshots

    def __getitem__(self, name: str) -> Snapshot:
        return self._snapshots[name]

    def newest_first(self) -> list[Snapshot]:
        return sorted(
            self._snapshots.values(), key=lambda snap: snap.saved_at, reverse=True
        )

    def add(self, name: str, icons: list[dict]) -> Snapshot:
        """Store *icons* under *name*, replacing any snapshot already using it."""
        snapshot = Snapshot(
            name=name,
            saved_at=datetime.now().isoformat(timespec="seconds"),
            icons=icons,
        )
        self._snapshots[name] = snapshot
        self._write()
        return snapshot

    def rename(self, old: str, new: str) -> None:
        snapshot = self._snapshots.pop(old)
        self._snapshots[new] = Snapshot(
            name=new, saved_at=snapshot.saved_at, icons=snapshot.icons
        )
        self._write()

    def delete(self, name: str) -> None:
        del self._snapshots[name]
        self._write()