"""Summarize article text using Claude."""

import logging

import anthropic

from bot.config import ANTHROPIC_API_KEY, SUMMARY_MAX_TOKENS, SUMMARY_MODEL

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """\
You are a concise news summarizer for a team Slack channel. When given article \
text, provide a clear, informative summary that helps busy professionals decide \
if the article is worth reading in full.

Format your response as:
- **TL;DR:** One sentence summary
- **Key points:** 3-5 bullet points covering the most important details
- **Why it matters:** One sentence on relevance or implications

Keep the total summary under 200 words. Be factual and neutral.\
"""


def summarize(article_text: str, url: str) -> str | None:
    """Generate a summary of the article text.

    Returns the summary string, or None on failure.
    """
    # Truncate very long articles to stay within token limits
    max_chars = 20_000
    if len(article_text) > max_chars:
        article_text = article_text[:max_chars] + "\n\n[Article truncated...]"

    try:
        response = client.messages.create(
            model=SUMMARY_MODEL,
            max_tokens=SUMMARY_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this article from {url}:\n\n{article_text}",
                }
            ],
        )
        return response.content[0].text

    except Exception:
        logger.exception("Error summarizing article: %s", url)
        return None
