import os
from telebot import types
from datetime import datetime, timedelta
from database import get_db, is_admin, is_premium, get_premium_expiry

# ==================== COMMAND HANDLERS ====================

def cmd_start(bot, message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⭐ Premium", callback_data="premium"),
        types.InlineKeyboardButton("📋 Plans", callback_data="plans")
    )
    markup.add(
        types.InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        types.InlineKeyboardButton("👤 Status", callback_data="status")
    )
    
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel"))
    
    bot.reply_to(message, 
        f"🤖 **Welcome {message.from_user.first_name}!**\n\n"
        "🔥 Auto Reaction Bot Pro\n\n"
        "• Auto react on posts\n"
        "• Multiple emojis at once\n"
        "• Post link reactions\n"
        "• Premium plans available\n\n"
        "👇 Choose option:",
        parse_mode="Markdown", reply_markup=markup)

def cmd_setreaction(bot, message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "❌ Premium feature! Use /plans")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(message, "📝 `/setreaction <channel_id> <emojis>`\nExample: `/setreaction -100123456 👍❤️`", parse_mode="Markdown")
        return
    
    channel_input = args[1]
    emojis = args[2]
    
    try:
        if channel_input.startswith("@"):
            chat = bot.get_chat(channel_input)
            channel_id = chat.id
        else:
            channel_id = int(channel_input)
            chat = bot.get_chat(channel_id)
    except:
        bot.reply_to(message, "❌ Invalid channel!")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO reactions (user_id, channel_id, emojis) VALUES (?,?,?)",
                   (user_id, channel_id, emojis))
    conn.commit()
    conn.close()
    
    # Update memory
    import bot
    if channel_id not in bot.auto_react:
        bot.auto_react[channel_id] = {}
    bot.auto_react[channel_id][user_id] = list(emojis)
    
    bot.reply_to(message, f"✅ Auto reaction set!\nChannel: {chat.title}\nEmojis: {emojis}")

