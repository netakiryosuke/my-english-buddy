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
        self.on_emit = on_emit

        self._lines: list[str] = []
        self._started_at = datetime.now()

    def log(self, message: str) -> None:
        if not message:
            return

        self._lines.append(message)

        if self.on_emit:
            self.on_emit(message)

    def save(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)

        filename = self._started_at.strftime("%Y-%m-%d_%H-%M-%S.txt")
        path = self.log_dir / filename

        path.write_text("\n".join(self._lines), encoding="utf-8")
