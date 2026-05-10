import json
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

W, H   = 1080, 1080
BG     = "#07101B"
CARD   = "#0B1624"
ROW    = "#0D1B2A"
GOLD   = "#F0B429"
BORDER = "#D99A00"
GREEN  = "#22C55E"
RED    = "#EF4444"
WHITE  = "#FFFFFF"
MUTED  = "#CBD5E1"
SILVER = "#94A3B8"

def F(s):  return ImageFont.truetype("assets/Cairo-Bold.ttf",    s)
def FR(s): return ImageFont.truetype("assets/Tajawal-Regular.ttf",s)
def FB(s): return ImageFont.truetype("assets/Tajawal-Bold.ttf",   s)

def tc(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="mm",direction="rtl",language="ar")
def tr(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="rm",direction="rtl",language="ar")
def tl(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="lm",direction="rtl",language="ar")

# ── وقت الإشارة بتوقيت KSA ─────────────────────────────────
KSA = timezone(timedelta(hours=3))
now = datetime.now(KSA)

gen_at = data.get("generated_at", "")
if gen_at:
    try:
        dt = datetime.strptime(gen_at, "%Y-%m-%d %H:%M")
        signal_date = dt.strftime("%Y/%m/%d")
        signal_time = dt.strftime("%I:%M %p")
    except:
        signal_date = now.strftime("%Y/%m/%d")
        signal_time = now.strftime("%I:%M %p")
else:
    signal_date = now.strftime("%Y/%m/%d")
    signal_time = now.strftime("%I:%M %p")

signal_time = signal_time.replace("AM","ص").replace("PM","م")

# ── canvas ──────────────────────────────────────────────────
img  = Image.new("RGB",(W,H),BG)
draw = ImageDraw.Draw(img)

glow = Image.new("RGBA",(W,H),(0,0,0,0))
ImageDraw.Draw(glow).ellipse((260,-180,820,330),fill=(240,180,41,38))
glow = glow.filter(ImageFilter.GaussianBlur(75))
img  = Image.alpha_composite(img.convert("RGBA"),glow).convert("RGB")
draw = ImageDraw.Draw(img)

# ── إطار ────────────────────────────────────────────────────
draw.rounded_rectangle((55,38,W-55,H-38),radius=46,fill=CARD,outline=BORDER,width=3)

# ── شريط التاريخ والوقت ─────────────────────────────────────
draw.rounded_rectangle((55,38,W-55,104),radius=46,fill="#060F1C")
draw.line([(75,104),(W-75,104)],fill=BORDER,width=1)

# أيقونة تقويم + التاريخ — يمين
draw.text((W-95,71),"📅",font=F(22),anchor="mm")
draw.text((W-125,71),signal_date,
    fill=GOLD,font=FB(24),anchor="rm",direction="ltr")

