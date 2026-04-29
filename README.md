# News Summarizer Slack Bot

A Slack bot that monitors a channel for posted links, fetches the article content, and replies in-thread with an AI-generated summary using Claude.

## How it works

1. Someone posts a link in your Slack channel (e.g. `#news-you-can-use`)
2. The bot detects the URL, fetches the article, and extracts the text
3. Claude summarizes the article into a TL;DR, key points, and a "why it matters" line
4. The bot replies in-thread so the channel stays clean

The bot uses **Socket Mode**, which means it connects outbound to Slack via WebSocket — no public URL or ingress needed. This makes deployment simple on any platform.

## Prerequisites

- Python 3.11+
- A Slack workspace where you can create apps
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** > **From scratch**
2. Name it something like `News Summarizer` and select your workspace

#### Enable Socket Mode

3. Go to **Settings > Socket Mode** (left sidebar) and toggle **Enable Socket Mode** on
4. Go to **Settings > Basic Information > App-Level Tokens**
5. Click **Generate Token and Scopes**, name it `socket-token`, and add the scope `connections:write`
6. Copy the token (starts with `xapp-`) — this is your `SLACK_APP_TOKEN`

#### Set Bot Permissions

7. Go to **Features > OAuth & Permissions > Scopes > Bot Token Scopes** and add:
   - `channels:history` — read messages in public channels
   - `channels:read` — view basic channel info
   - `chat:write` — post messages
   - `groups:history` — read messages in private channels (optional, if the channel is private)

#### Enable Events

> **Important:** Socket Mode must be enabled (step 3) *before* this step, otherwise Slack will require a Request URL and won't let you save.

8. Go to **Features > Event Subscriptions** and toggle **Enable Events** on
9. Under **Subscribe to bot events**, add:
   - `message.channels` — listens for messages in public channels
   - `message.groups` — (optional) listens in private channels
   - `app_mention` — responds when @mentioned
10. Click **Save Changes**

#### Install the App

10. Go to **Settings > Install App** and click **Install to Workspace**
11. Copy the **Bot User OAuth Token** (starts with `xoxb-`) — this is your `SLACK_BOT_TOKEN`

#### Invite the Bot to Your Channel

12. In Slack, go to `#news-you-can-use` (or whichever channel) and type:
    ```
    /invite @News Summarizer
    ```

### 2. Configure Environment Variables

Copy the example env file and fill in your tokens:

```bash
cp .env.example .env
```

Edit `.env`:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-level-token
ANTHROPIC_API_KEY=sk-ant-your-api-key
```

### 3. Run Locally

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Start the bot
python -m bot.app
```

You should see `Starting News Summarizer Bot...` in the console. Post a news link in your channel to test it.

## Deploying to Railway

