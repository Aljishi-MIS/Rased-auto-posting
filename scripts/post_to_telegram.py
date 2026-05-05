import requests
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

caption = """
🚀 *إشارة اليوم*

📊 *4030 - البحري*

💰 السعر الحالي: 31.90 ريال  
🎯 نقطة الدخول: 32.20 ريال  

🟢 الهدف الأول: 33.17 ريال  
🟢 الهدف الثاني: 34.13 ريال  

🔴 وقف الخسارة: 31.56 ريال  

⚡ الزخم: قوي

📌 قراءة فنية:
إغلاق إيجابي + زخم قوي + حجم تداول مرتفع

⚠️ *تعليمي فقط — ليس توصية استثمارية*
"""

with open("output.png", "rb") as photo:
    res = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "Markdown"
        },
        files={"photo": photo}
    )

print(res.json())