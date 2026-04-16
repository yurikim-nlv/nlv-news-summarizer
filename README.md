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

3. Go to **Settings > Basic Information > App-Level Tokens**
4. Click **Generate Token and Scopes**, name it `socket-token`, and add the scope `connections:write`
5. Copy the token (starts with `xapp-`) — this is your `SLACK_APP_TOKEN`

#### Set Bot Permissions

6. Go to **Features > OAuth & Permissions > Scopes > Bot Token Scopes** and add:
   - `channels:history` — read messages in public channels
   - `channels:read` — view basic channel info
   - `chat:write` — post messages
   - `groups:history` — read messages in private channels (optional, if the channel is private)

#### Enable Events

7. Go to **Features > Event Subscriptions** and toggle **Enable Events** on
8. Under **Subscribe to bot events**, add:
   - `message.channels` — listens for messages in public channels
   - `message.groups` — (optional) listens in private channels
   - `app_mention` — responds when @mentioned
9. Click **Save Changes**

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
2. Click **New Project** > **Deploy from GitHub Repo**
3. Connect your GitHub account and select this repository
4. Railway will auto-detect the Dockerfile and deploy

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
| `SUMMARY_MODEL` | No | `claude-sonnet-4-20250514` | Claude model to use for summaries |
| `SUMMARY_MAX_TOKENS` | No | `1024` | Max tokens for summary response |

## Project Structure

```
├── bot/
│   ├── __init__.py
│   ├── app.py           # Slack event handlers and bot startup
│   ├── article.py       # URL extraction and article text fetching
│   ├── config.py        # Environment variable loading
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

## Troubleshooting

**Bot doesn't respond to links:**
- Make sure the bot is invited to the channel (`/invite @News Summarizer`)
- Check that `message.channels` is enabled under Event Subscriptions
- Look at the Railway logs for errors

**"Could not extract article" in logs:**
- Some sites block automated requests or are heavily JavaScript-rendered
- Paywalled articles may not return useful text
- This is expected for a subset of links — the bot silently skips them

**Bot responds to its own messages (loop):**
- This shouldn't happen — the bot filters out messages with `bot_id`. If it does, check that the Slack app has a proper bot user configured.