[Railway](https://railway.app) is the easiest way to keep this bot running 24/7. The free tier includes $5/month in credits, which is more than enough for this bot.

### First-time setup

1. Create an account at [railway.app](https://railway.app)
2. Install the [Railway GitHub App](https://github.com/apps/railway-app) on your GitHub account — grant it access to this repository (or all repositories)
3. Back in Railway, click **New Project** > **Deploy from GitHub Repo**
4. Select this repository — Railway will auto-detect the Dockerfile and deploy

### Set environment variables

5. In your Railway project, go to **Variables** and add:
   - `SLACK_BOT_TOKEN` = your `xoxb-...` token
   - `SLACK_APP_TOKEN` = your `xapp-...` token
   - `ANTHROPIC_API_KEY` = your `sk-ant-...` key
6. Railway will automatically redeploy with the new variables

### That's it

Railway auto-deploys on every push to `main`. Check the **Logs** tab to confirm the bot started successfully.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | Yes | — | Bot user OAuth token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Yes | — | App-level token (`xapp-...`) |
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key |
| `SUMMARY_MODEL` | No | `claude-sonnet-4-6` | Claude model to use for summaries |
| `SUMMARY_MAX_TOKENS` | No | `1024` | Max tokens for summary response |

## Project Structure

```
├── bot/
│   ├── __init__.py
│   ├── app.py           # Slack event handlers and bot startup
│   ├── article.py       # URL extraction and article text fetching
│   ├── config.py        # Environment variable loading
│   ├── gdrive.py        # Google Drive / Docs file fetching and extraction
│   └── summarizer.py    # Claude-powered article summarization
├── .env.example         # Template for environment variables
├── Dockerfile           # Container build for deployment
├── railway.json         # Railway deployment config
├── pyproject.toml       # Python project metadata and dependencies
└── README.md
```

## Supported Link Types

The bot will attempt to summarize any HTTP/HTTPS link that looks like a news article. It automatically skips:

- YouTube / video links
- Twitter/X posts
- Image files (png, jpg, gif)
- Slack internal links
- Giphy links

### Google Drive support

The bot has special handling for Google Drive and Google Docs links. Supported formats:

| Link type | Example | Notes |
|-----------|---------|-------|
| Google Docs | `docs.google.com/document/d/...` | Exported as plain text |
| Google Slides | `docs.google.com/presentation/d/...` | Exported as plain text |
| PDF on Drive | `drive.google.com/file/d/...` | Text extracted with pypdf |
| Word doc on Drive | `drive.google.com/file/d/...` | Text extracted with python-docx |

> **Requirement:** The file must be shared as **"Anyone with the link can view"**. Private files will return an error. Authentication is not supported.

## Troubleshooting

**Bot doesn't respond to links:**
- Make sure the bot is invited to the channel (`/invite @News Summarizer`)
- Check that `message.channels` is enabled under Event Subscriptions
- Look at the Railway logs for errors

**"Couldn't summarize this link" reply in Slack:**
- Some sites block automated requests. The bot will reply in-thread explaining whether the fetch or summarization step failed.
- If a site consistently blocks requests, the article fetcher in `bot/article.py` may need tweaking (see below).

**Bot responds to its own messages (loop):**
- This shouldn't happen — the bot filters out messages with `bot_id`. If it does, check that the Slack app has a proper bot user configured.

## Article Fetching — What We've Tweaked

Not every site makes it easy to grab article text. The fetcher (`bot/article.py`) has been iteratively improved to handle real-world sites. Here's what's in place and why:

| Layer | What it does | Why it was added |
|-------|-------------|-----------------|
| **trafilatura (default)** | Downloads and extracts article text using its built-in fetcher | Works out of the box for most sites |
| **Browser-like headers (fallback)** | Retries with a full set of headers (`User-Agent`, `Sec-Fetch-*`, `Accept`, etc.) mimicking a real Chrome browser | Added after sites like motor1.com returned 403 errors — they check for bot-like request headers |
| **Skip patterns** | Ignores URLs that aren't articles (YouTube, Twitter/X, images, Slack links, Giphy) | Prevents unnecessary fetch attempts on non-article content |

### Known limitation: paywalled sites on cloud hosting

Some major news sites (NYTimes, Washington Post, etc.) block requests from cloud server IP addresses. Articles from these sites will work when running the bot locally (residential IP) but **fail when deployed to Railway or similar platforms**.

To fix this, you'd need to route requests through a residential proxy service such as [ScraperAPI](https://www.scraperapi.com/), [Bright Data](https://brightdata.com/), or [ScrapingBee](https://www.scrapingbee.com/). These add a small per-request cost but make cloud-hosted fetching indistinguishable from a normal browser.

### If a new site isn't working

1. Run the bot locally and check the logs — they'll show whether the download failed (403/timeout) or the extraction returned too little text
2. Common fixes:
   - **403 errors**: The site may need additional headers or cookie handling. Update `BROWSER_HEADERS` in `bot/article.py`
   - **Empty extraction**: trafilatura's parser may not understand the site's HTML structure. Try adjusting the `trafilatura.extract()` options (e.g., `favor_recall=True` instead of `favor_precision=True`)
   - **JavaScript-rendered sites**: Sites that load content via JavaScript won't work with any HTTP-based fetcher. These would require a headless browser (e.g., Playwright), which is a heavier dependency

## Changelog

### Google Drive & Docs support
**What changed:** Added `bot/gdrive.py`, a dedicated module for handling Google Drive and Google Docs links. Updated `bot/app.py` to route Drive URLs through this new fetcher instead of the standard article fetcher. Added `pypdf` and `python-docx` as dependencies.

**Why:** The standard article fetcher failed on Drive links because `drive.google.com` serves a JavaScript-rendered file preview page, not readable HTML. Even with browser-like headers, there's no article text to extract. Drive files need to be downloaded directly and parsed based on their file type.

**How it works:**
- Google Docs/Slides links are exported directly as plain text via Google's own export API (no scraping needed)
- `drive.google.com/file/d/...` links are downloaded as raw bytes, then the file type is detected from the first few bytes (magic bytes) rather than guessing from the URL
- PDFs are parsed with `pypdf`, Word docs with `python-docx`
- If the file isn't publicly shared, the bot replies with a clear error explaining the sharing requirement
