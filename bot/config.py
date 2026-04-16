import os

from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "claude-sonnet-4-6")
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "1024"))
