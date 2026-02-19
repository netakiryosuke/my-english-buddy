from PySide6.QtCore import QThread, Signal

from app.application.conversation_runner import ConversationRunner


class ConversationWorker(QThread):
    log = Signal(str)
    calibration_started = Signal()
    calibration_finished = Signal(float)
    calibration_failed = Signal(str)

    def __init__(self, runner: ConversationRunner):
        super().__init__()
        self.runner = runner

        self.runner.logger.on_emit = self.log.emit

        # Bridge calibration events to the UI.
        self.runner.on_calibration_start = self.calibration_started.emit
        self.runner.on_calibration_end = self.calibration_finished.emit
        self.runner.on_calibration_error = lambda e: self.calibration_failed.emit(
            str(e)
        )

    def request_noise_calibration(self) -> None:
        self.runner.request_noise_recalibration()

    def run(self) -> None:
        try:
            self.runner.run()
        except Exception as e:
            self.log.emit(f"Unexpected error: {e}")
