import telebot
from flask import Flask, request
import openai

# التوكن مباشرة (موصى فقط للتجربة، الأفضل تستعمل Secrets)
TOKEN = "8477120330:AAGNqSX4Kb1wMhQcGqeNRyTZfqJhZw2Vbdg"
bot = telebot.TeleBot(TOKEN)

# OpenAI API Key من Secrets
openai.api_key = "ضع_هنا_مفتاح_OPENAI_الخاص_بك"

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

# أمر /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً! ارسل اسم العملة (مثال: EURUSD أو Bitcoin) وأنا أجيبك بتحليل من NORO AI.")

# دالة استدعاء GPT
def ask_noro_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "انت خبير تحليل فني وفوركس بأسلوب ICT و SMC."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ خطأ بالاتصال بـ Noro AI: {str(e)}"

# أي رسالة يرسلها المستخدم
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_text = message.text
    analysis = ask_noro_ai(user_text)
    bot.reply_to(message, analysis)

# تشغيل
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-3ims.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
