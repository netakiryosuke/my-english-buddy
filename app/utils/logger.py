from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

class Logger:
    def __init__(
        self,
        *,
        log_dir: Path = Path("logs"),
        on_emit: Callable[[str], None] | None = None,
    ):
        self.log_dir = log_dir
        self._on_emit: Callable[[str], None] | None = None

        self._lines: list[str] = []
        self._started_at = datetime.now()

        # Set via property to keep replay behavior consistent.
        self.on_emit = on_emit

    @property
    def on_emit(self) -> Callable[[str], None] | None:
        return self._on_emit

    @on_emit.setter
    def on_emit(self, callback: Callable[[str], None] | None) -> None:
        # Only replay buffered logs when the first subscriber is attached.
        should_replay = self._on_emit is None and callback is not None
        self._on_emit = callback

        if should_replay:
            for line in self._lines:
                callback(line)

    def log(self, message: str) -> None:
        if not message:
            return

        self._lines.append(message)

        if self._on_emit:
            self._on_emit(message)

    def save(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)

        filename = self._started_at.strftime("%Y-%m-%d_%H-%M-%S.txt")
        path = self.log_dir / filename

        path.write_text("\n".join(self._lines), encoding="utf-8")
