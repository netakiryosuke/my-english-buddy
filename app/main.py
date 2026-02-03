from __future__ import annotations

import sys

from openai import (
    OpenAI,
    APIConnectionError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)

from app.audio.listener import Listener
from app.audio.speech_to_text import SpeechToText
from app.application.conversation_service import ConversationService
from app.config import AppConfig
from app.llm.openai_client import OpenAIChatClient
from app.utils.args import parse_args
from app.utils.env import load_dotenv


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    load_dotenv(args.env_file)

    try:
        config = AppConfig.from_env()

        openai_client = OpenAI(
            api_key=config.openai.api_key,
            base_url=config.openai.base_url,
        )

        listener = Listener()
        audio = listener.listen()

        stt = SpeechToText(client=openai_client)
        user_text = stt.transcribe(audio)

        if not user_text:
            return 0

        chat_client = OpenAIChatClient(client=openai_client, model=config.openai.model)
        conversation_service = ConversationService(chat_client=chat_client)

        prompt = config.resolve_system_prompt()

        if prompt is not None:
            conversation_service.system_prompt = prompt

        reply = conversation_service.reply(user_text)
        print(reply)
        return 0

    except ValueError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 2
    except AuthenticationError as e:
        print("OpenAI auth error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 3
    except RateLimitError as e:
        print("OpenAI rate limit error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 4
    except APIConnectionError as e:
        print("OpenAI connection error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 5
    except OpenAIError as e:
        print("OpenAI error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 6
    except Exception as e:
        print("Unexpected error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 8


if __name__ == "__main__":
    raise SystemExit(main())
