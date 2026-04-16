"""Fetch and extract article text from URLs."""

import logging
import re
from urllib.request import Request, urlopen

import trafilatura

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# URLs that aren't articles worth summarizing
SKIP_PATTERNS = [
    r"^https?://(www\.)?(youtube\.com|youtu\.be)/",
    r"^https?://(www\.)?twitter\.com/",
    r"^https?://(www\.)?x\.com/",
    r"^https?://(.*\.)?slack\.com/",
    r"^https?://(.*\.)?giphy\.com/",
    r"\.(png|jpg|jpeg|gif|mp4|mp3|pdf)(\?.*)?$",
]


def should_skip(url: str) -> bool:
    """Return True if the URL is not an article we should summarize."""
    return any(re.search(p, url, re.IGNORECASE) for p in SKIP_PATTERNS)


def extract_urls(text: str) -> list[str]:
    """Pull URLs out of a Slack message.

    Slack wraps URLs in angle brackets: <https://example.com>
    Sometimes with a label: <https://example.com|example.com>
    """
    # Match Slack-formatted URLs
    slack_urls = re.findall(r"<(https?://[^|>]+)(?:\|[^>]*)?>", text)
    if slack_urls:
        return [u for u in slack_urls if not should_skip(u)]

    # Fallback: bare URLs
    bare_urls = re.findall(r"https?://\S+", text)
    return [u for u in bare_urls if not should_skip(u)]


def fetch_article(url: str) -> str | None:
    """Download and extract the main text content from a URL.

    Returns the article text, or None if extraction fails.
    """
    try:
        # First try trafilatura's built-in fetcher
        downloaded = trafilatura.fetch_url(url)

        # Fallback: fetch with a browser-like User-Agent for sites that block bots
        if not downloaded:
            logger.info("Retrying with browser User-Agent: %s", url)
            try:
                req = Request(url, headers={"User-Agent": USER_AGENT})
                with urlopen(req, timeout=15) as resp:
                    downloaded = resp.read().decode(resp.headers.get_content_charset() or "utf-8")
            except Exception:
                logger.warning("Fallback fetch also failed: %s", url)
                return None

        if not downloaded:
            logger.warning("Failed to download: %s", url)
            return None

        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )

        if not text or len(text.strip()) < 100:
            logger.warning("Extracted text too short from: %s", url)
            return None

        return text.strip()

    except Exception:
        logger.exception("Error fetching article: %s", url)
        return None
