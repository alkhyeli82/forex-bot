import os
import telebot
from flask import Flask, request
import openai
import yfinance as yf
import schedule
import time
import threading
from datetime import datetime

TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TOKEN)
openai.api_key = OPENAI_KEY
app = Flask(__name__)

# قواعد بيانات مؤقتة
open_trades = {}
closed_trades = []

# Webhook
@app.route("/" + TOKEN, methods=["POST"])
def getMessage():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "✅ البوت شغال", 200

# ---- الدوال ----
def get_price(symbol):
    try:
        data = yf.Ticker(symbol)
        price = data.history(period="1d")["Close"].iloc[-1]
        return round(price, 2)
    except Exception:
        return None

def ask_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت خبير فوركس بأسلوب ICT/SMC."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"

def generate_weekly_report():
    if not closed_trades:
        return "📭 لا توجد نتائج بعد."
    
    wins = [t for t in closed_trades if t["result"] > 0]
    losses = [t for t in closed_trades if t["result"] <= 0]
    total_pips = sum([t["result"] for t in closed_trades])

    text = "📅 ملخص الأسبوع:\n\n"
    text += f"✅ رابحة: {len(wins)}\n"
    text += f"❌ خاسرة: {len(losses)}\n"
    text += f"📈 مجموع البيبس: {total_pips}\n\n"
    for t in closed_trades:
        text += f"{t['symbol']} → {t['result']} pips\n"
    return text

# ---- أوامر ----
@bot.message_handler(commands=["weekly"])
def weekly(message):
    bot.reply_to(message, generate_weekly_report())

# ---- جدولة التقرير الأسبوعي ----
CHAT_ID = os.environ.get("CHAT_ID")  # ID القناة أو المجموعة

def job():
    report = generate_weekly_report()
    if CHAT_ID:
        bot.send_message(CHAT_ID, report)

def run_scheduler():
    schedule.every().friday.at("23:59").do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

# تشغيل الجدولة في Thread منفصل
t = threading.Thread(target=run_scheduler)
t.start()

# ---- تشغيل السيرفر ----
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # مهم: Render يعطيك PORT جاهز
    bot.remove_webhook()
    bot.set_webhook(url=f"https://forex-bot-31ws.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=port)
