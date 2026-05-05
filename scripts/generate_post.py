import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter


with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


W, H = 1080, 1080

BG = "#07101B"
CARD = "#0B1624"
ROW = "#0D1B2A"
GOLD = "#F0B429"
GREEN = "#22C55E"
RED = "#EF4444"
WHITE = "#FFFFFF"
BORDER = "#D99A00"
MUTED = "#CBD5E1"

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


font_path = "assets/Cairo-Bold.ttf"

font_brand = ImageFont.truetype(font_path, 58)
font_sub = ImageFont.truetype(font_path, 30)
font_stock = ImageFont.truetype(font_path, 58)

font_label = ImageFont.truetype(font_path, 30)
font_value = ImageFont.truetype(font_path, 32)

# تم التصغير هنا
font_note = ImageFont.truetype(font_path, 19)
font_footer = ImageFont.truetype(font_path, 21)
font_link = ImageFont.truetype(font_path, 25)


def text_center(x, y, text, font, color):
    draw.text(
        (x, y),
        str(text),
        fill=color,
        font=font,
        anchor="mm",
        direction="rtl",
        language="ar",
    )


def text_right(x, y, text, font, color):
    draw.text(
        (x, y),
        str(text),
        fill=color,
        font=font,
        anchor="rm",
        direction="rtl",
        language="ar",
    )


def text_left(x, y, text, font, color):
    draw.text(
        (x, y),
        str(text),
        fill=color,
        font=font,
        anchor="lm",
        direction="rtl",
        language="ar",
    )


def paste_logo():
    try:
        logo = Image.open("assets/logo.png").convert("RGBA")
        logo = logo.resize((108, 108))

        mask = Image.new("L", (108, 108), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 108, 108), fill=255)

        img.paste(logo, (486, 78), mask)
    except Exception:
        pass


def draw_icon(cx, cy, kind, color):
    draw.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=color, width=3)

    if kind == "price":
        draw.rectangle((cx - 12, cy + 5, cx - 6, cy + 16), fill=WHITE)
        draw.rectangle((cx - 2, cy - 2, cx + 4, cy + 16), fill=WHITE)
        draw.rectangle((cx + 8, cy - 12, cx + 14, cy + 16), fill=WHITE)

    elif kind == "target":
        draw.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), outline=color, width=3)
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=color)
        draw.line((cx + 7, cy - 7, cx + 18, cy - 18), fill=color, width=4)

    elif kind == "stop":
        draw.polygon(
            [
                (cx, cy - 18),
                (cx + 16, cy - 7),
                (cx + 12, cy + 14),
                (cx, cy + 21),
                (cx - 12, cy + 14),
                (cx - 16, cy - 7),
            ],
            outline=color,
        )
        draw.line((cx - 7, cy - 7, cx + 7, cy + 7), fill=color, width=4)
        draw.line((cx + 7, cy - 7, cx - 7, cy + 7), fill=color, width=4)


# Glow
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse((260, -180, 820, 330), fill=(240, 180, 41, 38))
glow = glow.filter(ImageFilter.GaussianBlur(75))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img)


# Frame
draw.rounded_rectangle(
    (110, 45, 970, 1035),
    radius=46,
    fill=CARD,
    outline=BORDER,
    width=3,
)

paste_logo()


# Header
text_center(540, 215, "مضارب", font_brand, GOLD)
text_center(540, 275, "تحليل فني وتعليمي لسوق الأسهم السعودية", font_sub, WHITE)

draw.line((250, 335, 830, 335), fill=BORDER, width=2)
draw.ellipse((532, 331, 548, 347), fill=GOLD)


# Stock
stock_name = data.get("stock_name", "")
symbol = data.get("symbol", "")
text_center(540, 395, f"{stock_name} - {symbol}", font_stock, WHITE)


# Rows
rows = [
    ("السعر الحالي", data.get("price", ""), WHITE, "price"),
    ("نقطة الدخول", data.get("entry", ""), GOLD, "target"),
    ("الهدف الأول", data.get("target1", ""), GREEN, "target"),
    ("الهدف الثاني", data.get("target2", ""), GREEN, "target"),
    ("وقف الخسارة", data.get("stop_loss", ""), RED, "stop"),
]

y = 480

for label, value, color, icon in rows:
    draw.rounded_rectangle(
        (210, y - 33, 870, y + 33),
        radius=18,
        fill=ROW,
        outline="#6B7280",
        width=2,
    )

    draw_icon(835, y, icon, color)
    text_right(760, y, f"{label}:", font_label, color)
    text_left(300, y, f"{value} ريال", font_value, color)

    y += 72


# Note
draw.rounded_rectangle(
    (175, 850, 905, 925),
    radius=18,
    fill="#07111E",
    outline=GOLD,
    width=3,
)

note = data.get(
    "note",
    "قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة."
)

text_center(
    540,
    885,
    note,
    font_note,
    WHITE,
)


# Footer
draw.line((250, 955, 830, 955), fill=BORDER, width=2)
draw.ellipse((532, 950, 548, 966), fill=GOLD)

text_center(
    540,
    985,
    "محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية",
    font_footer,
    MUTED,
)

draw.rounded_rectangle(
    (390, 1010, 690, 1055),
    radius=22,
    fill="#0B1624",
    outline=GOLD,
    width=2,
)

text_center(540, 1032, "t.me/TASI_Smart", font_link, GOLD)


img.save("output.png", quality=95)
print("Final Modareb post generated successfully.")
