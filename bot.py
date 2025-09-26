import os
import telebot

# جلب التوكن من Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً 👋 البوت شغال ✅")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"إنت كتبت: {message.text}")

# تشغيل البوت
bot.polling(non_stop=True)
