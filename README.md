# my-english-buddy

## Text-only LLM test (OpenAI)

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
uv run python -m app.main "Hello! Please correct my English: I has a pen."

# or omit the prompt to use the built-in sample text
uv run python -m app.main

# system prompt from file
echo "You are an English tutor. Be concise." > prompt.txt
uv run python -m app.main

# override system prompt from the command line
uv run python -m app.main --system "You are an English tutor. Be concise." "Hello!"

# specify env file explicitly
uv run python -m app.main --env-file .env "Hello!"
```

### Notes

- This is a minimal text-only connection check. Audio features will be added later.
- Request timeout is fixed to 60 seconds in the app.