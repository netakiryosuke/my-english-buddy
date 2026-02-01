# my-english-buddy

## Text-only LLM test (OpenAI)

### Environment variables

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` (optional)
- `OPENAI_TIMEOUT_SECONDS` (optional, default: `60`)

### Run

```bash
export OPENAI_API_KEY="..."
uv run python -m app.main "Hello! Please correct my English: I has a pen."

# or (also supported)
uv run python app/main.py "Hello!"
```

### Notes

- This is a minimal text-only connection check. Audio features will be added later.