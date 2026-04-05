"""Unit tests for local Kokoro TTS implementation."""

import sys
import unittest
from unittest.mock import MagicMock, patch

import numpy as np


class TestLocalTextToSpeech(unittest.TestCase):
    def setUp(self):
        # kokoro が未インストールの環境でもテストできるよう sys.modules にモックを差し込む。
        self._mock_kokoro = MagicMock()
        self._mock_pipeline = MagicMock()
        self._mock_kokoro.KPipeline.return_value = self._mock_pipeline
        self._kokoro_patcher = patch.dict("sys.modules", {"kokoro": self._mock_kokoro})
        self._kokoro_patcher.start()
        # モジュールのキャッシュをクリアして再インポートさせる。
        sys.modules.pop("app.infrastructure.local.text_to_speech", None)

    def tearDown(self):
        self._kokoro_patcher.stop()
        sys.modules.pop("app.infrastructure.local.text_to_speech", None)

    def _make_sut(self, voice: str = "af_heart", lang_code: str = "a"):
        from app.infrastructure.local.text_to_speech import TextToSpeech
        return TextToSpeech(voice=voice, lang_code=lang_code)

    def test_synthesize_returns_float32_array(self):
        """synthesize() は float32 の np.ndarray を返す。"""
        sut = self._make_sut()
        chunk = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        sut._pipeline.return_value = [("", "", chunk)]

        result = sut.synthesize("Hello")

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.dtype, np.float32)

    def test_synthesize_concatenates_multiple_chunks(self):
        """KPipeline が複数チャンクを返す場合、すべて結合される。"""
        sut = self._make_sut()
        chunks = [
            ("", "", np.array([0.1, 0.2], dtype=np.float32)),
            ("", "", np.array([0.3, 0.4], dtype=np.float32)),
        ]
        sut._pipeline.return_value = chunks

        result = sut.synthesize("Hello world")

        np.testing.assert_array_almost_equal(result, [0.1, 0.2, 0.3, 0.4])

    def test_synthesize_passes_text_and_voice_to_pipeline(self):
        """synthesize() はテキストとボイスを KPipeline に渡す。"""
        sut = self._make_sut(voice="am_michael")
        sut._pipeline.return_value = [("", "", np.array([0.0], dtype=np.float32))]

        sut.synthesize("Test text")

        sut._pipeline.assert_called_once_with("Test text", voice="am_michael")

    def test_synthesize_returns_empty_array_when_no_chunks(self):
        """KPipeline がチャンクを返さない場合、空の配列を返す。"""
        sut = self._make_sut()
        sut._pipeline.return_value = []

        result = sut.synthesize("Hello")

        self.assertEqual(len(result), 0)
        self.assertEqual(result.dtype, np.float32)

    def test_synthesize_wraps_exception_as_tts_error(self):
        """KPipeline が例外を送出した場合、TextToSpeechError にラップされる。"""
        from app.application.errors import TextToSpeechError

        sut = self._make_sut()
        sut._pipeline.side_effect = RuntimeError("synthesis failed")

        with self.assertRaises(TextToSpeechError):
            sut.synthesize("Hello")

    def test_import_error_raises_tts_error(self):
        """kokoro が未インストールの場合、インスタンス化時に TextToSpeechError が送出される。"""
        from app.application.errors import TextToSpeechError

        # kokoro モジュールを None に差し替えると ModuleNotFoundError が発生する。
        with patch.dict("sys.modules", {"kokoro": None}):  # type: ignore[dict-item]
            sys.modules.pop("app.infrastructure.local.text_to_speech", None)
            with self.assertRaises(TextToSpeechError):
                from app.infrastructure.local.text_to_speech import TextToSpeech
                TextToSpeech()


if __name__ == "__main__":
    unittest.main()
