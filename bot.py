import os
import telebot
from flask import Flask, request
import openai

# جلب التوكنات من Environment Variables في Render
TOKEN = os.environ.get("BOT_TOKEN")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# تأكيد أن التوكنات موجودة
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")
if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY غير موجود في Environment Variables")

# تهيئة البوت والتطبيق
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Webhook endpoint (معالجة رسائل تيليجرام)
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# Route لفحص البوت من المتصفح
@app.route("/")
def webhook():
    return "✅ البوت شغال 100%", 200

# أمر /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 أهلًا! اكتب اسم العملة أو السلعة (مثال: EURUSD, Bitcoin, Gold) للحصول على تحليل."
    )

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

# تشغيل التطبيق
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
