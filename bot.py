import telebot
import os
import sys
from config import BOT_TOKEN, OWNER_ID, UPI_ID
from database import init_db, get_db, is_admin, is_premium
from telebot import types
import time
from datetime import datetime, timedelta
import threading

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

bot = telebot.TeleBot(BOT_TOKEN)

# Auto-reaction tracking
auto_react = {}

# =============== COMMANDS ===============

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⭐ Premium", callback_data="premium"))
    markup.add(types.InlineKeyboardButton("📋 Plans", callback_data="plans"))
    markup.add(types.InlineKeyboardButton("ℹ️ Help", callback_data="help"))
    
    bot.reply_to(message, f"🤖 Welcome {message.from_user.first_name}!\n\n"
                 "I'm Auto Reaction Bot\n"
                 "• Auto react on channel posts\n"
                 "• Multiple emoji reactions\n"
                 "• Works without admin in public channels\n\n"
                 "👇 Choose option:", reply_markup=markup)

# =============== OWNER COMMANDS ===============

@bot.message_handler(commands=['admin'])
def owner_panel(message):
    if message.from_user.id != OWNER_ID and not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Owner only command!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Admin", callback_data="add_admin"),
        types.InlineKeyboardButton("➖ Remove Admin", callback_data="remove_admin"),
        types.InlineKeyboardButton("📊 View Plans", callback_data="view_plans"),
        types.InlineKeyboardButton("➕ Add Plan", callback_data="add_plan"),
        types.InlineKeyboardButton("🗑 Delete Plan", callback_data="delete_plan"),
        types.InlineKeyboardButton("📢 Force Channels", callback_data="force_channels"),
        types.InlineKeyboardButton("💳 UPI Settings", callback_data="upi_settings"),
        types.InlineKeyboardButton("📨 Broadcast", callback_data="broadcast"),
        types.InlineKeyboardButton("👥 Admins List", callback_data="admin_list")
    )
    bot.send_message(message.chat.id, "👑 Owner Panel:", reply_markup=markup)

@bot.message_handler(commands=['setreaction'])
def set_reaction(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "❌ Premium feature! Buy premium first.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: `/setreaction <channel_id> <emojis>`\nExample: `/setreaction -1001234567890 👍❤️😍`")
        return
    
    channel_id = int(args[1])
    emojis = args[2]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO reactions (user_id, channel_id, emojis) VALUES (?,?,?)",
                   (user_id, channel_id, emojis))
    conn.commit()
    conn.close()
    
    if channel_id not in auto_react:
        auto_react[channel_id] = {}
    auto_react[channel_id][user_id] = list(emojis)
    
    bot.reply_to(message, f"✅ Auto reaction set for channel `{channel_id}` with: {emojis}")

@bot.message_handler(commands=['react'])
def react_post(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "❌ Premium feature!")
        return
    
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "Usage: `/react <post_link> <emojis>`\nExample: `/react https://t.me/channel/123 👍❤️`")
        return
    
    post_link = args[1]
    emojis = list(args[2])
    
    try:
        parts = post_link.replace("https://t.me/", "").split("/")
        channel_username = parts[0]
        message_id = int(parts[1])
        
        for emoji in emojis:
            bot.send_reaction(chat_id=f"@{channel_username}", message_id=message_id, emoji=emoji)
        
        bot.reply_to(message, f"✅ Reacted with: {args[2]}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# =============== CALLBACK HANDLERS ===============

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "premium":
        premium_menu(call.message)
    elif call.data == "plans":
        show_plans(call.message)
    elif call.data == "help":
        show_help(call.message)
    elif call.data == "add_admin":
        msg = bot.send_message(call.message.chat.id, "Send user ID to add as admin:")
        bot.register_next_step_handler(msg, process_add_admin)
    elif call.data == "admin_list":
        show_admins(call.message)
    elif call.data == "view_plans":
        show_all_plans(call.message)
    elif call.data == "add_plan":
        msg = bot.send_message(call.message.chat.id, "Send: name|days|price|features\nExample: Pro|30|99|Unlimited")
        bot.register_next_step_handler(msg, process_add_plan)
    elif call.data == "delete_plan":
        msg = bot.send_message(call.message.chat.id, "Send plan ID to delete:")
        bot.register_next_step_handler(msg, process_delete_plan)
    elif call.data == "upi_settings":
        msg = bot.send_message(call.message.chat.id, f"Current UPI: {UPI_ID}\nSend new UPI ID:")
        bot.register_next_step_handler(msg, process_upi_update)
    elif call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "Send message to broadcast:")
        bot.register_next_step_handler(msg, process_broadcast)
    elif call.data == "force_channels":
        show_force_channels(call.message)
    elif call.data == "add_force_channel":
        msg = bot.send_message(call.message.chat.id, "Send channel username (with @):")
        bot.register_next_step_handler(msg, process_add_force_channel)
    elif call.data.startswith("buy_"):
        plan_id = int(call.data.split("_")[1])
        handle_buy_plan(call.message, plan_id)

