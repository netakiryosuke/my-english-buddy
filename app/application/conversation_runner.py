from __future__ import annotations

import os
from queue import Empty, Queue
from pathlib import Path
from threading import Event, Thread

import numpy as np

from app.infrastructure.audio.listener import Listener
from app.infrastructure.audio.speaker import Speaker
from app.application.conversation_service import ConversationService
from app.interface.speech_to_text import SpeechToText
from app.interface.text_to_speech import TextToSpeech
from app.utils.logger import Logger


class ConversationRunner:
    WAKE_WORDS = ["buddy"]

    DEBUG_SAVE_TTS_WAV_ENV = "MEB_DEBUG_SAVE_TTS_WAV"
    DEBUG_SAVE_TTS_DIR_ENV = "MEB_DEBUG_SAVE_TTS_DIR"

    def __init__(
        self,
        listener: Listener,
        stt: SpeechToText,
        conversation_service: ConversationService,
        tts: TextToSpeech,
        speaker: Speaker,
        logger: Logger,
        ) -> None:
        self.listener = listener
        self.stt = stt
        self.conversation_service = conversation_service
        self.tts = tts
        self.speaker = speaker
        self.logger = logger
        self.is_awake = False
        self.reply_queue: Queue[str] = Queue(maxsize=1)
        self.stop_speaking_event = Event()

    def run(self) -> None:
        self._start_speaker_thread()

        while True:
            audio = self.listener.listen()
            user_text = self.stt.transcribe(audio)

            if not user_text:
                continue

            self.stop_speaking_event.set()

            if not self.is_awake:
                if self._detect_wake_word(user_text):
                    self.is_awake = True
                else:
                    continue

            self._log(f"You: {user_text}")

            reply = self.conversation_service.reply(user_text)

            if not reply or not reply.strip():
                continue

            self._log(f"Buddy: {reply}")

            self._publish_reply(reply)

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger.log(message)

    def _detect_wake_word(self, text: str) -> bool:
        normalized_text = text.lower()

        return any(
            wake_word in normalized_text
            for wake_word in self.WAKE_WORDS
        )

    def _publish_reply(self, reply: str) -> None:
        try:
            while True:
                self.reply_queue.get_nowait()
        except Empty:
            pass

        try:
            self.reply_queue.put_nowait(reply)
        except Exception:
            pass

    def _start_speaker_thread(self) -> None:
        thread = Thread(
            target=self._speaker_loop,
            daemon=True,
        )
        thread.start()

    def _speaker_loop(self) -> None:
        while True:
            reply = self.reply_queue.get()

            if not reply:
                continue

            try:
                self.stop_speaking_event.clear()

                reply_audio = self.tts.synthesize(reply)
                self._maybe_debug_save_tts_wav(reply, reply_audio)
                self.speaker.speak(reply_audio, stop_event=self.stop_speaking_event)
            except Exception as e:
                self._log(f"Error in speaker loop: {e}")

                self.stop_speaking_event.set()
                continue

    def _maybe_debug_save_tts_wav(self, text: str, audio: np.ndarray) -> None:
        """Optionally save synthesized audio to WAV for debugging.

        Enable by setting env var `MEB_DEBUG_SAVE_TTS_WAV` to a truthy value.
        This is intended for diagnosing whether truncation occurs during TTS
        synthesis or during playback.
        """

        enabled = os.getenv(self.DEBUG_SAVE_TTS_WAV_ENV, "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not enabled:
            return

        try:
            save_dir = Path(
                os.getenv(self.DEBUG_SAVE_TTS_DIR_ENV, "logs/audio_debug")
            )
            save_dir.mkdir(parents=True, exist_ok=True)

            audio_float = np.asarray(audio, dtype=np.float32)
            if audio_float.ndim == 2:
                audio_float = audio_float.reshape(-1)

            sample_rate = int(getattr(self.speaker, "sample_rate", 24_000))

            abs_audio = np.abs(audio_float)
            threshold = 0.02
            above = np.flatnonzero(abs_audio > threshold)
            lead_silence_ms = (
                float(above[0]) / sample_rate * 1000.0
                if above.size
                else float(len(audio_float)) / sample_rate * 1000.0
            )
            total_ms = float(len(audio_float)) / sample_rate * 1000.0

            # Keep filename filesystem-safe and short.
            safe_prefix = "".join(
                ch for ch in text.strip().replace("\n", " ")[:24]
                if ch.isalnum() or ch in {" ", "-", "_"}
            ).strip().replace(" ", "_")
            if not safe_prefix:
                safe_prefix = "reply"

            from datetime import datetime
            import wave
            from typing import cast

            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
            path = save_dir / f"tts_{stamp}_{safe_prefix}.wav"

            audio_int16 = np.clip(audio_float, -1.0, 1.0)
            audio_int16 = (audio_int16 * 32767.0).astype(np.int16)

            wf = cast(wave.Wave_write, wave.open(str(path), "wb"))
            with wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())

            self._log(
                "[debug] saved TTS wav: "
                f"{path} lead_silence_ms={lead_silence_ms:.1f} total_ms={total_ms:.1f}"
            )
        except (OSError, ValueError, RuntimeError) as e:
            self._log(f"[debug] failed to save TTS wav: {e}")
