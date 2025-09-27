import os
import telebot
from flask import Flask, request
import openai

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

# أمر /start مع كيبورد رئيسي
@bot.message_handler(commands=["start"])
def send_welcome(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Gold", "Bitcoin")
    keyboard.row("EURUSD", "GBPUSD", "USDJPY")
    bot.reply_to(
        message,
        "👋 أهلًا! اختر من الأزرار أو اكتب اسم العملة/السلعة لتحصل على تحليل.\n"
        "اكتب /help لمعرفة المزيد.",
        reply_markup=keyboard
    )

# أمر /help
@bot.message_handler(commands=["help"])
def send_help(message):
    bot.reply_to(
        message,
        "ℹ️ الأوامر المتاحة:\n"
        "- /start ➝ لعرض لوحة الأزرار.\n"
        "- /forex ➝ أشهر أزواج الفوركس.\n"
        "- /crypto ➝ أشهر العملات الرقمية.\n"
        "- أو اكتب اسم أي عملة/سلعة مباشرة (مثال: Gold, Bitcoin, EURUSD)."
    )

# أمر /forex
@bot.message_handler(commands=["forex"])
def send_forex(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("EURUSD", "GBPUSD")
    keyboard.row("USDJPY", "AUDUSD")
    bot.reply_to(message, "📊 اختر زوج الفوركس:", reply_markup=keyboard)

# أمر /crypto
@bot.message_handler(commands=["crypto"])
def send_crypto(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Bitcoin", "Ethereum")
    keyboard.row("Solana", "XRP")
    bot.reply_to(message, "💰 اختر العملة الرقمية:", reply_markup=keyboard)

# دالة استدعاء GPT (Noro AI style)
def ask_noro_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت خبير تحليل فني بأسلوب ICT و SMC."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ خطأ بالاتصال مع Noro AI: {str(e)}"

# استقبال أي رسالة من المستخدم
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_text = message.text
    analysis = ask_noro_ai(user_text)
    bot.reply_to(message, analysis)

# تشغيل
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # ✅ Render يمرر البورت هنا
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
