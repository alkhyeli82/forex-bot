import os
import telebot
from flask import Flask, request

# توكن البوت بين علامتي اقتباس
TOKEN = "8477120330:AAGNqSX4Kb1wMhQcGqeNRyTZfqJhZw2Vbdg"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# يستقبل التلغرام التحديثات عبر الويب هوك
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# صفحة فحص سريعة
@app.route("/")
def webhook():
    return "البوت شغال ✅", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-mwej.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
