import os
from flask import Flask, request, jsonify
import telebot

TOKEN = os.environ.get("BOT_TOKEN")  # موجود عندك في Render
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__)

# رسالة /start
@bot.message_handler(commands=['start'])
def start_msg(m):
    bot.reply_to(m, "أهلاً 👋 البوت شغال ✅ (Webhook/Render Free)")

# مثال: تكرار ما يكتبه المستخدم
@bot.message_handler(func=lambda m: True)
def echo_all(m):
    bot.reply_to(m, f"إنت كتبت: {m.text}")

# Telegram سيستدعي هذا المسار بالـ updates
@app.post(f"/webhook/{TOKEN}")
def telegram_webhook():
    update = request.stream.read().decode("utf-8")
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200

# مسار لضبط الـ webhook بسهولة
@app.get("/setwebhook")
def set_webhook():
    base = os.environ.get("WEBHOOK_BASE_URL")  # مثال: https://forex-bot-xxxx.onrender.com
    if not base:
        return "Set WEBHOOK_BASE_URL env var first", 500
    url = f"{base}/webhook/{TOKEN}"
    ok = bot.set_webhook(url=url, drop_pending_updates=True)
    return jsonify({"set_webhook": ok, "url": url})

# صحّة الخدمة
@app.get("/")
def health():
    return "OK", 200

# لا تستعمل app.run في Render؛ سنشغّل عبر gunicorn
