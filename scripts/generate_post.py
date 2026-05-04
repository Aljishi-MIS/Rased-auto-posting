import json
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# دالة لمعالجة العربية
def ar(text):
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

# تحميل البيانات
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# إعداد الصورة
width, height = 1080, 1080
img = Image.new("RGB", (width, height), "#0D1117")
draw = ImageDraw.Draw(img)

# تحميل الخط
font_title = ImageFont.truetype("assets/Tajawal-Bold.ttf", 70)
font_big = ImageFont.truetype("assets/Tajawal-Bold.ttf", 55)
font_small = ImageFont.truetype("assets/Tajawal-Bold.ttf", 40)

# ألوان
gold = "#F0B429"
green = "#22C55E"
red = "#EF4444"
white = "#FFFFFF"
gray = "#9CA3AF"

# العنوان
draw.text((540, 100), ar(data["brand"]), fill=gold, font=font_title, anchor="mm")

# اسم السهم
draw.text((540, 250), ar(f"{data['stock_name']} — {data['symbol']}"), fill=white, font=font_big, anchor="mm")

# خط فاصل
draw.line((200, 330, 880, 330), fill=gray, width=2)

# البيانات
y = 380

draw.text((540, y), ar(f"السعر الحالي: {data['price']} ريال"), fill=white, font=font_small, anchor="mm")
y += 80

draw.text((540, y), ar(f"نقطة الدخول: {data['entry']} ريال"), fill=gold, font=font_small, anchor="mm")
y += 80

draw.text((540, y), ar(f"الهدف: {data['target1']} ريال"), fill=green, font=font_small, anchor="mm")
y += 80

draw.text((540, y), ar(f"وقف الخسارة: {data['stop_loss']} ريال"), fill=red, font=font_small, anchor="mm")
y += 80

draw.text((540, y), ar(f"الزخم: {data['momentum']}"), fill=white, font=font_small, anchor="mm")
y += 100

# الملاحظة
draw.text((540, y), ar(data["note"]), fill=gray, font=font_small, anchor="mm")

# حفظ الصورة
img.save("output.png")

print("Arabic fixed successfully!")
