import os
import telebot
from flask import Flask, request
import openai

# يسحب التوكنات من Environment Variables
TOKEN = os.environ.get("8477120330:AAGNqSX4Kb1wMhQcGqeNRyTZfqJhZw2Vbdg")  
openai.api_key = os.environ.get("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")

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

# أمر /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلًا! ارسل اسم العملة أو السلعة (مثال: EURUSD, Bitcoin, Gold) لتحصل على تحليل.")

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
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
" + TOKEN)
    app.run(host="0.0.0.0", port=port)
