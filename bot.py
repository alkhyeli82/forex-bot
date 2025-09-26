import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")  # نخزن التوكن في إعدادات السيرفر
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 أهلاً بك! بوت WhaleForex شغال ✅")

bot.polling(none_stop=True)
