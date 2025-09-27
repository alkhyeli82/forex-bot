import telebot
from flask import Flask, request

TOKEN = "ضع_التوكن_الجديد_هنا"
bot = telebot.TeleBot(TOKEN)

# عرّف Flask app
app = Flask(__name__)

# Webhook endpoint
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# عشان تختبر البوت
@app.route("/")
def webhook():
    return "البوت شغال ✅", 200


# هنا لازم تخلي البوت يربط نفسه بالرابط
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-mwej.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
