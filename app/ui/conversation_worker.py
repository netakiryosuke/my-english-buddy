from PySide6.QtCore import QThread, Signal
from openai import (
    APIConnectionError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)

from app.application.conversation_runner import ConversationRunner

class ConversationWorker(QThread):
    log = Signal(str)

    def __init__(self, runner: ConversationRunner):
        super().__init__()
        self.runner = runner

        self.runner.on_log = self.log.emit

    def run(self):
        try:
            self.runner.run()
        except ValueError as e:
            self.log.emit(f"Config error: {e}")
        except AuthenticationError as e:
            self.log.emit(f"OpenAI auth error: {e}")
        except RateLimitError as e:
            self.log.emit(f"OpenAI rate limit error: {e}")
        except APIConnectionError as e:
            self.log.emit(f"OpenAI connection error: {e}")
        except OpenAIError as e:
            self.log.emit(f"OpenAI error: {e}")
        except Exception as e:
            self.log.emit(f"Unexpected error: {e}")
