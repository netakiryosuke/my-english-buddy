"""Unit tests for local Kokoro TTS implementation."""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.application.errors import TextToSpeechError


@pytest.fixture(autouse=True)
def mock_kokoro(monkeypatch):
    """kokoro が未インストールの環境でもテストできるよう sys.modules にモックを差し込む。"""
    mock = MagicMock()
    mock_pipeline = MagicMock()
    mock.KPipeline.return_value = mock_pipeline
    monkeypatch.setitem(sys.modules, "kokoro", mock)
    # モジュールキャッシュをクリアして再インポートさせる。
    sys.modules.pop("app.infrastructure.local.text_to_speech", None)
    yield mock
    sys.modules.pop("app.infrastructure.local.text_to_speech", None)


def make_sut(voice: str = "af_heart", lang_code: str = "a"):
    from app.infrastructure.local.text_to_speech import TextToSpeech
    return TextToSpeech(voice=voice, lang_code=lang_code)


class TestSynthesize:
    def test_returns_float32_array(self, mock_kokoro):
        """synthesize() は float32 の np.ndarray を返す。"""
        sut = make_sut()
        sut._pipeline.return_value = [("", "", np.array([0.1, 0.2, 0.3], dtype=np.float32))]

        result = sut.synthesize("Hello")

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32

    def test_concatenates_multiple_chunks(self, mock_kokoro):
        """KPipeline が複数チャンクを返す場合、すべて結合される。"""
        sut = make_sut()
        sut._pipeline.return_value = [
            ("", "", np.array([0.1, 0.2], dtype=np.float32)),
            ("", "", np.array([0.3, 0.4], dtype=np.float32)),
        ]

        result = sut.synthesize("Hello world")

        np.testing.assert_array_almost_equal(result, [0.1, 0.2, 0.3, 0.4])

    def test_passes_text_and_voice_to_pipeline(self, mock_kokoro):
        """synthesize() はテキストとボイスを KPipeline に渡す。"""
        sut = make_sut(voice="am_michael")
        sut._pipeline.return_value = [("", "", np.array([0.0], dtype=np.float32))]

        sut.synthesize("Test text")

        sut._pipeline.assert_called_once_with("Test text", voice="am_michael")

    def test_returns_empty_array_when_no_chunks(self, mock_kokoro):
        """KPipeline がチャンクを返さない場合、空の配列を返す。"""
        sut = make_sut()
        sut._pipeline.return_value = []

        result = sut.synthesize("Hello")

        assert len(result) == 0
        assert result.dtype == np.float32

    def test_wraps_exception_as_tts_error(self, mock_kokoro):
        """KPipeline が例外を送出した場合、TextToSpeechError にラップされる。"""
        sut = make_sut()
        sut._pipeline.side_effect = RuntimeError("synthesis failed")

        with pytest.raises(TextToSpeechError):
            sut.synthesize("Hello")


class TestInit:
    def test_pipeline_init_failure_raises_tts_error(self, mock_kokoro):
        """KPipeline の初期化失敗を TextToSpeechError にラップする。"""
        mock_kokoro.KPipeline.side_effect = RuntimeError("model download failed")

        with pytest.raises(TextToSpeechError, match="Failed to initialize Kokoro TTS pipeline"):
            make_sut()

    def test_import_error_raises_tts_error_with_install_hint(self):
        """kokoro が未インストールの場合、インストール方法を含む TextToSpeechError が送出される。"""
        with patch.dict("sys.modules", {"kokoro": None}):  # type: ignore[dict-item]
            sys.modules.pop("app.infrastructure.local.text_to_speech", None)
            with pytest.raises(TextToSpeechError) as exc_info:
                from app.infrastructure.local.text_to_speech import TextToSpeech
                TextToSpeech()
            assert "uv sync --extra local-tts" in str(exc_info.value)
