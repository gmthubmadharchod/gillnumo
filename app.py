from flask import Flask, request, jsonify
from threading import Thread
import os
import time
import telebot
import bot as bot_module

app = Flask(__name__)

# Get bot instance
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN)

# Update bot in bot.py
bot_module.bot = bot

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": "Auto Reaction Bot Pro v1.0",
        "developer": "@YourUsername"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.json:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

def setup_webhook():
    """Set webhook with retry"""
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    if not webhook_url:
        print("⚠️ WEBHOOK_URL not set! Using polling mode...")
        # Start polling in background
        Thread(target=bot.polling, kwargs={"non_stop": True}, daemon=True).start()
        return
    
    # Remove old webhook
    bot.remove_webhook()
    time.sleep(1)
    
    # Set new webhook with retry
    for attempt in range(3):
        try:
            bot.set_webhook(url=f"{webhook_url}/webhook", max_connections=5)
            print(f"✅ Webhook set to: {webhook_url}/webhook")
            break
        except Exception as e:
            print(f"❌ Webhook attempt {attempt+1} failed: {e}")
            time.sleep(2)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(3)
    
    # Setup webhook
    setup_webhook()
    
    print("🤖 Bot is fully operational!")
    print("="*50)
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
