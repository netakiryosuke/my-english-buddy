# My English Buddy

My English Buddy is a small CLI prototype for English practice.

It records audio from your microphone, auto-stops after you finish speaking, transcribes your speech with OpenAI Speech-to-Text, sends the text to an OpenAI chat model (with a tutor-style system prompt), and prints the reply.

This project is still **work in progress**. The README is intentionally practical rather than exhaustive.

## Overview

- **Input**: microphone audio (automatic speech detection)
- **Transcription**: OpenAI audio transcription API (currently hard-coded to `gpt-4o-mini-transcribe` in the code)
- **Reply**: OpenAI Chat Completions API using `OPENAI_MODEL`
- **Memory**: short in-memory message history during a single process run (cleared on restart)

Current limitations (expected at this stage):

- Single-turn interaction per run (record → transcribe → reply → exit)
- No text-to-speech output
- No persistent memory storage

## Requirements

- **Python**: 3.12 (see `.python-version`)
- **OpenAI**: an API key with access to the models you choose
- **Microphone access** and a working audio stack
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

4) Run:

```bash
uv run python -m app.main
```

If you want to load a different dotenv file:

```bash
uv run python -m app.main --env-file path/to/.env
```

To disable dotenv loading entirely, pass an empty value:

```bash
uv run python -m app.main --env-file ""
```

## Environment variables

You can configure the app via environment variables (typically in `.env`).

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key used by the OpenAI SDK. |
| `OPENAI_MODEL` | Yes | - | Chat model for replies (example: `gpt-4o-mini`). |
| `OPENAI_BASE_URL` | No | - | Override API base URL (useful for proxies/compatible endpoints). |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` | No | - | Inline system prompt text. If set, it takes priority over the prompt file. |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` | No | `prompt.txt` | Path to a text file containing the system prompt. Used only if the file exists and is non-empty. |

System prompt resolution order:

1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT`
2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (default: `prompt.txt`)
3) Built-in default prompt in the application

## Example: custom prompt

```bash
echo "You are an English tutor. Be concise. Correct mistakes gently." > prompt.txt
uv run python -m app.main
```
