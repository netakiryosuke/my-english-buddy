from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config import AppConfig
from app.container import build_container
from app.ui.conversation_worker import ConversationWorker
from app.ui.main_window import MainWindow
from app.utils.args import parse_args
from app.utils.env import load_dotenv


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    load_dotenv(args.env_file)

    try:
        config = AppConfig.from_env()
        container = build_container(config)
    except ValueError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Failed to initialize application: {e}", file=sys.stderr)
        return 2

    conversation_worker = ConversationWorker(container.conversation_runner)

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(container.logger.save)

    window = MainWindow(conversation_worker)
    window.show()

    conversation_worker.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