def cmd_react(bot, message):
    user_id = message.from_user.id
    
    if not is_admin(user_id) and not is_premium(user_id):
        bot.reply_to(message, "❌ Premium feature!")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        bot.reply_to(message, "📝 `/react <post_link> <emojis>`\nExample: `/react https://t.me/ch/10 👍`", parse_mode="Markdown")
        return
    
    post_link = args[1]
    emojis = list(args[2])
    
    try:
        if "t.me/c/" in post_link:
            parts = post_link.replace("https://t.me/c/", "").split("/")
            channel_id = int(f"-100{parts[0]}")
            message_id = int(parts[1])
        else:
            parts = post_link.replace("https://t.me/", "").split("/")
            channel_id = f"@{parts[0]}"
            message_id = int(parts[1])
        
        reaction_list = [types.ReactionTypeEmoji(e) for e in emojis]
        bot.set_message_reaction(channel_id, message_id, reaction_list, is_big=True)
        bot.reply_to(message, f"✅ Reacted: {args[2]}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def cmd_status(bot, message):
    user_id = message.from_user.id
    status = f"👤 **Status**\n🆔 ID: `{user_id}`\n"
    
    if is_admin(user_id):
        status += "👑 Role: Admin\n"
    elif is_premium(user_id):
        expiry = get_premium_expiry(user_id)
        status += f"⭐ Role: Premium\n📅 Expires: {expiry}\n"
    else:
        status += "👤 Role: Free\n"
    
    bot.reply_to(message, status, parse_mode="Markdown")

# ==================== MENU FUNCTIONS ====================

def show_admin_panel(bot, message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Admin", callback_data="add_admin"),
        types.InlineKeyboardButton("➖ Remove Admin", callback_data="remove_admin")
    )
    markup.add(
        types.InlineKeyboardButton("📋 Plans", callback_data="view_plans"),
        types.InlineKeyboardButton("➕ Add Plan", callback_data="add_plan")
    )
    markup.add(
        types.InlineKeyboardButton("✏️ Modify Plan", callback_data="modify_plan"),
        types.InlineKeyboardButton("🗑 Delete Plan", callback_data="delete_plan")
    )
    markup.add(
        types.InlineKeyboardButton("📢 Force Channels", callback_data="force_channels"),
        types.InlineKeyboardButton("💳 UPI Settings", callback_data="upi_settings")
    )
    markup.add(
        types.InlineKeyboardButton("📨 Broadcast", callback_data="broadcast_menu"),
        types.InlineKeyboardButton("✅ Verify Payment", callback_data="verify_payment")
    )
    
    bot.send_message(message.chat.id, "👑 **Admin Panel**", parse_mode="Markdown", reply_markup=markup)

def show_plans_menu(bot, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans ORDER BY price")
    plans = cursor.fetchall()
    conn.close()
    
    if not plans:
        bot.send_message(message.chat.id, "No plans available!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for plan in plans:
        markup.add(types.InlineKeyboardButton(
            f"💎 {plan['name']} - ₹{plan['price']} / {plan['days']}d",
            callback_data=f"buy_{plan['id']}"
        ))
    markup.add(types.InlineKeyboardButton("💳 Payment Info", callback_data="payment_info"))
    
    bot.send_message(message.chat.id, "📋 **Plans:**", parse_mode="Markdown", reply_markup=markup)

# ==================== PROCESS FUNCTIONS ====================

def process_add_admin(bot, message):
    try:
        new_id = int(message.text)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id, added_by, added_date) VALUES (?,?,?)",
                      (new_id, message.from_user.id, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Admin added: `{new_id}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Invalid ID!")

def process_add_plan(bot, message):
    try:
        parts = message.text.split("|")
        name, days, price = parts[0].strip(), int(parts[1]), float(parts[2])
        features = parts[3].strip() if len(parts) > 3 else ""
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO plans (name, days, price, features) VALUES (?,?,?,?)",
                      (name, days, price, features))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"✅ Plan '{name}' added! 💰₹{price}")
    except:
        bot.send_message(message.chat.id, "❌ Format: name|days|price|features")

def process_verify_payment(bot, message):
    if message.photo and message.caption:
        try:
            parts = message.caption.split("|")
            user_id = int(parts[0].strip())
            plan_id = int(parts[1].strip())
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
            plan = cursor.fetchone()
            
            if plan:
                end = datetime.now() + timedelta(days=plan['days'])
                cursor.execute("INSERT OR REPLACE INTO premium VALUES (?,?,?,?)",
                             (user_id, plan['name'], datetime.now().strftime("%Y-%m-%d"),
                              end.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                
                try:
                    bot.send_message(user_id, f"✅ Premium Activated!\nPlan: {plan['name']}\nExpires: {end.strftime('%d-%m-%Y')}")
                except:
                    pass
                
                bot.send_message(message.chat.id, f"✅ Premium activated for {user_id}")
        except:
            bot.send_message(message.chat.id, "❌ Format: user_id|plan_id")

def handle_buy_plan(bot, message, plan_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
    plan = cursor.fetchone()
    conn.close()
    
    if not plan:
        bot.send_message(message.chat.id, "Plan not found!")
        return
    
    upi = os.environ.get("UPI_ID", "yourupi@bank")
    text = f"""
💳 **Payment**
📦 Plan: {plan['name']}
💰 Amount: ₹{plan['price']}
📅 Duration: {plan['days']} days

**UPI:** `{upi}`

Send screenshot with caption:
`{message.from_user.id}|{plan_id}`
"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

def process_broadcast(bot, message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM premium UNION SELECT DISTINCT user_id FROM admins")
    users = cursor.fetchall()
    conn.close()
    
    sent = 0
    for user in users:
        try:
            bot.send_message(user['user_id'], f"📢 {message.text}")
            sent += 1
        except:
            pass
    
    bot.send_message(message.chat.id, f"✅ Sent to {sent} users")
