import telebot
from flask import Flask, request

TOKEN = "8477120330:AAGNqSX4Kb1wMhQcGqeNRyTZfqJhZw2Vbdg"
bot = telebot.TeleBot(TOKEN)

# Flask app
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
    return "البوت شغال ✅", 200

# أوامر البوت
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "أهلاً 👋، البوت شغال معاك!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"استقبلت رسالتك: {message.text}")

# تشغيل
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-3ims.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)

