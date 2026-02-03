# my-english-buddy

## Audio-based OpenAI chat application

### Environment variables

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (required)
- `OPENAI_BASE_URL` (optional)

Optional system prompt configuration:

- `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` (optional)
- `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` (optional, default: `prompt.txt`)

You can put these in a `.env` file (recommended). See `.env.example`.

### Run

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY

# Run with audio input (records from your microphone)
uv run python -m app.main

# System prompt from file
echo "You are an English tutor. Be concise." > prompt.txt
uv run python -m app.main

# Override system prompt from the command line
uv run python -m app.main --system "You are an English tutor. Be concise."

# Specify env file explicitly
uv run python -m app.main --env-file .env
```

### Notes

- The application records audio from your microphone and transcribes it using OpenAI's Whisper API.
- Request timeout is fixed to 60 seconds in the app.