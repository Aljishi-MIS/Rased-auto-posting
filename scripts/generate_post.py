import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap


# Load data
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# Canvas
W, H = 1080, 1080

BG = "#0D1117"
CARD = "#111827"
ROW = "#0F172A"
GOLD = "#F0B429"
GREEN = "#22C55E"
RED = "#EF4444"
WHITE = "#FFFFFF"
GRAY = "#A3AAB8"
BORDER = "#334155"

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


# Fonts
font_path = "assets/Cairo-Bold.ttf"

font_brand = ImageFont.truetype(font_path, 76)
font_sub = ImageFont.truetype(font_path, 30)
font_stock = ImageFont.truetype(font_path, 56)
font_row = ImageFont.truetype(font_path, 36)
font_note = ImageFont.truetype(font_path, 30)
font_footer = ImageFont.truetype(font_path, 25)


def text_center(x, y, text, font, color):
    draw.text(
        (x, y),
        str(text),
        fill=color,
        font=font,
        anchor="mm",
        direction="rtl",
        language="ar"
    )


def text_right(x, y, text, font, color):
    draw.text(
        (x, y),
        str(text),
        fill=color,
        font=font,
        anchor="rm",
        direction="rtl",
        language="ar"
    )


def paste_logo():
    try:
        logo = Image.open("assets/logo.png").convert("RGBA")
        logo = logo.resize((118, 118))

        mask = Image.new("L", (118, 118), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 118, 118), fill=255)

        img.paste(logo, (481, 88), mask)
    except:
        pass


# Glow
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse((280, -160, 800, 340), fill=(240, 180, 41, 35))
glow = glow.filter(ImageFilter.GaussianBlur(70))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img)


# Card
draw.rounded_rectangle(
    (65, 65, 1015, 1015),
    radius=44,
    fill=CARD,
    outline=BORDER,
    width=3
)

paste_logo()


# Header
text_center(540, 245, "مضارب", font_brand, GOLD)

# مسافة أكبر بين مضارب والوصف
text_center(540, 325, "تحليل فني وتعليمي لسوق الأسهم السعودية", font_sub, WHITE)

draw.line((190, 380, 890, 380), fill=GOLD, width=4)


# Stock
text_right(900, 445, f"{data['stock_name']} - {data['symbol']}", font_stock, WHITE)


# Rows
rows = [
    ("السعر الحالي", f"{data.get('price', '')} ريال", WHITE),
    ("نقطة الدخول", f"{data.get('entry', '')} ريال", GOLD),
    ("الهدف الأول", f"{data.get('target1', '')} ريال", GREEN),
    ("الهدف الثاني", f"{data.get('target2', '')} ريال", GREEN),
    ("وقف الخسارة", f"{data.get('stop_loss', '')} ريال", RED),
]

y = 515

for label, value, color in rows:
    draw.rounded_rectangle(
        (175, y - 28, 905, y + 28),
        radius=16,
        fill=ROW,
        outline="#1F2937",
        width=1
    )

    text_right(880, y, f"{label}: {value}", font_row, color)
    y += 60


# Note
note = data.get("note", "")
wrapped_note = textwrap.fill(note, width=30)

draw.rounded_rectangle(
    (120, 795, 960, 895),
    radius=26,
    fill="#0B0F19",
    outline=BORDER,
    width=2
)

text_center(540, 845, wrapped_note, font_note, GRAY)


# Footer
text_center(
    540,
    940,
    "محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية",
    font_footer,
    GRAY
)

draw.text(
    (540, 985),
    "t.me/TASI_Smart",
    fill="#64748B",
    font=font_footer,
    anchor="mm"
)


# Save
img.save("output.png", quality=95)
print("Premium Arabic post generated successfully.")
