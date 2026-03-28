def build_interruption_prompt(
    *,
    was_speaking: bool,
    speaking_text: str | None,
) -> str | None:
    """Builds an ephemeral system prompt when the user interrupts Buddy mid-speech.

    Returns None when no interruption occurred so callers can pass it directly
    to ConversationService.prepare_reply without extra checks.
    """
    if not was_speaking:
        return None

    prompt = (
        "The user started speaking while the assistant was speaking. "
        "Treat the user's next message as an interruption that may be a correction or a follow-up question. "
        "Respond naturally."
    )

    if speaking_text:
        # Keep this provider-agnostic and do not commit it to memory.
        # Tell the model to ignore it if irrelevant to avoid topic pollution.
        prompt += (
            "\n\n"
            "The assistant was in the middle of saying: \""
            + speaking_text.strip()
            + "\". "
            "If the user's message seems to respond to or correct that, use it as context; "
            "otherwise ignore it and answer the user's message normally."
        )

    return prompt
