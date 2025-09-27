import os
import telebot
from flask import Flask, request
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# تخزين الصفقات
open_trades = {}

@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "✅ البوت شغال", 200

# ============ أوامر ============ #
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["صفقة جديدة", "قائمة الصفقات", "تحديث الأسعار"]
    markup.add(*buttons)
    bot.reply_to(message, "👋 أهلاً! اكتب اسم العملة أو افتح صفقة جديدة.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "صفقة جديدة")
def new_trade(message):
    bot.reply_to(message, "✍️ اكتب تفاصيل الصفقة:\n\nBuy Gold 1900 SL 1880 TP1 1920 TP2 1930 TP3 1950")

# حفظ صفقة
@bot.message_handler(func=lambda msg: msg.text.startswith(("Buy", "Sell")))
def save_trade(message):
    trade = message.text.split()
    if len(trade) < 7:
        bot.reply_to(message, "⚠️ الصيغة غير صحيحة.\nجرّب: Buy Gold 1900 SL 1880 TP1 1920 TP2 1930 TP3 1950")
        return

    action, symbol, entry = trade[0], trade[1], float(trade[2])
    SL = float(trade[4])
    TP1 = float(trade[6])
    TP2 = float(trade[8]) if len(trade) > 8 else None
    TP3 = float(trade[10]) if len(trade) > 10 else None

    open_trades[symbol] = {
        "action": action,
        "entry": entry,
        "SL": SL,
        "TPs": [TP1, TP2, TP3],
        "status": "مفتوحة",
        "activated": False,
        "progress": 0  # 0=جديدة، 1=TP1، 2=TP2، 3=TP3
    }

    bot.reply_to(message, f"✅ صفقة جديدة:\n{action} {symbol} @ {entry}\nSL: {SL}\nTPs: {TP1}, {TP2}, {TP3}")

# قائمة الصفقات
@bot.message_handler(func=lambda msg: msg.text == "قائمة الصفقات")
def list_trades(message):
    if not open_trades:
        bot.reply_to(message, "📭 لا توجد صفقات.")
        return

    text = "📊 الصفقات:\n\n"
    for sym, t in open_trades.items():
        status = "✅ مفعلة" if t["activated"] else "⌛ بانتظار التفعيل"
        text += f"{t['action']} {sym} @ {t['entry']} | SL: {t['SL']} | TPs: {t['TPs']} | {status}\n\n"
    bot.reply_to(message, text)

# تحديث الأسعار (محاكاة)
@bot.message_handler(func=lambda msg: msg.text == "تحديث الأسعار")
def update_prices(message):
    notifications = []
    for sym, t in list(open_trades.items()):
        current_price = t["entry"]  # ⚠️ محاكاة: السعر = الدخول

        # 🚨 التفعيل
        if not t["activated"] and current_price == t["entry"]:
            t["activated"] = True
            notifications.append(f"🚨 الصفقة على {sym} تفعلت عند {t['entry']}")

        # إذا مفعلة نتابع الأهداف
        if t["activated"]:
            progress = t["progress"]

            # 🎯 TP1
            if progress == 0 and current_price >= t["TPs"][0]:
                t["progress"] = 1
                notifications.append(f"🎯 الصفقة {sym} وصلت TP1 عند {t['TPs'][0]}\n➡️ خذ ربح جزئي وانقل الاستوب على الدخول")

            # 🎯 TP2
            elif progress == 1 and t["TPs"][1] and current_price >= t["TPs"][1]:
                t["progress"] = 2
                notifications.append(f"🎯 الصفقة {sym} وصلت TP2 عند {t['TPs'][1]}\n➡️ انقل الاستوب على TP1 وخذ ربح إضافي")

            # 🎯 TP3
            elif progress == 2 and t["TPs"][2] and current_price >= t["TPs"][2]:
                t["progress"] = 3
                t["status"] = "مغلقة"
                notifications.append(f"🏆 الصفقة {sym} وصلت TP3 عند {t['TPs'][2]}\n✅ الصفقة أغلقت على كامل الأهداف")
                del open_trades[sym]

            # 🔴 وقف الخسارة
            if current_price <= t["SL"]:
                t["status"] = "مغلقة"
                notifications.append(f"❌ الصفقة {sym} ضربت وقف الخسارة {t['SL']}")
                del open_trades[sym]

    if notifications:
        bot.reply_to(message, "\n".join(notifications))
    else:
        bot.reply_to(message, "⌛ لا جديد، الصفقات شغالة.")

# تشغيل السيرفر
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
