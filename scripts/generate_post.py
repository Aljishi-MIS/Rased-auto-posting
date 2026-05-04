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


# Fonts (👇 التعديل هنا)
font_path = "assets/Cairo-Bold.ttf"

font_brand = ImageFont.truetype(font_path, 58)
font_sub = ImageFont.truetype(font_path, 30)
font_stock = ImageFont.truetype(font_path, 58)

font_label = ImageFont.truetype(font_path, 30)   # النص (السعر الحالي…)
font_value = ImageFont.truetype(font_path, 32)   # 👈 الأرقام أصغر

font_note = ImageFont.truetype(font_path, 24)    # 👈 قراءة فنية أصغر
font_footer = ImageFont.truetype(font_path, 24)
font_link = ImageFont.truetype(font_path, 26)


def text_center(x, y, text, font, color):
    draw.text((x, y), str(text), fill=color, font=font,
              anchor="mm", direction="rtl", language="ar")


def text_right(x, y, text, font, color):
    draw.text((x, y), str(text), fill=color, font=font,
              anchor="rm", direction="rtl", language="ar")


def text_left(x, y, text, font, color):
    draw.text((x, y), str(text), fill=color, font=font,
              anchor="lm", direction="rtl", language="ar")


def paste_logo():
    try:
        logo = Image.open("assets/logo.png").convert("RGBA")
        logo = logo.resize((108, 108))

        mask = Image.new("L", (108, 108), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 108, 108), fill=255)

        img.paste(logo, (486, 78), mask)
    except:
        pass


# Glow
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse((260, -180, 820, 330), fill=(240, 180, 41, 38))
glow = glow.filter(ImageFilter.GaussianBlur(75))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img)


# Frame
draw.rounded_rectangle((110, 45, 970, 1035),
                       radius=46, fill=CARD, outline=BORDER, width=3)

paste_logo()


# Header
text_center(540, 215, "مضارب", font_brand, GOLD)
text_center(540, 275, "تحليل فني وتعليمي لسوق الأسهم السعودية", font_sub, WHITE)

draw.line((250, 335, 830, 335), fill=BORDER, width=2)
draw.ellipse((532, 331, 548, 347), fill=GOLD)


# Stock
text_center(540, 395, f"{data['stock_name']} - {data['symbol']}", font_stock, WHITE)


# Rows
rows = [
    ("السعر الحالي", data['price'], WHITE),
    ("نقطة الدخول", data['entry'], GOLD),
    ("الهدف الأول", data['target1'], GREEN),
    ("الهدف الثاني", data['target2'], GREEN),
    ("وقف الخسارة", data['stop_loss'], RED),
]

y = 480

for label, value, color in rows:
    draw.rounded_rectangle((210, y - 33, 870, y + 33),
                           radius=18, fill=ROW, outline="#6B7280", width=2)

    # النص يمين
    text_right(760, y, f"{label}:", font_label, color if color != WHITE else WHITE)

    # 👈 الأرقام يسار (أصغر)
    text_left(300, y, f"{value} ريال", font_value, color)

    y += 72


# Note
draw.rounded_rectangle((175, 850, 905, 925),
                       radius=18, fill="#07111E", outline=GOLD, width=3)

text_center(
    540,
    885,
    data.get("note", "قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة."),
    font_note,
    WHITE
)


# Footer
draw.line((250, 955, 830, 955), fill=BORDER, width=2)
draw.ellipse((532, 950, 548, 966), fill=GOLD)

text_center(540, 985,
            "محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية",
            font_footer,
            WHITE)

# Link
draw.rounded_rectangle((390, 1010, 690, 1055),
                       radius=22, fill="#0B1624", outline=GOLD, width=2)

text_center(540, 1032, "t.me/TASI_Smart", font_link, GOLD)


# Save
img.save("output.png", quality=95)

print("Final refined version ready")
