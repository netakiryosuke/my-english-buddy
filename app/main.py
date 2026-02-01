from __future__ import annotations

import sys

from app.utils.args import parse_args
from app.utils.env import load_dotenv


def main(argv: list[str] | None = None) -> int:
    from app.application.conversation_service import ConversationService
    from app.config import AppConfig
    from app.llm.openai_client import OpenAIChatClient
    from openai import APIConnectionError, AuthenticationError, OpenAIError, RateLimitError

    args = parse_args(sys.argv[1:] if argv is None else argv)
    # TODO: This is a temporary text-only sample. In the real app, user_text will
    # come from Speech-to-Text (STT) results.
    user_text = args.prompt or "Hello! Please correct my English: I has a pen."

    load_dotenv(args.env_file)

    try:
        config = AppConfig.from_env()
        chat_client = OpenAIChatClient(config.openai)
        service = ConversationService(chat_client=chat_client)
        # TODO: system prompt should be user-configurable via UI.
        # Priority: CLI --system > env/file > ConversationService default.
        resolved_system = (
            args.system if args.system is not None else config.resolve_system_prompt()
        )
        if resolved_system is not None:
            service.system_prompt = resolved_system

        reply = service.reply(user_text)
        print(reply)
        return 0
    except ValueError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 2
    except AuthenticationError as e:
        print("OpenAI auth error: invalid API key or base URL.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 3
    except RateLimitError as e:
        print("OpenAI rate limit error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 4
    except APIConnectionError as e:
        print("OpenAI connection error (network/timeout).", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 5
    except OpenAIError as e:
        print("OpenAI error.", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
