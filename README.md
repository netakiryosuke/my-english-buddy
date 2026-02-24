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
Copy-Item prompt.txt.example prompt.txt  # optional (custom system prompt; gitignored)

uv run python -m app.main
```

### macOS/Linux/WSL

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY and OPENAI_MODEL

uv sync
cp prompt.txt.example prompt.txt  # optional (custom system prompt; gitignored)

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
| `OPENAI_API_KEY` | Yes | - | OpenAI API key used by the OpenAI SDK. (Currently required even when using local STT.) |
| `OPENAI_MODEL` | Yes | - | Chat model for replies (example: `gpt-4o-mini`). |
| `OPENAI_BASE_URL` | No | - | Override API base URL (useful for proxies/compatible endpoints). |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` | No | - | Inline system prompt text. If set, it takes priority over the prompt file. |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` | No | `prompt.txt` | Path to a text file containing the system prompt. Used only if the file exists and is non-empty. |
| `MY_ENGLISH_BUDDY_STT_PROVIDER` | No | `openai` | Speech-to-Text provider: `openai` (default) or `local` (faster-whisper). |
| `MY_ENGLISH_BUDDY_LOCAL_STT_MODEL` | No | `distil-large-v3` | Model name for local STT (e.g., `distil-large-v3`, `large-v3`, `medium`). Only used when `MY_ENGLISH_BUDDY_STT_PROVIDER=local`. |

System prompt resolution order:

1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` (environment variable)
2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (default: `prompt.txt`) if file exists and is non-empty
3) Built-in default prompt in the application

## Optional: Local Speech-to-Text

You can switch from OpenAI STT to local offline transcription (faster-whisper):

Example:

```bash
uv sync --extra local-stt
```

Notes:
- GPU acceleration is optional; the app falls back to CPU if CUDA libraries are missing.
- `OPENAI_API_KEY` is still required for chat and TTS.

## Development

### Running Tests

The project includes unit tests for core application logic. To run tests:

```bash
# Install test dependencies
uv sync --extra test

# Run tests
uv run pytest
```

Note: Test coverage is currently limited to core application logic. Infrastructure and GUI layer tests are planned for future development.

## Troubleshooting

### Microphone Not Working

- **macOS/Linux**: Ensure the terminal or Python has microphone permissions in System Preferences/Settings
- **All platforms**: Check that your microphone is properly connected and set as the default input device
- Run a simple audio test to verify your microphone works outside this app

### No Sound Output

- Verify your speakers/headphones are connected and working
- Check system volume settings
- Ensure OpenAI TTS API is accessible (check API key and network connection)

### OpenAI API Errors

- Verify `OPENAI_API_KEY` is set correctly in `.env`
- Check that your API key has access to the required models:
  - `gpt-4o-mini-transcribe` (Speech-to-Text, only if using OpenAI STT)
  - Your chosen `OPENAI_MODEL` (Chat Completions)
  - `gpt-4o-mini-tts` (Text-to-Speech)
- Verify network connectivity to OpenAI services
- If using local STT, only chat and TTS models need OpenAI access

### Local STT Issues

- **Installation errors**: Ensure you ran `uv sync --extra local-stt`
- **GPU not detected**: Install CUDA 12 + cuDNN, or the app will fall back to CPU (slower)
- **Model download fails**: Check internet connection (models are downloaded from Hugging Face on first use)
- **Slow transcription**: GPU acceleration is recommended; CPU-only mode is significantly slower

### Wake Word Not Working

- Ensure you say "buddy" clearly at the beginning
- Check the GUI log window to see if your speech is being transcribed
- If the app went to sleep due to inactivity, say "buddy" again
