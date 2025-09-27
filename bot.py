import os
import telebot
from flask import Flask, request

# التوكن (خذه من BotFather وحطه في Environment Variable في Render باسم BOT_TOKEN)
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# قاعدة بيانات بسيطة للتوصيات
signals = {}

# Webhook
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "✅ البوت شغال", 200

# أمر /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "👋 أهلاً بك في بوت التوصيات!\n\nاكتب /help للمساعدة.")

# أمر /help
@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(message,
        "📌 أوامر البوت:\n\n"
        "/signal → إضافة توصية جديدة (خاصة بالأدمن)\n"
        "/list → عرض التوصيات المفتوحة\n"
        "/close → إغلاق توصية\n\n"
        "مثال إضافة توصية:\n"
        "`/signal Buy Gold 1900 SL 1880 TP1 1920 TP2 1930 TP3 1950`",
        parse_mode="Markdown"
    )

# إضافة توصية جديدة
@bot.message_handler(commands=["signal"])
def add_signal(message):
    try:
        parts = message.text.split()
        if len(parts) < 7:
            bot.reply_to(message, "⚠️ صيغة غير صحيحة.\nمثال: /signal Buy Gold 1900 SL 1880 TP1 1920 TP2 1930 TP3 1950")
            return
        
        action, symbol, entry = parts[1], parts[2], float(parts[3])
        SL = float(parts[5])
        TP1 = float(parts[7])
        TP2 = float(parts[9]) if len(parts) > 9 else None
        TP3 = float(parts[11]) if len(parts) > 11 else None

        signals[symbol] = {
            "action": action,
            "entry": entry,
            "SL": SL,
            "TPs": [TP1, TP2, TP3],
            "status": "مفتوحة"
        }

        bot.reply_to(message,
            f"📢 توصية جديدة:\n"
            f"{action} {symbol} @ {entry}\n"
            f"SL: {SL}\n"
            f"TPs: {TP1}, {TP2}, {TP3}"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

# عرض التوصيات
@bot.message_handler(commands=["list"])
def list_signals(message):
    if not signals:
        bot.reply_to(message, "📭 لا توجد توصيات مفتوحة.")
        return
    
    text = "📊 التوصيات:\n\n"
    for sym, s in signals.items():
        text += f"{s['action']} {sym} @ {s['entry']} | SL: {s['SL']} | TPs: {s['TPs']} | {s['status']}\n\n"
    bot.reply_to(message, text)

# إغلاق توصية
@bot.message_handler(commands=["close"])
def close_signal(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ الصيغة: /close Gold")
            return
        
        symbol = parts[1]
        if symbol in signals:
            signals[symbol]["status"] = "مغلقة"
            bot.reply_to(message, f"✅ التوصية {symbol} تم إغلاقها.")
        else:
            bot.reply_to(message, "❌ التوصية غير موجودة.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

# تشغيل السيرفر
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)

