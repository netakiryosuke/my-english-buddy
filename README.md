🗾Japanese: [日本語版](README.ja.md)

# My English Buddy

My English Buddy is a desktop application for English conversation practice powered by OpenAI APIs.

It continuously listens to your microphone, transcribes your speech, generates replies, and speaks them back. A simple GUI window shows the conversation log.

## Quickstart

### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY and OPENAI_MODEL

uv sync
Copy-Item prompt.txt.example prompt.txt  # optional (custom system prompt)

uv run python -m app.main
```

### macOS/Linux/WSL

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY and OPENAI_MODEL

uv sync
cp prompt.txt.example prompt.txt  # optional (custom system prompt)

uv run python -m app.main
```

Say “buddy” to wake it up, then speak in English.

Optional:
- Use a different dotenv file: `uv run python -m app.main --env-file path/to/.env`
- Disable dotenv loading: `uv run python -m app.main --env-file ""`

## Behavior

- **Wake word**: say “buddy” to start. After ~3 minutes of inactivity, it goes back to sleep and you’ll need to say “buddy” again.
- **Interruption**: speaking while the assistant talks stops playback immediately.
- **Memory**: in-memory only (up to 50 messages; uses the latest 20 as context). Not saved between app restarts.
- **Logs**: saved on app exit to `logs/YYYY-MM-DD_HH-MM-SS.txt`.

## Environment Variables

You can configure the app via environment variables (typically in `.env`).

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key used by the OpenAI SDK. |
| `OPENAI_MODEL` | Yes | - | Chat model for replies (example: `gpt-4o-mini`). |
| `OPENAI_BASE_URL` | No | - | Override API base URL (useful for proxies/compatible endpoints). |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` | No | - | Inline system prompt text. If set, it takes priority over the prompt file. |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` | No | `prompt.txt` | Path to a text file containing the system prompt. Used only if the file exists and is non-empty. |
| `MY_ENGLISH_BUDDY_STT_PROVIDER` | No | `openai` | Speech-to-Text provider: `openai` (default) or `local` (faster-whisper). |
| `MY_ENGLISH_BUDDY_LOCAL_STT_MODEL` | No | `distil-large-v3` | Model name for local STT (e.g., `distil-large-v3`, `large-v3`, `medium`). Only used when `MY_ENGLISH_BUDDY_STT_PROVIDER=local`. |
| `MY_ENGLISH_BUDDY_TTS_PROVIDER` | No | `openai` | Text-to-Speech provider: `openai` (default) or `local` (Kokoro). |
| `MY_ENGLISH_BUDDY_TTS_VOICE` | No | *(provider default)* | Voice name. OpenAI default: `alloy`. Kokoro default: `af_heart`. |
| `MY_ENGLISH_BUDDY_TTS_LANG_CODE` | No | `a` | Kokoro language code. `a`=American English, `j`=Japanese, `b`=British English. Only used when `MY_ENGLISH_BUDDY_TTS_PROVIDER=local`. |

System prompt resolution order:

1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` (environment variable)
2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (default: `prompt.txt`) if file exists and is non-empty
3) Built-in default prompt in the application

## Optional: Local Speech-to-Text

You can switch from OpenAI STT to local offline transcription (faster-whisper):

Example:

```bash
uv sync --extra local-stt

# Enable local STT (add these to your .env)
MY_ENGLISH_BUDDY_STT_PROVIDER=local
# Optional
MY_ENGLISH_BUDDY_LOCAL_STT_MODEL=distil-large-v3
```

Notes:
- GPU acceleration is optional; the app falls back to CPU if CUDA libraries are missing.
- `OPENAI_API_KEY` is still required for chat.

## Optional: Local Text-to-Speech

You can switch from OpenAI TTS to Kokoro, a high-quality local TTS engine (no API calls, no running cost):

```bash
uv sync --extra local-tts

# Enable local TTS (add these to your .env)
MY_ENGLISH_BUDDY_TTS_PROVIDER=local
# Optional: voice and language
MY_ENGLISH_BUDDY_TTS_VOICE=af_heart
MY_ENGLISH_BUDDY_TTS_LANG_CODE=a
```

Notes:
- GPU (CUDA) is recommended for low latency; CPU-only works but is slower.
- On first run the Kokoro model (~300 MB) is downloaded automatically from Hugging Face.
- On Linux, the CUDA 12.4 PyTorch wheel is used automatically. On macOS or CPU-only Linux, the CPU wheel from PyPI is used instead.
- `OPENAI_API_KEY` is still required for chat.

## Development

### Running Tests

The project includes unit tests. To run tests:

```bash
# Install test dependencies
uv sync --extra test

# Run tests
uv run pytest
```

## Troubleshooting

- **Wake word not working**: Say "buddy" clearly. If the app went to sleep due to inactivity, say "buddy" again.
- **Too sensitive / not detecting speech**: Use the menu `Tools` → `ノイズキャリブレーション` and try again.
- **No voice / interrupted too easily**: Try speaking after the assistant finishes; speaking while it talks stops playback.
- **Local STT**: Install with `uv sync --extra local-stt`.
- **Local TTS**: Install with `uv sync --extra local-tts`.
- **Logs**: On exit, a log file is saved to `logs/` (use it when reporting issues).
