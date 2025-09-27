# -*- coding: utf-8 -*-
import os, time
from flask import Flask, request, jsonify
import telebot
from telebot import types
import yfinance as yf
import pandas as pd

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ===== الأصول المتاحة: اسم ودّي -> تيكر Yahoo =====
ALL_SYMBOLS = {
    # سلع/مؤشرات/كريبتو
    "GOLD":"XAUUSD=X", "SILVER":"XAGUSD=X", "USOIL":"CL=F",
    "NAS100":"^NDX", "DOW":"^DJI", "SPX":"^GSPC", "BTC":"BTC-USD",
    # Majors
    "EURUSD":"EURUSD=X", "GBPUSD":"GBPUSD=X", "USDJPY":"JPY=X",
    "USDCHF":"CHF=X", "USDCAD":"CAD=X", "AUDUSD":"AUDUSD=X", "NZDUSD":"NZDUSD=X",
    # Minors
    "GBPJPY":"GBPJPY=X", "EURJPY":"EURJPY=X", "EURAUD":"EURAUD=X",
}

# فئات سريعة للاختيار
CATEGORIES = {
    "Majors": {"EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD"},
    "Minors": {"GBPJPY","EURJPY","EURAUD"},
    "Metals": {"GOLD","SILVER"},
    "Indices":{"NAS100","DOW","SPX"},
    "Crypto": {"BTC"},
}

# اختيارات المستخدمين (ذاكرة مؤقتة)
user_choices = {}   # user_id -> set(["GOLD","USOIL",...])

# ===== أدوات المؤشرات السريعة =====
def rsi(series, length=14):
    d = series.diff()
    up = d.clip(lower=0)
    dn = (-d).clip(lower=0)
    ma_up = up.ewm(alpha=1/length, adjust=False).mean()
    ma_dn = dn.ewm(alpha=1/length, adjust=False).mean()
    rs = ma_up / (ma_dn + 1e-9)
    return 100 - (100 / (1 + rs))

