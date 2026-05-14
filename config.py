import os

# Telegram Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Database
DATABASE_URL = "reaction_bot.db"

# UPI Payment
UPI_ID = os.environ.get("UPI_ID", "yourupi@bank")

# Force Channels (comma separated)
FORCE_CHANNELS = os.environ.get("FORCE_CHANNELS", "")

# Webhook URL
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Port
PORT = int(os.environ.get("PORT", "5000"))
