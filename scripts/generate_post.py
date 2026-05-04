import json
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display


def ar(text):
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


# تحميل البيانات
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# إعداد الصورة
W, H = 1080, 1080
img = Image.new("RGB", (W, H), "#0D1117")
draw = ImageDraw.Draw(img)


# 🔥 الخط الجديد (مهم)
font_path = "assets/Cairo-Bold.ttf"

font_brand = ImageFont.truetype(font_path, 70)
font_sub = ImageFont.truetype(font_path, 34)
font_stock = ImageFont.truetype(font_path, 60)
font_text = ImageFont.truetype(font_path, 44)
font_note = ImageFont.truetype(font_path, 32)
font_footer = ImageFont.truetype(font_path, 26)


# الألوان
gold = "#F0B429"
green = "#22C55E"
red = "#EF4444"
white = "#FFFFFF"
gray = "#94A3B8"


# Header
draw.text((540, 150), ar(data["brand"]), fill=gold, font=font_brand, anchor="mm")
draw.text((540, 210), ar("تحليل فني لسوق الأسهم السعودي"), fill=white, font=font_sub, anchor="mm")

draw.line((200, 260, 880, 260), fill=gold, width=3)


# Stock
stock = ar(data["stock_name"])
symbol = data["symbol"]

draw.text((540, 330), ar(f"{stock} - {symbol}"), fill=white, font=font_stock, anchor="mm")


# Rows
y = 430

rows = [
    ("السعر الحالي", data["price"], white),
    ("نقطة الدخول", data["entry"], gold),
    ("الهدف الأول", data["target1"], green),
    ("الهدف الثاني", data["target2"], green),
    ("وقف الخسارة", data["stop_loss"], red),
    ("الزخم", data["momentum"], white),
]

for label, value, color in rows:
    text = ar(f"{label} : {value} ريال")
    draw.text((540, y), text, fill=color, font=font_text, anchor="mm")
    y += 65


# Note
note = ar(data["note"])
draw.text((540, 850), note, fill=gray, font=font_note, anchor="mm")


# Footer
footer = ar("⚠️ محتوى تعليمي فقط — ليس توصية استثمارية")
draw.text((540, 950), footer, fill=gray, font=font_footer, anchor="mm")


# حفظ
img.save("output.png")
print("FINAL CLEAN OUTPUT READY")
