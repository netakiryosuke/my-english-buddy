import inspect

import numpy as np

from app.application.errors import SpeechToTextError
from app.utils.logger import Logger

try:
    from faster_whisper import WhisperModel
except ModuleNotFoundError as e:
    raise SpeechToTextError(
        "Local STT provider requires 'faster-whisper'. "
        "Install it with: uv sync --extra local-stt"
    ) from e
except Exception as e:
    raise SpeechToTextError(
        "Failed to import local STT dependencies. "
        "If you want GPU acceleration, install CUDA 12 + cuDNN and ensure your system can find their libraries (for example via the OS's standard library search path). "
        f"Original error: {e}"
    ) from e


class SpeechToText:
    def __init__(
        self,
        *,
        model: str = "distil-large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "en",
        vad_filter: bool = True,
        vad_threshold: float = 0.6,
        vad_min_speech_duration_ms: int = 250,
        vad_min_silence_duration_ms: int = 600,
        vad_speech_pad_ms: int = 200,
        logger: Logger | None = None,
    ) -> None:
        self.model_name = model
        self.language = language
        self._logger = logger

        self._vad_filter = bool(vad_filter)
        # These are passed to faster-whisper's Silero VAD integration.
        # Keep defaults conservative: reduce false positives without breaking short wake words.
        self._vad_parameters: dict[str, float | int] = {
            "threshold": float(vad_threshold),
            "min_speech_duration_ms": int(vad_min_speech_duration_ms),
            "min_silence_duration_ms": int(vad_min_silence_duration_ms),
            "speech_pad_ms": int(vad_speech_pad_ms),
        }

        self.device: str | None = None
        self.compute_type: str | None = None

        self._transcribe_supports_vad_filter: bool = False
        self._transcribe_supports_vad_parameters: bool = False
        self._logged_no_vad_support: bool = False

        self._log(
            "[STT] Initializing local STT (faster-whisper): "
            f"model={self.model_name}, requested_device={device}, requested_compute_type={compute_type}"
        )

        if self._vad_filter:
            self._log(
                "[STT] Local STT VAD enabled: "
                f"vad_parameters={self._vad_parameters}"
            )
        else:
            self._log("[STT] Local STT VAD disabled")

        preferred_device = device
        preferred_compute_type = compute_type

        try:
            self._model = WhisperModel(
                self.model_name,
                device=preferred_device,
                compute_type=preferred_compute_type,
                num_workers=2,
            )
            self.device = preferred_device
            self.compute_type = preferred_compute_type
        except Exception as e:
            message = str(e)
            likely_missing_cuda_libs = (
                "cublas64_12.dll" in message
                or "cudnn" in message.lower()
                or "cublas" in message.lower()
                or "cuda" in message.lower()
            )

            if likely_missing_cuda_libs and preferred_device == "cuda":
                # Keep the config surface minimal: automatically fall back to CPU.
                self._log(
                    "[STT] Failed to initialize on CUDA; falling back to CPU (int8). "
                    f"Original error: {e}"
                )
                try:
                    self._model = WhisperModel(
                        self.model_name,
                        device="cpu",
                        compute_type="int8",
                        num_workers=1,
                    )
                    self.device = "cpu"
                    self.compute_type = "int8"
                except Exception as cpu_e:
                    raise SpeechToTextError(
                        "Failed to initialize local STT model on GPU and CPU. "
                        "GPU path requires CUDA 12 + cuDNN 9 (and cuBLAS) installed and discoverable. "
                        "CPU fallback uses int8 and should work without CUDA. "
                        "You can also switch back to OpenAI STT (MY_ENGLISH_BUDDY_STT_PROVIDER=openai). "
                        f"GPU error: {e} | CPU error: {cpu_e}"
                    ) from cpu_e

            raise SpeechToTextError(
                "Failed to initialize local STT model. "
                "If you want to use GPU, ensure CUDA 12 + cuDNN 9 are installed. "
                "Otherwise switch back to OpenAI STT (MY_ENGLISH_BUDDY_STT_PROVIDER=openai). "
                f"Original error: {e}"
            ) from e

        # Log device info after successful initialization.
        self._log(
            f"[STT] Local STT initialized: device={self.device}, compute_type={self.compute_type}"
        )
        self._log(self._format_cuda_device_info())

        self._detect_transcribe_feature_support()

    def _detect_transcribe_feature_support(self) -> None:
        # Feature-detect supported kwargs for transcribe() to avoid relying on TypeError messages.
        try:
            params = inspect.signature(self._model.transcribe).parameters
            self._transcribe_supports_vad_filter = "vad_filter" in params
            self._transcribe_supports_vad_parameters = "vad_parameters" in params
        except Exception as e:
            # Be conservative if introspection fails; do not attempt to pass VAD kwargs.
            self._log(
                "[STT] Failed to inspect transcribe() signature; disabling VAD kwargs. "
                f"Error: {e}"
            )
            self._transcribe_supports_vad_filter = False
            self._transcribe_supports_vad_parameters = False

    def _log(self, message: str) -> None:
        if not message:
            return
        if self._logger:
            self._logger.log(message)

    def _format_cuda_device_info(self) -> str:
        if self.device != "cuda":
            return ""
        try:
            import ctranslate2

            count = ctranslate2.get_cuda_device_count()
            return f"[STT] CTranslate2 CUDA device count: {count}"
        except Exception:
            return ""

    def transcribe(self, audio: np.ndarray) -> str:
        try:
            audio_arr = np.asarray(audio, dtype=np.float32)

            if audio_arr.ndim == 1:
                audio_1d = audio_arr
            elif audio_arr.ndim == 2:
                # Allow multi-channel audio by downmixing to mono.
                # Listener can be configured with multiple channels, e.g. (samples, channels).
                # Some audio stacks may produce (channels, samples), so handle both.
                if audio_arr.shape[0] >= audio_arr.shape[1]:
                    # (samples, channels)
                    audio_1d = audio_arr.mean(axis=1)
                else:
                    # (channels, samples)
                    audio_1d = audio_arr.mean(axis=0)
            else:
                raise ValueError(
                    f"Expected 1D mono audio or 2D multi-channel audio. Got shape={audio_arr.shape!r}"
                )

            # Listener produces float32 PCM in [-1, 1] at 16kHz.
            audio_1d = np.clip(audio_1d, -1.0, 1.0)
            audio_1d = np.ascontiguousarray(audio_1d)

            base_kwargs = {
                "language": self.language,
                "condition_on_previous_text": False,
                "without_timestamps": True,
                "beam_size": 5,
            }

            transcribe_kwargs = dict(base_kwargs)
            if self._transcribe_supports_vad_filter:
                transcribe_kwargs["vad_filter"] = bool(self._vad_filter)

            if self._vad_filter:
                if self._transcribe_supports_vad_parameters:
                    transcribe_kwargs["vad_parameters"] = self._vad_parameters
                elif not self._logged_no_vad_support:
                    # VAD requested but not supported by the installed faster-whisper version.
                    self._logged_no_vad_support = True
                    self._log("[STT] Installed faster-whisper does not support vad_parameters; continuing without it.")

            segments, _info = self._model.transcribe(audio_1d, **transcribe_kwargs)

            # `segments` is a generator; force evaluation.
            text = "".join(segment.text for segment in segments).strip()
            return text
        except SpeechToTextError:
            raise
        except Exception as e:
            raise SpeechToTextError(str(e)) from e
