import json
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display


def ar(text):
    """Fix Arabic shaping and RTL display for PIL."""
    if text is None:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


# Load data
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# Image settings
width, height = 1080, 1080
bg = "#0D1117"

img = Image.new("RGB", (width, height), bg)
draw = ImageDraw.Draw(img)


# Fonts
font_path = "assets/Tajawal-Bold.ttf"

font_title = ImageFont.truetype(font_path, 78)
font_stock = ImageFont.truetype(font_path, 58)
font_text = ImageFont.truetype(font_path, 44)
font_note = ImageFont.truetype(font_path, 34)
font_footer = ImageFont.truetype(font_path, 28)


# Colors
gold = "#F0B429"
green = "#22C55E"
red = "#EF4444"
white = "#FFFFFF"
gray = "#9CA3AF"
dark_card = "#111827"
border = "#2D3748"


# Background card
draw.rounded_rectangle(
    (70, 70, 1010, 1010),
    radius=40,
    fill=dark_card,
    outline=border,
    width=3
)


# Header
draw.text((540, 145), ar(data.get("brand", "مضارب")), fill=gold, font=font_title, anchor="mm")
draw.text((540, 215), ar("تحليل الأسهم السعودية"), fill=white, font=font_note, anchor="mm")

# Separator
draw.line((180, 280, 900, 280), fill=gold, width=3)


# Stock title
stock_title = f"{data.get('stock_name', '')} — {data.get('symbol', '')}"
draw.text((540, 350), ar(stock_title), fill=white, font=font_stock, anchor="mm")


# Data rows
rows = [
    (f"السعر الحالي: {data.get('price', '')} ريال", white),
    (f"نقطة الدخول: {data.get('entry', '')} ريال", gold),
    (f"الهدف الأول: {data.get('target1', '')} ريال", green),
    (f"الهدف الثاني: {data.get('target2', '')} ريال", green),
    (f"وقف الخسارة: {data.get('stop_loss', '')} ريال", red),
    (f"الزخم: {data.get('momentum', '')}", white),
]

y = 445
for text, color in rows:
    draw.text((540, y), ar(text), fill=color, font=font_text, anchor="mm")
    y += 72


# Note box
note_box = (130, 820, 950, 910)
draw.rounded_rectangle(note_box, radius=25, fill="#0B0F19", outline=border, width=2)

note = data.get("note", "")
draw.text((540, 865), ar(note), fill=gray, font=font_note, anchor="mm")


# Footer disclaimer
footer = "⚠️ محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية"
draw.text((540, 955), ar(footer), fill=gray, font=font_footer, anchor="mm")


# Save
img.save("output.png", quality=95)
print("Professional Arabic post generated successfully.")
