import os
import telebot
from flask import Flask, request
import openai

# قراءة التوكنات من Environment Variables
TOKEN = os.environ.get("BOT_TOKEN")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# تأكيد أنها موجودة
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")
if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY غير موجود في Environment Variables")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Webhook endpoint
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# Route لفحص البوت
@app.route("/")
def webhook():
    return "✅ البوت شغال", 200

# أمر /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلًا! اكتب اسم العملة أو السلعة (مثال: EURUSD, Bitcoin, Gold) للحصول على تحليل.")

# استقبال أي رسالة من المستخدم
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"📩 وصلتني رسالتك: {message.text}")

# تشغيل
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
