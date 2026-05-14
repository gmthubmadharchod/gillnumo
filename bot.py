import telebot
import os
from telebot import types
from database import init_db, get_db, is_admin, is_premium
from bot_handlers import *

# Bot instance
bot = None
auto_react = {}

def register_handlers():
    global bot
    if bot is None:
        return
    
    @bot.message_handler(commands=['start'])
    def start_handler(message):
        cmd_start(bot, message)
    
    @bot.message_handler(commands=['plans'])
    def plans_handler(message):
        show_plans_menu(bot, message)
    
    @bot.message_handler(commands=['status'])
    def status_handler(message):
        cmd_status(bot, message)
    
    @bot.message_handler(commands=['setreaction'])
    def setreaction_handler(message):
        cmd_setreaction(bot, message)
    
    @bot.message_handler(commands=['react'])
    def react_handler(message):
        cmd_react(bot, message)
    
    @bot.message_handler(commands=['admin', 'panel'])
    def admin_handler(message):
        show_admin_panel(bot, message)
    
    @bot.message_handler(commands=['broadcast'])
    def broadcast_handler(message):
        if is_admin(message.from_user.id):
            process_broadcast(bot, message)
    
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        callback_router(call)
    
    @bot.channel_post_handler(func=lambda message: True)
    def channel_handler(message):
        channel_id = message.chat.id
        if channel_id in auto_react:
            for user_id, emojis in auto_react[channel_id].items():
                try:
                    reaction_list = [types.ReactionTypeEmoji(e) for e in emojis]
                    bot.set_message_reaction(channel_id, message.message_id, 
                                            reaction_list, is_big=True)
                except:
                    pass

def callback_router(call):
    data = call.data
    msg = call.message
    
    if data == "premium":
        bot.send_message(msg.chat.id, "⭐ Premium features:\n• Auto reactions\n• Multiple emojis\n• Post links\n\nUse /plans to buy!")
    elif data == "plans":
        show_plans_menu(bot, msg)
    elif data == "help":
        bot.send_message(msg.chat.id, "📝 Commands:\n/start\n/plans\n/status\n/setreaction\n/react\n/admin")
    elif data == "status":
        cmd_status(bot, msg)
    elif data == "admin_panel":
        show_admin_panel(bot, msg)
    elif data == "add_admin":
        m = bot.send_message(msg.chat.id, "Send user ID:")
        bot.register_next_step_handler(m, lambda x: process_add_admin(bot, x))
    elif data == "remove_admin":
        m = bot.send_message(msg.chat.id, "Send user ID to remove:")
        bot.register_next_step_handler(m, lambda x: remove_admin(bot, x))
    elif data == "add_plan":
        m = bot.send_message(msg.chat.id, "Format: name|days|price|features")
        bot.register_next_step_handler(m, lambda x: process_add_plan(bot, x))
    elif data == "delete_plan":
        m = bot.send_message(msg.chat.id, "Send plan ID:")
        bot.register_next_step_handler(m, lambda x: delete_plan(bot, x))
    elif data == "modify_plan":
        m = bot.send_message(msg.chat.id, "Send: plan_id|name|days|price|features")
        bot.register_next_step_handler(m, lambda x: modify_plan(bot, x))
    elif data == "upi_settings":
        m = bot.send_message(msg.chat.id, f"Current: {os.environ.get('UPI_ID')}\nSend new UPI:")
        bot.register_next_step_handler(m, lambda x: update_upi(bot, x))
    elif data == "force_channels":
        show_force_channels(bot, msg)
    elif data == "add_force_channel":
        m = bot.send_message(msg.chat.id, "Send @username:")
        bot.register_next_step_handler(m, lambda x: add_force_ch(bot, x))
    elif data == "broadcast_menu":
        m = bot.send_message(msg.chat.id, "Send message:")
        bot.register_next_step_handler(m, lambda x: process_broadcast(bot, x))
    elif data == "verify_payment":
        m = bot.send_message(msg.chat.id, "Send screenshot with caption: user_id|plan_id")
        bot.register_next_step_handler(m, lambda x: process_verify_payment(bot, x))
    elif data == "payment_info":
        bot.send_message(msg.chat.id, f"💳 UPI: `{os.environ.get('UPI_ID')}`", parse_mode="Markdown")
    elif data.startswith("buy_"):
        plan_id = int(data.split("_")[1])
        handle_buy_plan(bot, msg, plan_id)
    
    bot.answer_callback_query(call.id)

# Helper functions
def remove_admin(bot, message):
    try:
        uid = int(message.text)
        conn = get_db()
        conn.cursor().execute("DELETE FROM admins WHERE user_id=?", (uid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Removed: {uid}")
    except:
        bot.send_message(message.chat.id, "❌ Error!")

def delete_plan(bot, message):
    try:
        pid = int(message.text)
        conn = get_db()
        conn.cursor().execute("DELETE FROM plans WHERE id=?", (pid,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Deleted plan {pid}")
    except:
        bot.send_message(message.chat.id, "❌ Error!")

def modify_plan(bot, message):
    try:
        p = message.text.split("|")
        pid, name, days, price = int(p[0]), p[1], int(p[2]), float(p[3])
        features = p[4] if len(p) > 4 else ""
        conn = get_db()
        conn.cursor().execute("UPDATE plans SET name=?,days=?,price=?,features=? WHERE id=?",
                            (name, days, price, features, pid))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Modified!")
    except:
        bot.send_message(message.chat.id, "❌ Error!")

def update_upi(bot, message):
    os.environ["UPI_ID"] = message.text.strip()
    bot.send_message(message.chat.id, f"✅ UPI updated!")

def add_force_ch(bot, message):
    try:
        username = message.text.strip()
        chat = bot.get_chat(username)
        conn = get_db()
        conn.cursor().execute("INSERT OR IGNORE INTO force_channels VALUES (?,?,?)",
                            (username, chat.id, message.from_user.id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Added: {chat.title}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid channel!")

def show_force_channels(bot, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM force_channels")
    channels = cursor.fetchall()
    conn.close()
    
    text = "📢 **Force Channels:**\n" + "\n".join([f"• {c['channel_username']}" for c in channels]) if channels else "No channels."
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Add", callback_data="add_force_channel"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

def init_bot():
    global bot
    if bot is None:
        bot = telebot.TeleBot(os.environ.get("BOT_TOKEN", ""))
    
    init_db()
    
    # Load saved reactions
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reactions")
    for r in cursor.fetchall():
        channel_id = r['channel_id']
        if channel_id not in auto_react:
            auto_react[channel_id] = {}
        auto_react[channel_id][r['user_id']] = list(r['emojis'])
    conn.close()
    
    register_handlers()
    print(f"✅ Bot ready! {len(auto_react)} channels loaded.")

# Auto init
init_bot()
