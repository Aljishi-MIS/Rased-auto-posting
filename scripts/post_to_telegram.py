import requests
import os
import json

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")

with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


def pct(base, target):
    try:
        b = float(base)
        t = float(target)
        if b > 0:
            return f"({((t-b)/b*100):+.1f}%)"
    except Exception:
        pass
    return ""


stock_name     = data.get("stock_name",        "")
symbol         = data.get("symbol",            "")
price          = data.get("price",             "")
entry          = data.get("entry",             "")
target1        = data.get("target1",           "")
target2        = data.get("target2",           "")
stop_loss      = data.get("stop_loss",         "")
momentum       = data.get("momentum",          "")
note           = data.get("note",              "")
score          = data.get("score",             "")
rs_rank        = data.get("rs_rank",           "")
sector         = data.get("sector",            "")
generated      = data.get("generated_at",      "")
claude_note    = data.get("claude_note",       "")
claude_warning = data.get("claude_warning",    "")
claude_conf    = data.get("claude_confidence", "")
news_sentiment = data.get("news_sentiment",    "neutral")
news_summary   = data.get("news_summary",      "")
target2_pct    = data.get("target2_pct",       10.0)
expected_days  = data.get("expected_days",     7)
max_days       = data.get("max_days",          10)
acceleration   = data.get("acceleration",      0)
signal_type    = data.get("type",              "")

pct_entry = pct(price,  entry)
pct_t1    = pct(entry,  target1)
pct_t2    = pct(entry,  target2)
pct_stop  = pct(entry,  stop_loss)

# رابط سجل الأداء
TRACK_URL = "https://aljishi.github.io/modareb-auto-posting/"

# نوع الإشارة
is_golden    = signal_type == "اشارة ذهبية"
signal_emoji = "⭐" if is_golden else "📊"
signal_label = "إشارة ذهبية — مضارب" if is_golden else "اشارة اليوم — مضارب"

# قسم الإطار الزمني
time_section = f"\n⏱ الإطار الزمني: *{expected_days}-{max_days} أيام* (هدف {target2_pct:.0f}%)"

# قسم التسارع
accel_section = ""
if acceleration >= 30:
    accel_section = f"\n🚀 *تسارع قوي* — {acceleration}/50"
elif acceleration >= 15:
    accel_section = f"\n📊 *تسارع متوسط* — {acceleration}/50"

# قسم الأخبار
news_section = ""
if news_summary:
    news_emoji = "✅" if news_sentiment == "positive" else "❌" if news_sentiment == "negative" else "➖"
    news_section = f"\n{news_emoji} *الاخبار:* {news_summary}"

# قسم Claude
claude_section = ""
if claude_note:
    claude_section += f"\n🤖 *تحليل Claude:* {claude_note}"
if claude_warning:
    claude_section += f"\n⚠️ *تنبيه:* {claude_warning}"
if claude_conf:
    conf_emoji = "🟢" if claude_conf == "عالية" else "🟡" if claude_conf == "متوسطة" else "🔴"
    claude_section += f"\n{conf_emoji} *الثقة:* {claude_conf}"

caption = f"""
{signal_emoji} *{signal_label}*

📊 *{stock_name} — {symbol}*
🏢 القطاع: {sector if sector else "—"}

💰 السعر الحالي: *{price} ريال*
🎯 نقطة الدخول: *{entry} ريال* {pct_entry}

🟢 الهدف الاول:  *{target1} ريال* {pct_t1}
🟢 الهدف الثاني: *{target2} ريال* {pct_t2}

🔴 وقف الخسارة: *{stop_loss} ريال* {pct_stop}
{time_section}{accel_section}

⚡ الزخم: *{momentum}*
📈 RS Rank: *{rs_rank}*
🔢 Score: *{score}*

📌 {note}{news_section}{claude_section}

🕐 {generated}

⚠️ _محتوى تعليمي وتحليلي فقط — لا يعد توصية استثمارية_
📈 [سجل الأداء]({TRACK_URL})
""".strip()

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

with open("output.png", "rb") as photo:
    response = requests.post(
        url,
        data={
            "chat_id":    CHAT_ID,
            "caption":    caption,
            "parse_mode": "Markdown"
        },
        files={"photo": photo},
        timeout=30
    )

result = response.json()
print("Telegram response:", result)

if not result.get("ok"):
    raise RuntimeError(f"Telegram failed: {result}")

print("Telegram post sent successfully")
