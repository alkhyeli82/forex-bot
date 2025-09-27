import os
import telebot
from flask import Flask, request
import openai
from telebot import types

# ====== التوكنات من Render Environment Variables ======
TOKEN = os.environ.get("BOT_TOKEN")
openai.api_key = os.environ.get("OPENAI_API_KEY")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في Environment Variables")
if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY غير موجود في Environment Variables")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ====== Webhook endpoint ======
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# ====== Route لفحص البوت ======
@app.route("/")
def webhook():
    return "✅ البوت شغال", 200

# ====== /start ======
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🟡 Gold", callback_data="Gold"),
        types.InlineKeyboardButton("₿ Bitcoin", callback_data="Bitcoin"),
        types.InlineKeyboardButton("💶 EURUSD", callback_data="EURUSD"),
    )
    bot.reply_to(
        message,
        "👋 أهلًا! اكتب اسم العملة أو السلعة (مثال: EURUSD, Bitcoin, Gold) أو اختر من الأزرار:",
        reply_markup=markup
    )

# ====== /help ======
@bot.message_handler(commands=["help"])
def help_message(message):
    bot.reply_to(
        message,
        "ℹ️ الأوامر المتاحة:\n"
        "/start - بدء استخدام البوت\n"
        "/help - عرض التعليمات\n"
        "يمكنك أيضًا كتابة أي عملة أو سلعة مباشرة (مثال: Gold, Bitcoin, EURUSD)."
    )

# ====== Noro AI GPT ======
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

# ====== استقبال أي رسالة ======
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_text = message.text
    analysis = ask_noro_ai(user_text)
    bot.reply_to(message, analysis)

# ====== معالجة ضغط الأزرار ======
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    query = call.data
    analysis = ask_noro_ai(query)
    bot.send_message(call.message.chat.id, f"🔎 التحليل لـ {query}:\n\n{analysis}")

# ====== تشغيل على Render ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    bot.set_webhook(url="https://forex-bot-31ws.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=port)