def atr(df, length=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([(h-l), (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    return tr.rolling(length).mean()

def build_card(name, side, price, entry, sl, tps):
    side = side.upper()
    arrow = "🟢 BUY" if side=="BUY" else ("🔴 SELL" if side=="SELL" else "⚪ HOLD")
    lines = [f"<b>{name}</b> | {arrow}", f"💰 Price: <b>{price:.5f}</b>"]
    if side in ("BUY","SELL"):
        lines += [f"🎯 Entry: <b>{entry:.5f}</b>", f"⛔ SL: <b>{sl:.5f}</b>"]
        for i, tp in enumerate(tps, start=1):
            lines.append(f"✅ TP{i}: <b>{tp:.5f}</b>")
    lines += ["—", "⚠️ تعليم فقط وليست نصيحة استثمارية."]
    return "\n".join(lines)

def calc_signal(nice_name, ticker):
    df = yf.download(ticker, period="2d", interval="5m", progress=False)
    if df is None or df.empty or len(df) < 60:
        return f"⚠️ لا توجد بيانات كافية لـ {nice_name}."
    df = df.dropna()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["RSI14"] = rsi(df["Close"], 14)
    df["ATR14"] = atr(df, 14)

    last = df.iloc[-1]
    price = float(last["Close"]); sma50 = float(last["SMA50"])
    r = float(last["RSI14"]); a = float(last["ATR14"])

    # منطق بسيط (سكالب 5m):
    # BUY إذا فوق SMA50 و RSI<40 — SELL إذا تحت SMA50 و RSI>60 — وإلا HOLD
    side = "HOLD"
    if price > sma50 and r < 40:
        side = "BUY"
    elif price < sma50 and r > 60:
        side = "SELL"

    if side == "BUY":
        entry, sl = price, price - a*1.5
        tps = [price + a*1.0, price + a*2.0, price + a*3.0]
        return build_card(nice_name, side, price, entry, sl, tps)
    elif side == "SELL":
        entry, sl = price, price + a*1.5
        tps = [price - a*1.0, price - a*2.0, price - a*3.0]
        return build_card(nice_name, side, price, entry, sl, tps)
    else:
        return build_card(nice_name, side, price, price, price, [])

# ===== أوامر تيليغرام =====
@bot.message_handler(commands=['start'])
def start_cmd(m):
    user_choices.setdefault(m.from_user.id, set(["GOLD","USOIL"]))  # افتراضي
    bot.reply_to(m,
        "✅ البوت شغّال (Webhook/Render Free)\n"
        "اختر أصولك واستخرج الإشارات عند الطلب.\n\n"
        "أوامر:\n"
        "• /assets — عرض الأصول المتاحة\n"
        "• /pick — اختيار سريع بالفئات\n"
        "• /choose GOLD USOIL BTC — اختيار يدوي\n"
        "• /my — عرض أصولك المختارة\n"
        "• /now — إشارات فورية لأصولك\n"
        "• /id — رقم محادثتك")

@bot.message_handler(commands=['assets'])
def assets_cmd(m):
    keys = " ".join(sorted(ALL_SYMBOLS.keys()))
    bot.reply_to(m, f"الأصول المتاحة:\n<code>{keys}</code>")

@bot.message_handler(commands=['pick'])
def pick_cmd(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
    kb.add("Majors", "Minors", "Metals", "Indices", "Crypto")
    kb.add("DONE")
    bot.send_message(m.chat.id, "اختر فئاتك (تقدر تضغط أكثر من زر، ثم DONE):", reply_markup=kb)

@bot.message_handler(func=lambda msg: msg.text in CATEGORIES or msg.text=="DONE")
def pick_flow(m):
    uid = m.from_user.id
    user_choices.setdefault(uid, set())
    if m.text == "DONE":
        chosen = " ".join(sorted(user_choices[uid])) or "(لا شيء)"
        bot.send_message(m.chat.id, f"تم ✅\nأصولك: <code>{chosen}</code>", reply_markup=types.ReplyKeyboardRemove())
        return
    user_choices[uid] |= CATEGORIES[m.text]
    bot.send_message(m.chat.id, f"أضفت: {m.text}. تقدر تضيف فئات أخرى أو اضغط DONE.")

@bot.message_handler(commands=['choose'])
def choose_cmd(m):
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "اكتب الأصول بعد الأمر. مثال:\n/choose GOLD USOIL BTC"); return
    picked = set([p.upper() for p in parts[1:] if p.upper() in ALL_SYMBOLS])
    if not picked:
        bot.reply_to(m, "لم يتم التعرف على أي أصل. اكتب /assets لرؤية القائمة."); return
    user_choices[m.from_user.id] = picked
    bot.reply_to(m, f"تم التعيين ✅\nأصولك: <code>{' '.join(sorted(picked))}</code>")

@bot.message_handler(commands=['my'])
def my_cmd(m):
    picked = user_choices.get(m.from_user.id, set())
    if not picked:
        bot.reply_to(m, "ما عندك أصول محددة. استخدم /pick أو /choose.")
    else:
        bot.reply_to(m, f"أصولك الحالية: <code>{' '.join(sorted(picked))}</code>")

@bot.message_handler(commands=['now'])
def now_cmd(m):
    picked = user_choices.get(m.from_user.id, set())
    if not picked:
        bot.reply_to(m, "اختر أصولك بالأمر /pick أو /choose أولاً."); return
    bot.reply_to(m, "⏱️ جاري حساب الإشارات ...")
    for name in sorted(picked):
        tick = ALL_SYMBOLS[name]
        try:
            card = calc_signal(name, tick)
        except Exception as e:
            card = f"⚠️ خطأ بـ {name}: {e}"
        bot.send_message(m.chat.id, card)
        time.sleep(1.0)

@bot.message_handler(commands=['id'])
def id_cmd(m):
    bot.reply_to(m, f"🪪 <code>{m.chat.id}</code>")

# ===== Webhook endpoints (Render Free) =====
@app.post(f"/webhook/{TOKEN}")
def telegram_webhook():
    update = request.stream.read().decode("utf-8")
    if not update:
        return "NO BODY", 400
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK", 200

@app.get("/setwebhook")
def set_webhook():
    base = os.environ.get("WEBHOOK_BASE_URL")
    if not base:
        return "Set WEBHOOK_BASE_URL env var first", 500
    url = f"{base}/webhook/{TOKEN}"
    ok = bot.set_webhook(url=url, drop_pending_updates=True)
    return jsonify({"set_webhook": ok, "url": url})

@app.get("/")
def health():
    return "OK", 200