# فاصل عمودي
draw.line([(W//2+10,52),(W//2+10,90)],fill=BORDER,width=1)

# أيقونة ساعة + الوقت — يسار
draw.text((95,71),"🕐",font=F(22),anchor="mm")
draw.text((125,71),signal_time,
    fill=GREEN,font=FB(24),anchor="lm",direction="ltr")

# نص وسط
draw.text((W//2-20,71),"وقت الإشارة",
    fill=SILVER,font=FR(20),anchor="mm",direction="rtl",language="ar")

# ── لوغو ────────────────────────────────────────────────────
LS=100; LX=W//2-LS//2; LY=116
try:
    logo=Image.open("assets/logo.png").convert("RGBA")
    logo=logo.resize((LS,LS),Image.LANCZOS)
    mask=Image.new("L",(LS,LS),0)
    ImageDraw.Draw(mask).ellipse((0,0,LS,LS),fill=255)
    draw.ellipse((LX-5,LY-5,LX+LS+5,LY+LS+5),fill="#081422",outline=BORDER,width=2)
    img.paste(logo,(LX,LY),mask)
    draw=ImageDraw.Draw(img)
except:
    pass

# ── عنوان ───────────────────────────────────────────────────
tc(draw,W//2,256,"مضارب",F(64),GOLD)
tc(draw,W//2,310,"تحليل فني وتعليمي لسوق الأسهم السعودية",FR(27),WHITE)

# ── فاصل ────────────────────────────────────────────────────
def divider(y):
    draw.line([(240,y),(W//2-12,y)],fill=BORDER,width=2)
    draw.line([(W//2+12,y),(W-240,y)],fill=BORDER,width=2)
    draw.ellipse((W//2-7,y-7,W//2+7,y+7),fill=GOLD)

divider(350)

# ── اسم السهم ───────────────────────────────────────────────
sn=data.get("stock_name",""); sym=data.get("symbol","")
tc(draw,W//2,406,f"{sn} - {sym}",F(56),WHITE)

divider(454)

# ── صفوف البيانات ───────────────────────────────────────────
rows=[
    ("السعر الحالي:",data.get("price",""),    WHITE,"price"),
    ("نقطة الدخول:", data.get("entry",""),    GOLD, "entry"),
    ("الهدف الأول:", data.get("target1",""),  GREEN,"target"),
    ("الهدف الثاني:",data.get("target2",""),  GREEN,"target"),
    ("وقف الخسارة:", data.get("stop_loss",""),RED,  "stop"),
]

y0=472; RH=76; MX=95

for i,(label,value,color,kind) in enumerate(rows):
    y=y0+i*RH; yc=y+RH//2
    draw.rounded_rectangle((MX,y+4,W-MX,y+RH-4),radius=20,fill=ROW,outline="#2A3F55",width=2)
    ix=W-MX-40
    draw.ellipse((ix-24,yc-24,ix+24,yc+24),outline=color,width=3)
    if kind=="price":
        for bx,bh in [(-10,6),(0,13),(10,20)]:
            draw.rectangle((ix+bx,yc+12-bh,ix+bx+7,yc+12),fill=WHITE)
    elif kind in("entry","target"):
        draw.ellipse((ix-12,yc-12,ix+12,yc+12),outline=color,width=3)
        draw.ellipse((ix-4,yc-4,ix+4,yc+4),fill=color)
        draw.line([(ix+8,yc-8),(ix+18,yc-18)],fill=color,width=4)
    elif kind=="stop":
        pts=[(ix,yc-17),(ix+14,yc-6),(ix+10,yc+12),(ix,yc+19),(ix-10,yc+12),(ix-14,yc-6)]
        draw.polygon(pts,outline=color)
        draw.line([(ix-7,yc-7),(ix+7,yc+7)],fill=color,width=4)
        draw.line([(ix+7,yc-7),(ix-7,yc+7)],fill=color,width=4)
    tr(draw,ix-34,yc,label,F(29),color)
    tl(draw,MX+26,yc,f"{value} ريال",F(31),color)

# ── صندوق الملاحظة ──────────────────────────────────────────
note_y=y0+len(rows)*RH+14
note=data.get("note","قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة.")
draw.rounded_rectangle((MX-10,note_y,W-MX+10,note_y+62),radius=18,fill="#07111E",outline=BORDER,width=2)
tc(draw,W//2,note_y+31,note,FR(21),MUTED)

# ── فوتر ────────────────────────────────────────────────────
div_y=note_y+84
divider(div_y)
tc(draw,W//2,div_y+26,"محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية",FR(21),MUTED)

pill_y=div_y+56; pw=290
draw.rounded_rectangle((W//2-pw//2,pill_y-20,W//2+pw//2,pill_y+20),radius=20,fill=CARD,outline=BORDER,width=2)
draw.text((W//2,pill_y),"t.me/TASI_Smart",fill=GOLD,font=F(24),anchor="mm",direction="ltr")

img.save("output.png",quality=97)
print(f"✅ Post generated — {signal_date} {signal_time}")
