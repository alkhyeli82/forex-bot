# app.py
import os
from flask import Flask, request
import telebot

TOKEN = os.getenv("BOT_TOKEN")  # عندك هذا المتغير في Render
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# صحّة الخدمة
@app.get("/")
def index():
    return "OK"

# تعيين الويب هوك
@app.get("/setwebhook")
def set_webhook():
    # يبني رابط https://<your-service>.onrender.com/webhook
    base = request.url_root.replace("http://", "https://")
    url = base + "webhook"
    bot.remove_webhook()
    ok = bot.set_webhook(url=url, timeout=10)
    return {"set_webhook": ok, "url": url}

# نقطة استلام رسائل تيليجرام
@app.post("/webhook")
def webhook():
    if request.headers.get("content-type") == "application/json":
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return "ok", 200
    return "unsupported", 400

# أوامر/رسائل بسيطة للاختبار
@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "أهلًا ✅ البوت شغّال")

@bot.message_handler(func=lambda m: True)
def echo(m):
    txt = (m.text or "").strip().lower()
    if txt in ["gold", "ذهب", "صفقة الذهب"]:
        bot.reply_to(m, "صفقة الذهب ✨ (رسالة اختبار)")
    else:
        bot.reply_to(m, f"إنت كتبت: {m.text}")
