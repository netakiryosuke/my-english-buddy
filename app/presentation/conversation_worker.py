from PySide6.QtCore import QThread, Signal

from app.application.conversation_runner import ConversationRunner


class ConversationWorker(QThread):
    log = Signal(str)

    def __init__(self, runner: ConversationRunner):
        super().__init__()
        self.runner = runner

        self.runner.logger.on_emit = self.log.emit

    def run(self) -> None:
        try:
            self.runner.run()
        except Exception as e:
            self.log.emit(f"Unexpected error: {e}")
