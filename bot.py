import telebot
import os

# قراءة التوكن من المتغير البيئي
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# أمر البداية
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً 👋 البوت شغّال ✅\nاستخدم /signal لإرسال إشارة.")

# أمر إرسال إشارة
@bot.message_handler(commands=['signal'])
def signal(message):
    try:
        # تقسيم النص بعد الأمر
        parts = message.text.split()
        if len(parts) < 6:
            bot.reply_to(message, "❌ صيغة الإشارة غير صحيحة.\nمثال:\n/signal BUY GOLD 1900 SL 1890 TP1 1910 TP2 1920")
            return

        action = parts[1]   # BUY أو SELL
        symbol = parts[2]   # GOLD أو EURUSD ...
        entry = parts[3]
        sl = parts[5]

        # استخراج التيك بروفيت (TP)
        tps = [tp for tp in parts[6:] if "TP" in tp or tp.replace('.', '').isdigit()]

        text = f"""
📊 *إشارة جديدة* 📊
----------------------
🔹 الصفقة: {action} {symbol}
🔹 دخول: {entry}
🔹 وقف خسارة: {sl}
"""

        for i, tp in enumerate(tps, start=1):
            text += f"🎯 TP{i}: {tp}\n"

        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ خطأ: {e}")

# تشغيل البوت
bot.polling(non_stop=True)