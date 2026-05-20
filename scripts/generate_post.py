import json
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

DATA_FILE  = "data/daily.json"
OUTPUT_IMG = "output.png"

# ─── الألوان ─────────────────────────────────────────────────
BG     = (8,   12,  26)
CARD   = (14,  20,  42)
GOLD   = (212, 175,  55)
GREEN  = ( 46, 204, 113)
RED    = (231,  76,  60)
WHITE  = (255, 255, 255)
GRAY   = (160, 170, 195)
BORDER = ( 30,  45,  80)

W, H = 900, 980


def font(size, bold=False):
    paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def pct(entry, target):
    try:
        e = float(entry); t = float(target)
        return f"+{((t-e)/e*100):.1f}%" if t > e else f"{((t-e)/e*100):.1f}%"
    except Exception:
        return ""


def draw_row(draw, y, label, value, color=WHITE, h=58):
    draw.rounded_rectangle([50, y, W-50, y+h], radius=10,
                           fill=CARD, outline=BORDER, width=1)
    draw.text((80,       y+h//2), label, font=font(19, bold=True), fill=GRAY,  anchor="lm")
    draw.text((W-80,     y+h//2), value, font=font(19),            fill=color, anchor="rm")
    return y + h + 10


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # تدرج الخلفية
    for y in range(H):
        t = y / H
        r = int(8  + (14-8) *t)
        g = int(12 + (20-12)*t)
        b = int(26 + (42-26)*t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    is_golden = d.get("type", "") == "اشارة ذهبية"
    accent    = GOLD if is_golden else (52, 152, 219)

    # ─── شريط العنوان ────────────────────────────────────────
    draw.rounded_rectangle([20, 20, W-20, 100], radius=18, fill=accent)
    title = "مضارب | إشارة ذهبية ⭐" if is_golden else "مضارب | إشارة اليوم 📊"
    draw.text((W//2, 60), title, font=font(30, bold=True), fill=BG, anchor="mm")

    # ─── بطاقة السهم ─────────────────────────────────────────
    draw.rounded_rectangle([20, 115, W-20, 240],
                           radius=16, fill=CARD, outline=accent, width=2)
    draw.text((W//2, 158), d.get("symbol", ""),      font=font(48, bold=True), fill=accent, anchor="mm")
    draw.text((W//2, 210), d.get("stock_name", ""),  font=font(22),            fill=WHITE,  anchor="mm")

    # ─── الأسعار ─────────────────────────────────────────────
    entry     = d.get("entry",     "")
    target1   = d.get("target1",   "")
    target2   = d.get("target2",   "")
    stop_loss = d.get("stop_loss", "")
    t2_pct    = d.get("target2_pct", 10.0)
    max_days  = d.get("max_days",  10)
    accel     = d.get("acceleration", 0)

    y = 260
    y = draw_row(draw, y, "نقطة الدخول",   f"{entry} ريال",                              WHITE)
    y = draw_row(draw, y, "الهدف الأول",   f"{target1} ريال  ({pct(entry,target1)})",    GREEN)
    y = draw_row(draw, y, "الهدف الثاني",  f"{target2} ريال  (+{t2_pct:.0f}%)",          GREEN)
    y = draw_row(draw, y, "وقف الخسارة",  f"{stop_loss} ريال  ({pct(entry,stop_loss)})", RED)
    y = draw_row(draw, y, "الإطار الزمني", f"أسبوع — أقصاه {max_days} أيام",             (52,152,219))
    y = draw_row(draw, y, "مكافأة/مخاطرة", f"{d.get('rr',0)}:1",                          GOLD)
    y = draw_row(draw, y, "قوة الإشارة",   f"{d.get('score',0)}/100",                    accent)

    # ─── شريط المؤشرات ───────────────────────────────────────
    y += 5
    draw.rounded_rectangle([50, y, W-50, y+65], radius=14,
                           fill=CARD, outline=accent, width=1)
    accel_text = f"  🚀 تسارع {accel}/50" if accel >= 15 else ""
    draw.text((W//2, y+22),
              f"RSI: {d.get('rsi',0)}  |  RS Rank: {d.get('rs_rank',0)}{accel_text}",
              font=font(18), fill=GRAY, anchor="mm")
    note = (d.get("signal_reason", "") or d.get("note", ""))[:55]
    draw.text((W//2, y+50), note, font=font(15), fill=GRAY, anchor="mm")

    # ─── تذييل ───────────────────────────────────────────────
    draw.text((W//2, H-55), d.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
              font=font(15), fill=GRAY, anchor="mm")
    draw.text((W//2, H-25),
              "⚠️  محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية",
              font=font(14), fill=(80, 90, 120), anchor="mm")

    img.save(OUTPUT_IMG, "PNG", quality=95)
    print(f"✅ الصورة محفوظة: {OUTPUT_IMG}")


if __name__ == "__main__":
    main()
