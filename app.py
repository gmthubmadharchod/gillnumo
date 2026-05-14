from flask import Flask, request, jsonify
from threading import Thread
import bot as telegram_bot
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "bot": "Auto Reaction Bot"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.json:
        telegram_bot.bot.process_new_updates(
            [telegram_bot.types.Update.de_json(request.json)]
        )
        return 'OK', 200
    return 'BAD REQUEST', 400

def run_bot():
    telegram_bot.bot.remove_webhook()
    time.sleep(1)
    telegram_bot.bot.set_webhook(url=os.environ.get("WEBHOOK_URL", "") + "/webhook")

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    import time
    Thread(target=run_flask).start()
    time.sleep(2)
    run_bot()
