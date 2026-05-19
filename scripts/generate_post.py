"""
generate_post.py
================
صورة تلغرام مع الأهداف المحدَّثة:
  هدف أول +5%  |  هدف ثانٍ +10% (ذهبية +12%)  |  وقف -4%  |  7-10 أيام
"""

import json, os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

DAILY_FILE  = "data/daily.json"
GOLDEN_FILE = "data/golden_signal.json"
OUTPUT_IMG  = "data/signal_image.png"
GOLDEN_IMG  = "data/golden_image.png"

BG_DARK    = (10,  14,  30)
BG_CARD    = (18,  24,  45)
GOLD       = (212, 175,  55)
GREEN      = ( 39, 174,  96)
RED        = (231,  76,  60)
WHITE      = (255, 255, 255)
LGRAY      = (180, 180, 200)
BLUE       = ( 52, 152, 219)

W, H = 800, 920


def load_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def generate_image(data, output_path, is_golden=False):
    img  = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    for y in range(H):
        r = int(10 + (18-10)*y/H); g = int(14 + (24-14)*y/H); b = int(30 + (45-30)*y/H)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    accent = GOLD if is_golden else BLUE
    tag    = "⭐ إشارة ذهبية" if is_golden else "📈 إشارة يومية"

    # شريط العنوان
    draw.rounded_rectangle([30,30,W-30,110], radius=16, fill=accent)
    draw.text((W//2, 70), "مُضارب | توصيات تاسي",
              font=load_font(32, bold=True), fill=BG_DARK, anchor="mm")

    # بيانات السهم
    draw.rounded_rectangle([30,130,W-30,300], radius=14,
                           fill=BG_CARD, outline=accent, width=2)
    draw.text((W//2, 180), data.get("symbol",""),      font=load_font(42,True), fill=accent, anchor="mm")
    draw.text((W//2, 230), data.get("stock_name",""),  font=load_font(24),      fill=WHITE,  anchor="mm")
    draw.text((W//2, 275), tag,                        font=load_font(20),      fill=LGRAY,  anchor="mm")

    # حساب نسب الأهداف
    entry     = float(data.get("entry",    0) or 0)
    target1   = float(data.get("target1",  0) or 0)
    target2   = float(data.get("target2",  0) or 0)
    stop_loss = float(data.get("stop_loss",0) or 0)
    t2_pct    = data.get("target2_pct", 10.0)
    max_days  = data.get("max_days", 10)

    def p(val):
        if entry > 0 and val > 0:
            return f"+{((val-entry)/entry*100):.1f}%"
        return ""

    def ps(val):
        if entry > 0 and val > 0:
            return f"-{((entry-val)/entry*100):.1f}%"
        return ""

    # صفوف البيانات
    rows = [
        ("نقطة الدخول",   f"{entry:.2f} ريال",                                    WHITE),
        ("الهدف الأول",   f"{target1:.2f} ريال  ({p(target1)})",                  GREEN),
        ("الهدف الثاني",  f"{target2:.2f} ريال  (+{t2_pct:.0f}%)",               GREEN),
        ("وقف الخسارة",   f"{stop_loss:.2f} ريال  ({ps(stop_loss)})",             RED),
        ("الإطار الزمني", f"أسبوع — أقصاه {max_days} أيام",                       BLUE),
        ("مكافأة/مخاطرة", f"{data.get('rr',0)}:1",                                GOLD),
        ("قوة الإشارة",   f"{data.get('score',0)}/100",                           accent),
    ]

    y_row = 330
    for label, value, color in rows:
        draw.rounded_rectangle([40,y_row,W-40,y_row+60], radius=10,
                               fill=BG_CARD, outline=(40,50,80), width=1)
        draw.text((70,     y_row+30), label, font=load_font(20,True), fill=LGRAY,  anchor="lm")
        draw.text((W-70,   y_row+30), value, font=load_font(20),      fill=color,  anchor="rm")
        y_row += 72

    # مؤشرات فنية
    y_tech = y_row + 10
    draw.rounded_rectangle([30,y_tech,W-30,y_tech+80], radius=14,
                           fill=BG_CARD, outline=accent, width=1)
    accel       = data.get("acceleration", 0)
    accel_text  = f"تسارع: {accel}/50" if accel > 0 else ""
    draw.text((W//2, y_tech+22), f"RSI: {data.get('rsi',0)}  |  {accel_text}",
              font=load_font(17), fill=LGRAY, anchor="mm")
    note_text = data.get("note", "")[:60]
    draw.text((W//2, y_tech+55), note_text,
              font=load_font(15), fill=LGRAY, anchor="mm")

    # تذييل
    draw.text((W//2, H-60), datetime.now().strftime("%Y-%m-%d  %H:%M"),
              font=load_font(15), fill=LGRAY, anchor="mm")
    draw.text((W//2, H-30), "⚠️  تحليلات تعليمية فقط — المستثمر يتخذ قراره بنفسه",
              font=load_font(14), fill=(120,120,140), anchor="mm")

    img.save(output_path, "PNG", quality=95)
    print(f"  ✅ صورة {'ذهبية' if is_golden else 'يومية'} محفوظة: {output_path}")


def main():
    os.makedirs("data", exist_ok=True)

    if os.path.exists(DAILY_FILE):
        with open(DAILY_FILE, encoding="utf-8") as f: daily = json.load(f)
        is_golden = daily.get("type", "") == "اشارة ذهبية"
        generate_image(daily, OUTPUT_IMG, is_golden=is_golden)
        # نسخ للـ output.png المستخدم في النشر
        import shutil
        shutil.copy(OUTPUT_IMG, "output.png")
    else:
        print("  ❌ daily.json غير موجود")

    if os.path.exists(GOLDEN_FILE):
        with open(GOLDEN_FILE, encoding="utf-8") as f: golden = json.load(f)
        generate_image(golden, GOLDEN_IMG, is_golden=True)


if __name__ == "__main__":
    main()
