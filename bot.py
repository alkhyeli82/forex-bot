import os
import telebot
from flask import Flask, request
import openai
from telebot import types

# جلب التوكنات من Environment Variables
TOKEN = os.environ.get("BOT_TOKEN")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# تأكيد أن التوكنات موجودة
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")
if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY غير موجود في Environment Variables")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ============ Webhook ============ #
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "✅ البوت شغال تمام", 200

# ============ الأوامر ============ #
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Gold", "Silver", "Bitcoin", "Ethereum", "EURUSD", "GBPUSD", "USDJPY", "Oil", "Nasdaq", "DowJones"]
    markup.add(*buttons)
    bot.reply_to(
        message,
        "👋 أهلًا بك في بوت التحليل!\n\n"
        "اكتب أو اضغط على زر من الأزرار تحت لتحصل على تحليل فوري 📊",
        reply_markup=markup
    )

@bot.message_handler(commands=["help"])
def send_help(message):
    bot.reply_to(
        message,
        "ℹ️ أوامر البوت:\n"
        "/start → تشغيل البوت وفتح قائمة الأزرار\n"
        "/help → عرض هذه المساعدة\n\n"
        "🔎 تقدر تكتب أي عملة أو سلعة مباشرة (مثال: Gold, Bitcoin, EURUSD) للحصول على تحليل."
    )

# ============ دالة GPT ============ #
def ask_noro_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت خبير تحليل فني بأسلوب ICT و SMC، تعطي تحليلات واضحة وسهلة."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ خطأ بالاتصال مع Noro AI: {str(e)}"

# ============ استقبال الرسائل ============ #
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_text = message.text.strip()
    analysis = ask_noro_ai(user_text)
    bot.reply_to(message, analysis)

# ============ تشغيل السيرفر ============ #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()

    app_url = "https://forex-bot-31ws.onrender.com/" + TOKEN
    bot.set_webhook(url=app_url)

    app.run(host="0.0.0.0", port=port)
