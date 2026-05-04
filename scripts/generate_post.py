import json
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper


def ar(text):
    if not text:
        return ""
    return arabic_reshaper.reshape(str(text))


# تحميل البيانات
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# إعداد الصورة
width, height = 1080, 1080
img = Image.new("RGB", (width, height), "#0D1117")
draw = ImageDraw.Draw(img)


# تحميل الخط
font_path = "assets/Tajawal-Bold.ttf"

font_title = ImageFont.truetype(font_path, 78)
font_stock = ImageFont.truetype(font_path, 60)
font_text = ImageFont.truetype(font_path, 44)
font_note = ImageFont.truetype(font_path, 34)
font_footer = ImageFont.truetype(font_path, 28)


# الألوان
gold = "#F0B429"
green = "#22C55E"
red = "#EF4444"
white = "#FFFFFF"
gray = "#9CA3AF"
dark_card = "#111827"
border = "#2D3748"


# الخلفية (كرت)
draw.rounded_rectangle(
    (70, 70, 1010, 1010),
    radius=40,
    fill=dark_card,
    outline=border,
    width=3
)


# العنوان
draw.text((540, 150), ar(data["brand"]), fill=gold, font=font_title, anchor="mm")
draw.text((540, 220), ar("تحليل الأسهم السعودية"), fill=white, font=font_note, anchor="mm")


# خط فاصل
draw.line((200, 280, 880, 280), fill=gold, width=3)


# اسم السهم (بدون bidi)
stock_name = ar(data["stock_name"])
symbol = data["symbol"]

draw.text((540, 350), f"{stock_name} - {symbol}", fill=white, font=font_stock, anchor="mm")


# البيانات
y = 450

rows = [
    ("السعر الحالي", data["price"], white),
    ("نقطة الدخول", data["entry"], gold),
    ("الهدف الأول", data["target1"], green),
    ("الهدف الثاني", data["target2"], green),
    ("وقف الخسارة", data["stop_loss"], red),
    ("الزخم", data["momentum"], white),
]


for label, value, color in rows:
    label_ar = ar(label)

    if str(value).replace(".", "").isdigit():
        text = f"{label_ar} : {value} ريال"
    else:
        text = f"{label_ar} : {value}"

    draw.text((540, y), text, fill=color, font=font_text, anchor="mm")
    y += 70


# صندوق الملاحظة
draw.rounded_rectangle(
    (130, 820, 950, 910),
    radius=25,
    fill="#0B0F19",
    outline=border,
    width=2
)

note = ar(data["note"])
draw.text((540, 865), note, fill=gray, font=font_note, anchor="mm")


# الفوتر
footer = ar("⚠️ محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية")
draw.text((540, 960), footer, fill=gray, font=font_footer, anchor="mm")


# حفظ الصورة
img.save("output.png", quality=95)

print("Final clean Arabic post generated successfully.")
