import json
from PIL import Image, ImageDraw, ImageFont

# تحميل البيانات
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# إنشاء صورة
width, height = 1080, 1080
img = Image.new("RGB", (width, height), "#0D1117")
draw = ImageDraw.Draw(img)

# تحميل الخط (سنضيفه لاحقاً)
font_title = ImageFont.load_default()
font_text = ImageFont.load_default()

# كتابة النص
y = 150

draw.text((100, y), f"{data['stock_name']} — {data['symbol']}", fill="white", font=font_title)
y += 80

draw.text((100, y), f"السعر: {data['price']}", fill="white", font=font_text)
y += 60

draw.text((100, y), f"الدخول: {data['entry']}", fill="white", font=font_text)
y += 60

draw.text((100, y), f"الهدف: {data['target1']}", fill="green", font=font_text)
y += 60

draw.text((100, y), f"وقف الخسارة: {data['stop_loss']}", fill="red", font=font_text)
y += 60

draw.text((100, y), f"الزخم: {data['momentum']}", fill="white", font=font_text)
y += 80

draw.text((100, y), data["note"], fill="gray", font=font_text)

# حفظ الصورة
img.save("output.png")

print("Post image generated successfully!")
