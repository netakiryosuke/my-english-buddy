from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_repo_root_on_sys_path() -> None:
	# Allow running both:
	# - uv run python -m app.main
	# - uv run python app/main.py
	if __package__:
		return
	repo_root = str(Path(__file__).resolve().parents[1])
	if repo_root not in sys.path:
		sys.path.insert(0, repo_root)


def _parse_args(argv: list[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Text-only OpenAI chat test")
	parser.add_argument("prompt", nargs="?", help="User prompt. If omitted, read from stdin.")
	parser.add_argument(
		"--env-file",
		default=".env",
		help="Path to .env file (default: .env). Use empty to disable.",
	)
	parser.add_argument(
		"--system",
		default=None,
		help="Optional system prompt override (otherwise default is used).",
	)
	return parser.parse_args(argv)


def _load_dotenv(env_file: str | None) -> None:
	if not env_file:
		return
	try:
		from dotenv import load_dotenv
	except Exception:
		# Optional in runtime; required dependency is included in pyproject.toml.
		return

	load_dotenv(env_file, override=False)


def main(argv: list[str] | None = None) -> int:
	_ensure_repo_root_on_sys_path()

	from app.application.conversation_service import ConversationService
	from app.config import AppConfig
	from app.llm.openai_client import OpenAIChatClient
	from openai import APIConnectionError, AuthenticationError, OpenAIError, RateLimitError

	args = _parse_args(sys.argv[1:] if argv is None else argv)
	user_text = args.prompt

	if user_text is None:
		user_text = sys.stdin.read().strip()
		if not user_text:
			user_text = input("> ").strip()

	_load_dotenv(args.env_file)

	try:
		config = AppConfig.from_env()
		chat_client = OpenAIChatClient(config.openai)
		service = ConversationService(chat_client=chat_client)
		if args.system is not None:
			service.system_prompt = args.system

		reply = service.reply(user_text)
		print(reply)
		return 0
	except ValueError as exc:
		print(f"Config error: {exc}", file=sys.stderr)
		return 2
	except AuthenticationError as exc:
		print("OpenAI auth error: invalid API key or base URL.", file=sys.stderr)
		print(str(exc), file=sys.stderr)
		return 3
	except RateLimitError as exc:
		print("OpenAI rate limit error.", file=sys.stderr)
		print(str(exc), file=sys.stderr)
		return 4
	except APIConnectionError as exc:
		print("OpenAI connection error (network/timeout).", file=sys.stderr)
		print(str(exc), file=sys.stderr)
		return 5
	except OpenAIError as exc:
		print("OpenAI error.", file=sys.stderr)
		print(str(exc), file=sys.stderr)
		return 6


if __name__ == "__main__":
	raise SystemExit(main())
