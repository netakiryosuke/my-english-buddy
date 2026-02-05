from PySide6.QtWidgets import QMainWindow, QTextEdit
from app.ui.conversation_worker import ConversationWorker


class MainWindow(QMainWindow):
    def __init__(self, worker: ConversationWorker):
        super().__init__()
        self.setWindowTitle("My English Buddy")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.setCentralWidget(self.log_view)

        worker.log.connect(self.append_log)

    def append_log(self, text: str):
        self.log_view.append(text)
