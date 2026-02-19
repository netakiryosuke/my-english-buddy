from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QTextEdit

from app.presentation.conversation_worker import ConversationWorker


class MainWindow(QMainWindow):
    def __init__(self, worker: ConversationWorker):
        super().__init__()
        self.worker = worker

        self.setWindowTitle("My English Buddy")
        self.resize(600, 400)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.setCentralWidget(self.log_view)

        self._setup_menu()
        self.statusBar().showMessage("Ready")

        self.worker.log.connect(self.append_log)
        self.worker.calibration_started.connect(self.on_calibration_started)
        self.worker.calibration_finished.connect(self.on_calibration_finished)
        self.worker.calibration_failed.connect(self.on_calibration_failed)

    def _setup_menu(self) -> None:
        tools_menu = self.menuBar().addMenu("Tools")

        self.calibrate_action = QAction("ノイズキャリブレーション", self)
        self.calibrate_action.triggered.connect(self.on_request_calibration)
        tools_menu.addAction(self.calibrate_action)

    def on_request_calibration(self) -> None:
        self.calibrate_action.setEnabled(False)
        self.statusBar().showMessage("Calibrating noise level...")
        self.worker.request_noise_calibration()

    def on_calibration_started(self) -> None:
        # Status is already set in on_request_calibration (also covers non-UI triggers).
        self.calibrate_action.setEnabled(False)
        self.statusBar().showMessage("Calibrating noise level...")

    def on_calibration_finished(self, threshold: float) -> None:
        self.calibrate_action.setEnabled(True)
        self.statusBar().showMessage(
            f"Noise calibration complete (threshold={threshold:.6f})"
        )

    def on_calibration_failed(self, message: str) -> None:
        self.calibrate_action.setEnabled(True)
        self.statusBar().showMessage(f"Noise calibration failed ({message})")

    def append_log(self, text: str):
        self.log_view.append(text)
