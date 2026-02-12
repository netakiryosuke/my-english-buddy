# My English Buddy

My English Buddy is a desktop application for English conversation practice powered by OpenAI APIs.

It continuously listens to your microphone, transcribes your speech with OpenAI Speech-to-Text, generates conversational replies using OpenAI Chat Completions, and speaks them back using OpenAI Text-to-Speech. The app features a simple GUI window that displays the conversation log.

This project is still **work in progress**. The README is intentionally practical rather than exhaustive.

## Overview

- **Interface**: GUI application (PySide6) with conversation log display
- **Input**: continuous microphone listening with automatic speech detection
- **Wake Word**: say "buddy" to activate the conversation (first time only)
- **Transcription**: OpenAI audio transcription API (hard-coded to `gpt-4o-mini-transcribe`)
- **Reply**: OpenAI Chat Completions API using `OPENAI_MODEL`
- **Speech Output**: OpenAI Text-to-Speech API (hard-coded to `gpt-4o-mini-tts` with `alloy` voice)
- **Memory**: in-memory conversation history (up to 50 messages) persists during the session
- **Interruption**: you can interrupt the assistant's speech by speaking, and it will stop immediately

Current limitations (expected at this stage):

- Memory is not saved between sessions (cleared on restart)
- No persistent storage or conversation history export
- TTS model and voice are not configurable via environment variables

## Requirements

- **Python**: 3.12 (see `.python-version`)
- **OpenAI API key**: with access to the models used (transcription, chat, TTS)
- **Microphone access** and a working audio stack
- **Audio output** (speakers or headphones)
- **uv** (recommended): the repo includes `uv.lock`

## Setup

1) Create your environment file:

```bash
cp .env.example .env
```

2) Edit `.env` and set at least `OPENAI_API_KEY` and `OPENAI_MODEL`.

3) Install dependencies (recommended):

```bash
uv sync
```

4) Run the application:

```bash
uv run python -m app.main
```

The GUI window will open and start listening. Say "buddy" to wake it up, then speak naturally in English. The assistant will reply with voice.

Optional: customize the system prompt (recommended):

```bash
cp prompt.txt.example prompt.txt
# Edit prompt.txt to customize the assistant's behavior
```

If you want to load a different dotenv file:

```bash
uv run python -m app.main --env-file path/to/.env
```

To disable dotenv loading entirely, pass an empty value:

```bash
uv run python -m app.main --env-file ""
```

## How It Works

1. **Listening**: The app continuously listens to your microphone in the background
2. **Wake Word**: Say "buddy" to activate the conversation (required only once per session)
3. **Speech Input**: After waking up, speak naturally; the app detects when you stop speaking
4. **Transcription**: Your speech is transcribed to text using OpenAI Speech-to-Text API
5. **Chat**: The transcribed text is sent to OpenAI Chat Completions API with conversation history
6. **Speech Output**: The assistant's reply is synthesized to speech using OpenAI Text-to-Speech API
7. **Playback**: The speech is played through your speakers/headphones
8. **Interruption**: You can interrupt the assistant by speaking while it's talking

The conversation memory stores up to 50 messages total during the session. When generating replies, it uses the most recent 20 messages as context to keep the conversation focused. Memory is cleared when the app restarts.

## Environment Variables

You can configure the app via environment variables (typically in `.env`).

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key used by the OpenAI SDK. |
| `OPENAI_MODEL` | Yes | - | Chat model for replies (example: `gpt-4o-mini`). |
| `OPENAI_BASE_URL` | No | - | Override API base URL (useful for proxies/compatible endpoints). |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` | No | - | Inline system prompt text. If set, it takes priority over the prompt file. |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` | No | `prompt.txt` | Path to a text file containing the system prompt. Used only if the file exists and is non-empty. |

System prompt resolution order:

1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` (environment variable)
2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (default: `prompt.txt`) if file exists and is non-empty
3) Built-in default prompt in the application

## Configuration

### System Prompt

The system prompt defines the assistant's personality and behavior. You can customize it in three ways (in priority order):

1. **Environment variable**: Set `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` directly
2. **Prompt file**: Create/edit the file specified in `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (default: `prompt.txt`)
3. **Built-in default**: If neither is provided, the app uses a built-in English tutor prompt

Example:

```bash
# Using a custom prompt file
cp prompt.txt.example prompt.txt
# Edit prompt.txt with your preferred instructions

# or use an environment variable
export MY_ENGLISH_BUDDY_SYSTEM_PROMPT="You are a friendly English tutor. Keep replies short."
uv run python -m app.main
```

## Development

### Running Tests

The project includes unit tests for core application logic. To run tests:

```bash
uv sync  # Install test dependencies
uv run pytest
```

Note: Tests do not cover infrastructure/GUI layers to keep them fast and dependency-free.

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
  - `gpt-4o-mini-transcribe` (Speech-to-Text)
  - Your chosen `OPENAI_MODEL` (Chat Completions)
  - `gpt-4o-mini-tts` (Text-to-Speech)
- Verify network connectivity to OpenAI services

### Wake Word Not Working

- Ensure you say "buddy" clearly at the beginning
- Check the GUI log window to see if your speech is being transcribed
- The wake word only needs to be said once per session

## Example: Custom Prompt

```bash
cp prompt.txt.example prompt.txt

# or create your own prompt file
echo "You are an English tutor. Be concise. Correct mistakes gently." > prompt.txt
uv run python -m app.main
```
