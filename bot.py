# -*- coding: utf-8 -*-
import os, time
import telebot
import yfinance as yf
import numpy as np
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from telebot.types import Message

# ============ الإعدادات ============
TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
INTERVAL_MIN = int(os.getenv("INTERVAL_MIN", "15"))  # كل كم دقيقة توليد إشارات تلقائية

# أسماء ودية -> تيكر Yahoo
SYMBOLS = {
    "GOLD": "XAUUSD=X",     # ذهب
    "USOIL": "CL=F",        # نفط خام
    "NAS100": "^NDX",       # ناسداك 100
    "GBPJPY": "GBPJPY=X",   # المجنون
    "DOW": "^DJI"           # الداو جونز
}
# ===================================

if not TOKEN:
    raise SystemExit("BOT_TOKEN missing")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
scheduler = BackgroundScheduler(timezone="UTC")

# ---------- مؤشرات مساعدة ----------
def rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/length, adjust=False).mean()
    ma_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-9)
    return 100 - (100 / (1 + rs))

def atr(df, length=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    prev_c = c.shift(1)
    tr = pd.concat([(h-l), (h-prev_c).abs(), (l-prev_c).abs()], axis=1).max(axis=1)
    return tr.rolling(length).mean()

def yahoo_price(ticker):
    """آخر سعر حالياً"""
    data = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
    if data is None or data.empty:
        return None
    return float(data["Close"].iloc[-1])

# ---------- نموذج الإشارة ----------
def build_card(name, side, entry, sl, tps, price=None, header="إشارة جديدة"):
    arrow = "🟢 BUY" if side == "BUY" else "🔴 SELL"
    lines = [f"📊 <b>{header}</b> — <b>{name}</b>",
             f"{arrow}",
             f"🎯 Entry: <b>{entry:.5f}</b>",
             f"⛔ SL: <b>{sl:.5f}</b>"]
    for i, tp in enumerate(tps, start=1):
        lines.append(f"✅ TP{i}: <b>{tp:.5f}</b>")
    if price is not None:
        lines.append(f"💰 Price now: <b>{price:.5f}</b>")
    lines += ["—", "⚠️ للتعليم فقط، ليست نصيحة استثمارية."]
    return "\n".join(lines)

# ---------- تخزين الصفقات المفتوحة (في الذاكرة) ----------
# ملاحظة: تُفقد عند إعادة التشغيل. لاحقاً ممكن نستخدم DB مجانية.
open_trades = []  # كل عنصر: dict {name, ticker, side, entry, sl, tps, activated, next_tp_idx, chat_id}

def add_trade(name, ticker, side, entry, sl, tps, chat_id):
    trade = {
        "name": name,
        "ticker": ticker,
        "side": side,          # BUY / SELL
        "entry": float(entry),
        "sl": float(sl),
        "tps": [float(x) for x in tps],
        "activated": False,    # تتفعل عندما يلمس السعر نقطة الدخول
        "next_tp_idx": 0,      # التالي المراد فحصه
        "chat_id": chat_id
    }
    open_trades.append(trade)

# ---------- توليد إشارة تلقائية بسيطة ----------
def generate_auto_signal(nice_name, ticker):
    # شموع 5 دقائق (سكالب)
    df = yf.download(tickers=ticker, period="2d", interval="5m", progress=False)
    if df is None or df.empty or len(df) < 60:
        return None
    df = df.dropna()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["RSI14"] = rsi(df["Close"], 14)
    df["ATR14"] = atr(df, 14)

    last = df.iloc[-1]
    price = float(last["Close"]); sma50 = float(last["SMA50"]); rsi14 = float(last["RSI14"]); atr14 = float(last["ATR14"])

    if price > sma50 and rsi14 < 40:
        side = "BUY"
        entry = price
        sl = price - atr14 * 1.5
        tps = [price + atr14 * 1.0, price + atr14 * 2.0, price + atr14 * 3.0]
    elif price < sma50 and rsi14 > 60:
        side = "SELL"
        entry = price
        sl = price + atr14 * 1.5
        tps = [price - atr14 * 1.0, price - atr14 * 2.0, price - atr14 * 3.0]
    else:
        return None

    return side, entry, sl, tps, price

def push_all_signals():
    if not TARGET_CHAT_ID:
        return
    for nice, tick in SYMBOLS.items():
        try:
            sig = generate_auto_signal(nice, tick)
            if not sig:
                continue
            side, entry, sl, tps, price = sig
            # أرسل الكرت وأضفها للمراقبة
            bot.send_message(TARGET_CHAT_ID, build_card(nice, side, entry, sl, tps, price))
            add_trade(nice, tick, side, entry, sl, tps, TARGET_CHAT_ID)
            time.sleep(1.2)
        except Exception as e:
            if ADMIN_ID:
                bot.send_message(ADMIN_ID, f"⚠️ Auto signal error {nice}: {e}")

# ---------- مراقبة الصفقات ----------
def check_trades():
    if not open_trades:
        return
    # نجمع كل التيكرز المطلوبة لنتيح طلبات أقل
    needed = {}
    for t in open_trades:
        needed.setdefault(t["ticker"], None)
    # جلب آخر أسعار
    for tick in list(needed.keys()):
        try:
            needed[tick] = yahoo_price(tick)
        except Exception:
            needed[tick] = None

    # فحص كل صفقة
    for trade in open_trades[:]:
        price = needed.get(trade["ticker"])
        if price is None:
            continue

        name, side = trade["name"], trade["side"]
        entry, sl = trade["entry"], trade["sl"]
        tps = trade["tps"]
        chat = trade["chat_id"]

        # تفعيل الصفقة عند لمس الدخول بالاتجاه الصحيح
        if not trade["activated"]:
            if (side == "BUY" and price >= entry) or (side == "SELL" and price <= entry):
                trade["activated"] = True
                bot.send_message(chat, build_card(name, side, entry, sl, tps, price, header="تم تفعيل الصفقة"))
            # لم تتفعل بعد — نكمل
            continue

        # فحص وقف الخسارة
        if (side == "BUY" and price <= sl) or (side == "SELL" and price >= sl):
            bot.send_message(chat, f"❌ <b>{name}</b> — الصفقة أُغلِقَت على وقف الخسارة.\n💰 Price: <b>{price:.5f}</b>")
            open_trades.remove(trade)
            continue

        # فحص الأهداف بالتتابع
        idx = trade["next_tp_idx"]
        if idx < len(tps):
            target = tps[idx]
            hit = (side == "BUY" and price >= target) or (side == "SELL" and price <= target)
            if hit:
                bot.send_message(chat, f"✅ <b>{name}</b> — تحقق الهدف TP{idx+1} عند <b>{target:.5f}</b>\n💰 Price: <b>{price:.5f}</b>")
                trade["next_tp_idx"] += 1
                # إذا وصل آخر هدف، أنهِ الصفقة
                if trade["next_tp_idx"] >= len(tps):
                    bot.send_message(chat, f"🎉 <b>{name}</b> — كل الأهداف تحققت. تم إغلاق الصفقة.")
                    open_trades.remove(trade)

# جدولة: إشارات تلقائية + مراقبة الصفقات
scheduler.add_job(push_all_signals, "interval", minutes=INTERVAL_MIN, next_run_time=None)
scheduler.add_job(check_trades, "interval", minutes=1, next_run_time=None)
scheduler.start()

# ============== أوامر تيليجرام ==============
@bot.message_handler(commands=["start"])
def start_cmd(m: Message):
    bot.reply_to(m,
        "✅ البوت شغّال.\n"
        "• يرسل إشارات تلقائية للأصول المحددة.\n"
        "• ويتابع الصفقة: تفعيل/أهداف/ستوب.\n\n"
        "أوامر:\n"
        "• /now — إرسال الإشارات الآن يدويًا\n"
        "• /signal — إضافة صفقة يدويًا (BUY/SELL)\n"
        "• /list — عرض الصفقات المفتوحة\n"
        "• /id — رقم المحادثة")

@bot.message_handler(commands=["id"])
def id_cmd(m: Message):
    bot.reply_to(m, f"🪪 <code>{m.chat.id}</code>")

@bot.message_handler(commands=["now"])
def now_cmd(m: Message):
    if ADMIN_ID and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ للمشرف فقط.")
        return
    bot.reply_to(m, "⏱️ جاري توليد الإشارات…")
    push_all_signals()

@bot.message_handler(commands=["list"])
def list_cmd(m: Message):
    if not open_trades:
        bot.reply_to(m, "لا توجد صفقات مفتوحة حالياً.")
        return
    lines = []
    for t in open_trades:
        state = "نشطة" if t["activated"] else "معلّقة"
        nxt = t["next_tp_idx"]+1 if t["next_tp_idx"] < len(t["tps"]) else "—"
        lines.append(f"• {t['name']} {t['side']} | Entry {t['entry']} | SL {t['sl']} | Next TP {nxt} | {state}")
    bot.reply_to(m, "\n".join(lines))

def parse_manual_signal(text):
    # مثال:
    # /signal BUY GOLD 1900 SL 1890 TP1 1910 TP2 1920 TP3 1930
    parts = text.split()
    if len(parts) < 6:
        return None
    side = parts[1].upper()
    if side not in ("BUY","SELL"):
        return None
    name = parts[2].upper()
    entry = float(parts[3])
    sl = None
    tps = []
    i = 4
    while i < len(parts):
        p = parts[i].upper()
        if p == "SL":
            sl = float(parts[i+1]); i += 2
        elif p.startswith("TP"):
            tps.append(float(parts[i+1])); i += 2
        else:
            i += 1
    if sl is None or not tps:
        return None
    # تحويل الاسم الودي إلى تيكر
    ticker = SYMBOLS.get(name, None)
    if ticker is None:
        return None
    return name, ticker, side, entry, sl, tps

@bot.message_handler(commands=["signal"])
def manual_signal_cmd(m: Message):
    if ADMIN_ID and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ للمشرف فقط.")
        return
    parsed = parse_manual_signal(m.text)
    if not parsed:
        bot.reply_to(m, "❌ صيغة غير صحيحة.\nمثال:\n/signal BUY GOLD 1900 SL 1890 TP1 1910 TP2 1920")
        return
    name, ticker, side, entry, sl, tps = parsed
    bot.send_message(m.chat.id, build_card(name, side, entry, sl, tps))
    add_trade(name, ticker, side, entry, sl, tps, m.chat.id)

# تشغيل مستمر
bot.infinity_polling(timeout=60, long_polling_timeout=60)