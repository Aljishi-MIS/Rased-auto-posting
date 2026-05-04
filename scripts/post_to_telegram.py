import os
import json
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# تحميل البيانات
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# تجهيز الكابشن
caption = f"""📊 {data['stock_name']} — {data['symbol']}

📍 السعر الحالي: {data['price']} ريال
🎯 نقطة الدخول: {data['entry']} ريال
✅ الهدف الأول: {data['target1']} ريال
🛑 وقف الخسارة: {data['stop_loss']} ريال
📈 الزخم: {data['momentum']}

⚠️ محتوى تعليمي فقط وليس توصية استثمارية
"""

# إرسال الصورة
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

with open("output.png", "rb") as photo:
    files = {"photo": photo}
    data_payload = {
        "chat_id": CHAT_ID,
        "caption": caption
    }

    res = requests.post(url, data=data_payload, files=files)

print(res.text)
