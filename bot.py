import os
import telebot
from telebot.types import Message

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
subscribers = set()

def is_admin(msg: Message) -> bool:
    return ADMIN_ID and msg.from_user and msg.from_user.id == ADMIN_ID

def format_signal(side, symbol, entry, sl, tps):
    side = side.upper()
    arrow = "🟢 BUY" if side == "BUY" else "🔴 SELL"
    lines = [f"<b>{arrow}</b>  |  <b>{symbol.upper()}</b>",
             f"🎯 Entry: <b>{entry}</b>",
             f"⛔ SL: <b>{sl}</b>"]
    for i, tp in enumerate(tps, start=1):
        lines.append(f"✅ TP{i}: <b>{tp}</b>")
    lines += ["—", "⚠️ هذه ليست نصيحة استثمارية."]
    return "\n".join(lines)

def parse_signal_args(text):
    parts = text.split()
    if len(parts) < 6: return None
    side, symbol, entry = parts[1], parts[2], parts[3]
    sl, tps, i = None, [], 4
    while i < len(parts):
        p = parts[i].upper()
        if p == "SL":
            sl = parts[i+1]; i += 2
        elif p.startswith("TP"):
            tps.append(parts[i+1]); i += 2
        else:
            i += 1
    if sl is None or not tps: return None
    return side, symbol, entry, sl, tps

@bot.message_handler(commands=['start'])
def start_cmd(msg: Message):
    bot.reply_to(msg,
        "✅ البوت شغّال!\n"
        "• /id — رقمك\n"
        "• /subscribe — اشتراك\n"
        "• /unsubscribe — إلغاء\n"
        "• /signal — إرسال صفقة (للمشرف)\n"
        "• /help — صيغة الاستخدام")

@bot.message_handler(commands=['help'])
def help_cmd(msg: Message):
    bot.reply_to(msg,
        "صيغة /signal (للمشرف فقط):\n"
        "<code>/signal BUY EURUSD 1.0800 SL 1.0750 TP1 1.0850 TP2 1.0900</code>")

@bot.message_handler(commands=['id'])
def id_cmd(msg: Message):
    bot.reply_to(msg, f"🪪 Your ID: <code>{msg.from_user.id}</code>")

@bot.message_handler(commands=['subscribe'])
def sub_cmd(msg: Message):
    subscribers.add(msg.chat.id)
    bot.reply_to(msg, "🔔 تم الاشتراك.")

@bot.message_handler(commands=['unsubscribe'])
def unsub_cmd(msg: Message):
    subscribers.discard(msg.chat.id)
    bot.reply_to(msg, "🔕 تم الإلغاء.")

@bot.message_handler(commands=['signal'])
def signal_cmd(msg: Message):
    if not is_admin(msg):
        bot.reply_to(msg, "⛔ للمشرف فقط."); return
    parsed = parse_signal_args(msg.text)
    if not parsed:
        bot.reply_to(msg, "❌ صيغة غير صحيحة. اكتب /help للمثال."); return
    side, symbol, entry, sl, tps = parsed
    bot.send_message(msg.chat.id, format_signal(side, symbol, entry, sl, tps))

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(msg: Message):
    if not is_admin(msg):
        bot.reply_to(msg, "⛔ للمشرف فقط."); return
    parsed = parse_signal_args(msg.text.replace("/broadcast", "/signal", 1))
    if not parsed:
        bot.reply_to(msg, "❌ صيغة غير صحيحة للبث."); return
    side, symbol, entry, sl, tps = parsed
    card = format_signal(side, symbol, entry, sl, tps)
    sent, fail = 0, 0
    for cid in list(subscribers):
        try:
            bot.send_message(cid, card); sent += 1
        except Exception:
            fail += 1
    bot.reply_to(msg, f"📢 تم: {sent} / فشل: {fail} / إجمالي: {len(subscribers)}")

bot.polling(non_stop=True)