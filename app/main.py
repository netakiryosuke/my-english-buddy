from __future__ import annotations

import sys

from openai import OpenAI
from PySide6.QtWidgets import QApplication

from app.audio.listener import Listener
from app.audio.speech_to_text import SpeechToText
from app.audio.speaker import Speaker
from app.audio.text_to_speech import TextToSpeech
from app.application.conversation_service import ConversationService
from app.application.conversation_runner import ConversationRunner
from app.config import AppConfig
from app.llm.openai_client import OpenAIChatClient
from app.ui.conversation_worker import ConversationWorker
from app.ui.main_window import MainWindow
from app.utils.args import parse_args
from app.utils.env import load_dotenv
from app.utils.logger import Logger


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    load_dotenv(args.env_file)

    try:
        config = AppConfig.from_env()

        openai_client = OpenAI(
            api_key=config.openai.api_key,
            base_url=config.openai.base_url,
        )

        chat_client = OpenAIChatClient(client=openai_client, model=config.openai.model)

        prompt = config.resolve_system_prompt()
    except ValueError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Failed to initialize application: {e}", file=sys.stderr)
        return 2

    conversation_runner = ConversationRunner(
        listener=Listener(),
        stt=SpeechToText(client=openai_client),
        conversation_service=ConversationService(chat_client=chat_client, system_prompt=prompt),
        tts=TextToSpeech(client=openai_client),
        speaker=Speaker(sample_rate=24_000),
        logger=Logger()
    )

    conversation_worker = ConversationWorker(conversation_runner)

    app = QApplication(sys.argv)
    window = MainWindow(conversation_worker)
    window.show()

    conversation_worker.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
