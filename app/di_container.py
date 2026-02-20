from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app.application.conversation_runner import ConversationRunner
from app.application.conversation_service import ConversationService
from app.infrastructure.audio.listener import Listener
from app.infrastructure.audio.speaker import Speaker
from app.config import AppConfig
from app.infrastructure.openai.chat_client import OpenAIChatClient
from app.infrastructure.openai.speech_to_text import SpeechToText as OpenAISpeechToText
from app.infrastructure.openai.text_to_speech import TextToSpeech as OpenAITextToSpeech
from app.application.port.chat_client import ChatClient
from app.application.port.speech_to_text import SpeechToText
from app.application.port.text_to_speech import TextToSpeech
from app.utils.logger import Logger


@dataclass(frozen=True)
class AppContainer:
    config: AppConfig
    logger: Logger
    listener: Listener
    speaker: Speaker
    chat_client: ChatClient
    stt: SpeechToText
    tts: TextToSpeech
    conversation_service: ConversationService
    conversation_runner: ConversationRunner


def build_container(
    config: AppConfig,
    *,
    logger: Logger | None = None,
    listener: Listener | None = None,
    speaker: Speaker | None = None,
    chat_client: ChatClient | None = None,
    stt: SpeechToText | None = None,
    tts: TextToSpeech | None = None,
    system_prompt: str | None = None,
) -> AppContainer:
    logger = logger or Logger()
    listener = listener or Listener()
    speaker = speaker or Speaker(sample_rate=24_000)

    if system_prompt is None:
        system_prompt = config.resolve_system_prompt()

    if chat_client is None or stt is None or tts is None:
        openai_client = OpenAI(
            api_key=config.openai.api_key,
            base_url=config.openai.base_url,
        )

        chat_client = chat_client or OpenAIChatClient(
            client=openai_client,
            model=config.openai.model,
        )

        if stt is None:
            if config.stt.provider == "local":
                from app.infrastructure.local.speech_to_text import (
                    SpeechToText as LocalSpeechToText,
                )

                stt = LocalSpeechToText(model=config.stt.local_model, logger=logger)
            else:
                stt = OpenAISpeechToText(client=openai_client)

        tts = tts or OpenAITextToSpeech(client=openai_client)

    conversation_service = ConversationService(
        chat_client=chat_client,
        system_prompt=system_prompt,
    )

    conversation_runner = ConversationRunner(
        listener=listener,
        stt=stt,
        conversation_service=conversation_service,
        tts=tts,
        speaker=speaker,
        logger=logger,
    )

    return AppContainer(
        config=config,
        logger=logger,
        listener=listener,
        speaker=speaker,
        chat_client=chat_client,
        stt=stt,
        tts=tts,
        conversation_service=conversation_service,
        conversation_runner=conversation_runner,
    )
