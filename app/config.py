from __future__ import annotations

import os
from dataclasses import dataclass
from app.utils.text import read_text_file

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_SYSTEM_PROMPT_FILE = "prompt.txt"


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str
    base_url: str | None = None


@dataclass(frozen=True)
class AppConfig:
    openai: OpenAIConfig
    system_prompt: str | None = None
    system_prompt_file: str | None = DEFAULT_SYSTEM_PROMPT_FILE

    @staticmethod
    def from_env() -> "AppConfig":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required.")

        model = os.getenv("OPENAI_MODEL")
        if not model:
            raise ValueError("OPENAI_MODEL is required.")

        base_url = os.getenv("OPENAI_BASE_URL") or None

        # TODO: In the real desktop app, this should likely be stored per-user
        # (e.g., in local storage) and editable in the UI.
        system_prompt = os.getenv("MY_ENGLISH_BUDDY_SYSTEM_PROMPT") or None
        system_prompt_file = os.getenv("MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE") or DEFAULT_SYSTEM_PROMPT_FILE

        return AppConfig(
            openai=OpenAIConfig(
                api_key=api_key,
                model=model,
                base_url=base_url,
            ),
            system_prompt=system_prompt,
            system_prompt_file=system_prompt_file,
        )

    def resolve_system_prompt(self) -> str | None:
        """Resolve system prompt from env or file.

        Priority (within config sources):
        1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT`
        2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (default: prompt.txt) if exists & non-empty
        3) None (ConversationService default will be used)
        """

        if self.system_prompt:
            return self.system_prompt
        if not self.system_prompt_file:
            return None

        try:
            text = read_text_file(self.system_prompt_file)
            return text or None
        except FileNotFoundError:
            return None
