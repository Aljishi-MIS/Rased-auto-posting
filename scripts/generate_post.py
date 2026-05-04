import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper


def ar(text):
    if not text:
        return ""
    return arabic_reshaper.reshape(str(text))


def paste_logo(base_img, logo_path, position, size):
    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((size, size))

        # دائرة ناعمة للشعار
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)

        base_img.paste(logo, position, mask)
    except Exception:
        pass


# Load data
with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)


# Canvas
width, height = 1080, 1080
img = Image.new("RGB", (width, height), "#0D1117")
draw = ImageDraw.Draw(img)


# Fonts
font_path = "assets/Tajawal-Bold.ttf"

font_brand = ImageFont.truetype(font_path, 70)
font_subtitle = ImageFont.truetype(font_path, 31)
font_stock = ImageFont.truetype(font_path, 56)
font_text = ImageFont.truetype(font_path, 41)
font_note = ImageFont.truetype(font_path, 31)
font_footer = ImageFont.truetype(font_path, 27)


# Colors
gold = "#F0B429"
green = "#22C55E"
red = "#EF4444"
white = "#FFFFFF"
gray = "#A3AAB8"
dark_card = "#111827"
inner_card = "#0B0F19"
border = "#334155"


# Soft background glow
glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)
glow_draw.ellipse((260, -180, 820, 360), fill=(240, 180, 41, 35))
glow = glow.filter(ImageFilter.GaussianBlur(70))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
draw = ImageDraw.Draw(img)


# Main card
draw.rounded_rectangle(
    (65, 65, 1015, 1015),
    radius=45,
    fill=dark_card,
    outline=border,
    width=3
)


# Logo
paste_logo(img, "assets/logo.png", (465, 88), 150)
draw = ImageDraw.Draw(img)


# Header text
draw.text((540, 270), ar(data.get("brand", "مضارب")), fill=gold, font=font_brand, anchor="mm")
draw.text((540, 325), ar("تحليل فني وتعليمي لسوق الأسهم السعودية"), fill=white, font=font_subtitle, anchor="mm")


# Gold separator
draw.line((190, 380, 890, 380), fill=gold, width=4)


# Stock title
stock_name = ar(data.get("stock_name", ""))
symbol = data.get("symbol", "")
draw.text((540, 450), f"{symbol} - {stock_name}", fill=white, font=font_stock, anchor="mm")


# Data rows with rounded backgrounds
rows = [
    ("السعر الحالي", data.get("price", ""), white),
    ("نقطة الدخول", data.get("entry", ""), gold),
    ("الهدف الأول", data.get("target1", ""), green),
    ("الهدف الثاني", data.get("target2", ""), green),
    ("وقف الخسارة", data.get("stop_loss", ""), red),
    ("الزخم", data.get("momentum", ""), white),
]

y = 535

for label, value, color in rows:
    label_ar = ar(label)

    if str(value).replace(".", "").isdigit():
        text = f"{label_ar} : {value} ريال"
    else:
        text = f"{label_ar} : {value}"

    draw.rounded_rectangle(
        (180, y - 34, 900, y + 34),
        radius=18,
        fill="#0F172A",
        outline="#1F2937",
        width=1
    )

    draw.text((540, y), text, fill=color, font=font_text, anchor="mm")
    y += 72


# Note box
note_box = (120, 835, 960, 920)
draw.rounded_rectangle(
    note_box,
    radius=25,
    fill=inner_card,
    outline=border,
    width=2
)

note = ar(data.get("note", ""))
draw.text((540, 878), note, fill=gray, font=font_note, anchor="mm")


# Footer
footer = ar("⚠️ محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية")
draw.text((540, 965), footer, fill=gray, font=font_footer, anchor="mm")


# Small brand mark
draw.text((540, 1005), "t.me/TASI_Smart", fill="#64748B", font=font_footer, anchor="mm")


# Save
img.save("output.png", quality=95)

print("Premium Modareb post generated successfully.")
