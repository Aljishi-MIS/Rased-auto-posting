import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# Load data
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# Canvas
W, H = 1080, 1080

BG = "#07101B"
CARD = "#0B1624"
ROW = "#0D1B2A"
GOLD = "#F0B429"
GREEN = "#22C55E"
RED = "#EF4444"
WHITE = "#FFFFFF"
GRAY = "#CBD5E1"
MUTED = "#94A3B8"
BORDER = "#D99A00"

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


# Fonts
font_path = "assets/Cairo-Bold.ttf"

font_brand = ImageFont.truetype(font_path, 58)
font_sub = ImageFont.truetype(font_path, 30)
font_stock = ImageFont.truetype(font_path, 58)
font_row = ImageFont.truetype(font_path, 34)
font_note = ImageFont.truetype(font_path, 28)
font_footer = ImageFont.truetype(font_path, 25)
font_link = ImageFont.truetype(font_path, 27)


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


def text_left(x, y, text, font, color):
    draw.text(
        (x, y),
        str(text),
        fill=color,
        font=font,
        anchor="lm",
        direction="rtl",
        language="ar"
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
    # circle
    draw.ellipse((cx - 31, cy - 31, cx + 31, cy + 31), outline=color, width=3)

    if kind == "price":
        draw.rectangle((cx - 14, cy + 5, cx - 7, cy + 18), fill=WHITE)
        draw.rectangle((cx - 3, cy - 3, cx + 4, cy + 18), fill=WHITE)
        draw.rectangle((cx + 8, cy - 14, cx + 15, cy + 18), fill=WHITE)

    elif kind == "target":
        draw.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), outline=color, width=3)
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color)
        draw.line((cx + 8, cy - 8, cx + 22, cy - 22), fill=color, width=4)

    elif kind == "stop":
        draw.polygon(
            [(cx, cy - 20), (cx + 18, cy - 8), (cx + 14, cy + 16),
             (cx, cy + 24), (cx - 14, cy + 16), (cx - 18, cy - 8)],
            outline=color
        )
        draw.line((cx - 8, cy - 8, cx + 8, cy + 8), fill=color, width=4)
        draw.line((cx + 8, cy - 8, cx - 8, cy + 8), fill=color, width=4)

    elif kind == "momentum":
        draw.line((cx - 12, cy + 14, cx - 2, cy - 2, cx + 6, cy + 6, cx + 16, cy - 16), fill=color, width=4)

    elif kind == "note":
        draw.rectangle((cx - 13, cy - 17, cx + 13, cy + 17), outline=color, width=3)
        draw.line((cx - 8, cy - 5, cx + 8, cy - 5), fill=color, width=2)
        draw.line((cx - 8, cy + 4, cx + 8, cy + 4), fill=color, width=2)


# Glow
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse((260, -180, 820, 330), fill=(240, 180, 41, 38))
glow = glow.filter(ImageFilter.GaussianBlur(75))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img)


# Main frame
draw.rounded_rectangle(
    (110, 45, 970, 1035),
    radius=46,
    fill=CARD,
    outline=BORDER,
    width=3
)

paste_logo()


# Header
text_center(540, 215, "مضارب", font_brand, GOLD)
text_center(540, 275, "تحليل فني وتعليمي لسوق الأسهم السعودية", font_sub, WHITE)

draw.line((250, 335, 830, 335), fill=BORDER, width=2)
draw.ellipse((532, 331, 548, 347), fill=GOLD)


# Stock title
stock_name = data.get("stock_name", "")
symbol = data.get("symbol", "")

draw.line((245, 395, 375, 395), fill=GOLD, width=2)
draw.line((705, 395, 835, 395), fill=GOLD, width=2)
draw.ellipse((372, 390, 382, 400), fill=GOLD)
draw.ellipse((698, 390, 708, 400), fill=GOLD)

text_center(540, 395, f"{stock_name} - {symbol}", font_stock, WHITE)


# Rows layout
rows = [
    ("السعر الحالي", f"{data.get('price', '')} ريال", WHITE, "price"),
    ("نقطة الدخول", f"{data.get('entry', '')} ريال", GOLD, "target"),
    ("الهدف الأول", f"{data.get('target1', '')} ريال", GREEN, "target"),
    ("الهدف الثاني", f"{data.get('target2', '')} ريال", GREEN, "target"),
    ("وقف الخسارة", f"{data.get('stop_loss', '')} ريال", RED, "stop"),
    ("الزخم", data.get("momentum", ""), WHITE, "momentum"),
]

y = 480

for label, value, color, icon in rows:
    draw.rounded_rectangle(
        (210, y - 33, 870, y + 33),
        radius=18,
        fill=ROW,
        outline="#6B7280",
        width=2
    )

    draw_icon(835, y, icon, color)

    text_right(760, y, f"{label}:", font_row, color if color != WHITE else WHITE)
    text_left(295, y, value, font_row, color)

    y += 72


# Note box
draw.rounded_rectangle(
    (175, 850, 905, 925),
    radius=18,
    fill="#07111E",
    outline=GOLD,
    width=3
)

draw_icon(855, 887, "note", GOLD)
text_center(
    510,
    887,
    data.get("note", "قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة."),
    font_note,
    WHITE
)


# Footer separator
draw.line((250, 955, 830, 955), fill=BORDER, width=2)
draw.ellipse((532, 950, 548, 966), fill=GOLD)

text_center(540, 985, "محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية", font_footer, WHITE)

# Telegram link pill
draw.rounded_rectangle(
    (390, 1010, 690, 1055),
    radius=22,
    fill="#0B1624",
    outline=GOLD,
    width=2
)
draw.text((540, 1032), "t.me/TASI_Smart", fill=GOLD, font=font_link, anchor="mm")


# Save
img.save("output.png", quality=95)
print("Premium Modareb post generated successfully.")