# =============== FUNCTIONS ===============

def premium_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 View Plans", callback_data="plans"))
    markup.add(types.InlineKeyboardButton("💳 Payment Info", callback_data="payment_info"))
    
    bot.send_message(message.chat.id, "⭐ Premium Features:\n"
                    "• Auto react on multiple channels\n"
                    "• Custom emoji reactions\n"
                    "• Post link reactions\n"
                    "• Priority support\n\n"
                    "Get premium now!",
                    reply_markup=markup)

def show_plans(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans")
    plans = cursor.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    for plan in plans:
        markup.add(types.InlineKeyboardButton(
            f"💎 {plan['name']} - ₹{plan['price']}/ {plan['days']} days",
            callback_data=f"buy_{plan['id']}"
        ))
    
    bot.send_message(message.chat.id, "📋 Available Plans:", reply_markup=markup)

def show_help(message):
    help_text = """
🤖 **Bot Commands:**

👤 **User Commands:**
/start - Start bot
/plans - View plans
/premium - Premium info

⚡ **Premium/Admin Commands:**
/setreaction channel_id emojis - Auto react
/react post_link emojis - React on post
/status - Check subscription

👑 **Owner Commands:**
/admin - Owner panel
/broadcast - Broadcast message
"""
    bot.send_message(message.chat.id, help_text)

def process_add_admin(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only owner can add admins!")
        return
    try:
        admin_id = int(message.text)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id, added_by, added_date) VALUES (?,?,?)",
                      (admin_id, OWNER_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ User {admin_id} is now admin!")
    except:
        bot.reply_to(message, "❌ Invalid user ID!")

def handle_buy_plan(message, plan_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
    plan = cursor.fetchone()
    conn.close()
    
    if not plan:
        bot.send_message(message.chat.id, "Plan not found!")
        return
    
    payment_text = f"""
💳 **Payment for {plan['name']} Plan**

💰 Amount: ₹{plan['price']}
📅 Duration: {plan['days']} days

**UPI ID:** `{UPI_ID}`

⚠️ Send screenshot to @{bot.get_me().username} after payment!

After payment use: /verify_payment {plan_id} <screenshot>
"""
    bot.send_message(message.chat.id, payment_text)

# =============== AUTO REACTION SYSTEM ===============

@bot.channel_post_handler(func=lambda message: True)
def auto_react_handler(message):
    channel_id = message.chat.id
    
    if channel_id in auto_react:
        for user_id, emojis in auto_react[channel_id].items():
            try:
                for emoji in emojis:
                    bot.set_message_reaction(message.chat.id, message.message_id, 
                                            [types.ReactionTypeEmoji(emoji)])
            except Exception as e:
                print(f"Reaction error: {e}")

# =============== MAIN ===============

def main():
    print("🤖 Bot starting...")
    init_db()
    
    # Load existing reactions
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reactions")
    reactions = cursor.fetchall()
    conn.close()
    
    for reaction in reactions:
        channel_id = reaction['channel_id']
        if channel_id not in auto_react:
            auto_react[channel_id] = {}
        auto_react[channel_id][reaction['user_id']] = list(reaction['emojis'])
    
    print("✅ Bot started!")
    bot.infinity_polling()

if __name__ == "__main__":
    main()
