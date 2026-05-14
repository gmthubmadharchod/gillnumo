import os

# Telegram Bot
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", "reaction_bot.db")

# UPI Payment
UPI_ID = os.environ.get("UPI_ID", "yourupi@bank")

# Force Channels (comma separated channel usernames)
FORCE_CHANNELS = os.environ.get("FORCE_CHANNELS", "")

# Webhook Settings
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
