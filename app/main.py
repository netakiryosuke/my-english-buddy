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
	user_text = args.prompt

	if user_text is None:
		user_text = sys.stdin.read().strip()
		if not user_text:
			user_text = input("> ").strip()

	load_dotenv(args.env_file)

	try:
		config = AppConfig.from_env()
		chat_client = OpenAIChatClient(config.openai)
		service = ConversationService(chat_client=chat_client)
		if args.system is not None:
			service.system_prompt = args.system

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
