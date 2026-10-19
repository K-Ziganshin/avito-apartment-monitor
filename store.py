"""Remembers which listings were already sent, so restarts do not produce duplicates."""

from __future__ import annotations

from pathlib import Path


class SeenStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> set[str]:
        if not self.path.exists():
            return set()
        return {line for line in self.path.read_text(encoding="utf-8").splitlines() if line}

    def add(self, ad_id: str) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(f"{ad_id}\n")
