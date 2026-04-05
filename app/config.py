import os
from dataclasses import dataclass
from typing import Literal

from app.utils.text import read_text_file

DEFAULT_SYSTEM_PROMPT_FILE = "prompt.txt"


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str
    base_url: str | None = None


@dataclass(frozen=True)
class SpeechToTextConfig:
    provider: Literal["openai", "local"] = "openai"
    local_model: str = "distil-large-v3"


@dataclass(frozen=True)
class TextToSpeechConfig:
    provider: Literal["openai", "local"] = "openai"
    # None の場合は各実装のデフォルトボイスを使用する。
    # OpenAI: "alloy" / Kokoro: "af_heart"
    voice: str | None = None
    # Kokoro 専用: "a"=American English, "j"=Japanese, "b"=British English など
    local_lang_code: str = "a"


@dataclass(frozen=True)
class AppConfig:
    openai: OpenAIConfig
    stt: SpeechToTextConfig = SpeechToTextConfig()
    tts: TextToSpeechConfig = TextToSpeechConfig()
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

        stt_provider = (os.getenv("MY_ENGLISH_BUDDY_STT_PROVIDER") or "openai").strip().lower()
        if stt_provider not in {"openai", "local"}:
            raise ValueError(
                "MY_ENGLISH_BUDDY_STT_PROVIDER must be 'openai' or 'local'. "
                f"Got: {stt_provider!r}"
            )

        local_stt_model = (os.getenv("MY_ENGLISH_BUDDY_LOCAL_STT_MODEL") or "distil-large-v3").strip()

        tts_provider = (os.getenv("MY_ENGLISH_BUDDY_TTS_PROVIDER") or "openai").strip().lower()
        if tts_provider not in {"openai", "local"}:
            raise ValueError(
                "MY_ENGLISH_BUDDY_TTS_PROVIDER must be 'openai' or 'local'. "
                f"Got: {tts_provider!r}"
            )

        tts_voice = (os.getenv("MY_ENGLISH_BUDDY_TTS_VOICE") or "").strip() or None
        tts_lang_code = (os.getenv("MY_ENGLISH_BUDDY_TTS_LANG_CODE") or "a").strip()

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
            stt=SpeechToTextConfig(
                provider=stt_provider,
                local_model=local_stt_model,
            ),
            tts=TextToSpeechConfig(
                provider=tts_provider,
                voice=tts_voice,
                local_lang_code=tts_lang_code,
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
