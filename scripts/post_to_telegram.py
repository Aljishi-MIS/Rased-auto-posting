import requests
import os
import json

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")

# ── قراءة البيانات من daily.json ────────────────────────────
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

stock_name  = data.get("stock_name", "")
symbol      = data.get("symbol", "")
price       = data.get("price", "")
entry       = data.get("entry", "")
target1     = data.get("target1", "")
target2     = data.get("target2", "")
stop_loss   = data.get("stop_loss", "")
momentum    = data.get("momentum", "")
note        = data.get("note", "")
score       = data.get("score", "")
rs_rank     = data.get("rs_rank", "")
sector      = data.get("sector", "")
generated   = data.get("generated_at", "")

# ── بناء الكابشن من البيانات الحية ──────────────────────────
caption = f"""
*إشارة اليوم — مضارب*

📊 *{stock_name} — {symbol}*
🏢 القطاع: {sector if sector else "—"}

💰 السعر الحالي: *{price} ريال*
🎯 نقطة الدخول: *{entry} ريال*

🟢 الهدف الأول:  *{target1} ريال*
🟢 الهدف الثاني: *{target2} ريال*

🔴 وقف الخسارة: *{stop_loss} ريال*

⚡ الزخم: *{momentum}*
📈 RS Rank: *{rs_rank}*
🔢 Score: *{score}*

📌 {note}

🕐 {generated}

⚠️ _محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية_
"""

# ── إرسال الصورة مع الكابشن ─────────────────────────────────
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

with open("output.png", "rb") as photo:
    response = requests.post(
        url,
        data={
            "chat_id":    CHAT_ID,
            "caption":    caption.strip(),
            "parse_mode": "Markdown"
        },
        files={"photo": photo},
        timeout=30
    )

result = response.json()
print("Telegram response:", result)

if not result.get("ok"):
    raise RuntimeError(f"Telegram failed: {result}")

print("✅ Telegram post sent successfully")
