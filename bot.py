import os
import telebot
from flask import Flask, request
import openai

# جلب التوكنات من Environment Variables في Render
TOKEN = os.environ.get("8477120330:AAGNqSX4Kb1wMhQcGqeNRyTZfqJhZw2Vbdg")  
openai.api_key = os.environ.get("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")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# قائمة الرموز المدعومة
SUPPORTED_ASSETS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD",
    "XAUUSD", "Gold", "Silver", "Oil", "WTI", "Brent",
    "Bitcoin", "BTCUSD", "Ethereum", "ETHUSD", "Nasdaq", "SP500"
]

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
    return "✅ البوت شغال مع Noro AI", 200

# أمر /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    help_text = (
        "👋 أهلًا بك في *WhaleForex Bot*!\n\n"
        "📊 ارسل اسم العملة أو السلعة لتحصل على تحليل من Noro AI.\n"
        "✅ أمثلة: Gold, Bitcoin, EURUSD, Oil\n\n"
        "⚡ الأصول المدعومة:\n" + ", ".join(SUPPORTED_ASSETS)
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

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
    user_text = message.text.strip()

    # التحقق من أن الأصل مدعوم
    if user_text not in SUPPORTED_ASSETS:
        bot.reply_to(
            message,
            f"⚠️ الأصل *{user_text}* غير مدعوم.\n\n✅ الأصول المتاحة:\n" + ", ".join(SUPPORTED_ASSETS),
            parse_mode="Markdown"
        )
        return

    # طلب التحليل من Noro AI
    bot.reply_to(message, f"⏳ جاري تحليل *{user_text}*...\n", parse_mode="Markdown")
    analysis = ask_noro_ai(user_text)
    bot.reply_to(message, f"💹 تحليل {user_text}:\n\n{analysis}")

# تشغيل السيرفر والويب هوك
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
