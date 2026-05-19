import json
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

with open("data/daily.json", "r", encoding="utf-8") as f:
    data = json.load(f)

W, H = 1080, 1080

BG_DARK  = (4, 8, 16)
BG_MID   = (8, 14, 26)
GOLD_1   = "#FFD700"
GOLD_2   = "#F0B429"
GOLD_3   = "#C8900A"
GOLD_4   = "#8B6914"
GREEN_G  = "#00FF88"
RED_G    = "#FF4560"
WHITE    = "#FFFFFF"
SILVER   = "#C8D8E8"

def F(s):  return ImageFont.truetype("assets/Cairo-Bold.ttf",    s)
def FR(s): return ImageFont.truetype("assets/Tajawal-Regular.ttf",s)
def FB(s): return ImageFont.truetype("assets/Tajawal-Bold.ttf",   s)

def tc(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="mm",direction="rtl",language="ar")
def tr(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="rm",direction="rtl",language="ar")

KSA = timezone(timedelta(hours=3))
now = datetime.now(KSA)
gen_at = data.get("generated_at","")
try:
    dt = datetime.strptime(gen_at, "%Y-%m-%d %H:%M")
    signal_date = dt.strftime("%Y/%m/%d")
    signal_time = dt.strftime("%I:%M %p").replace("AM","ص").replace("PM","م")
except:
    signal_date = now.strftime("%Y/%m/%d")
    signal_time = now.strftime("%I:%M %p").replace("AM","ص").replace("PM","م")

def pct(entry, price):
    try:
        e = float(entry); p = float(price)
        if e > 0:
            return f"{((p-e)/e*100):+.1f}%"
    except:
        pass
    return ""

entry   = data.get("entry",    "0")
target1 = data.get("target1",  "0")
target2 = data.get("target2",  "0")
stop    = data.get("stop_loss","0")
t2_pct  = data.get("target2_pct", 12.0)
max_days= data.get("max_days", 10)
accel   = data.get("acceleration", 0)

pct_t1   = pct(entry, target1)
pct_t2   = pct(entry, target2)
pct_stop = pct(entry, stop)

img  = Image.new("RGB",(W,H),BG_DARK)
draw = ImageDraw.Draw(img)

for y in range(H):
    t=y/H
    r=int(BG_DARK[0]+(BG_MID[0]-BG_DARK[0])*t)
    g=int(BG_DARK[1]+(BG_MID[1]-BG_DARK[1])*t)
    b=int(BG_DARK[2]+(BG_MID[2]-BG_DARK[2])*t)
    draw.line([(0,y),(W,y)],fill=(r,g,b))

for cx,cy,r,alpha in [(540,160,280,22),(540,160,180,35),(540,160,100,50)]:
    g2=Image.new("RGBA",(W,H),(0,0,0,0))
    ImageDraw.Draw(g2).ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,215,0,alpha))
    g2=g2.filter(ImageFilter.GaussianBlur(r*0.6))
    img=Image.alpha_composite(img.convert("RGBA"),g2).convert("RGB")
draw=ImageDraw.Draw(img)

draw.rounded_rectangle((24,24,W-24,H-24),radius=40,fill=None,outline=GOLD_4,width=1)
draw.rounded_rectangle((32,32,W-32,H-32),radius=34,fill=(7,14,26),outline=GOLD_3,width=2)
draw.rounded_rectangle((38,38,W-38,H-38),radius=30,fill=None,outline=GOLD_1,width=1)

def corner_deco(x,y,sx,sy,L=60):
    draw.line([(x,y),(x+sx*L,y)],fill=GOLD_1,width=3)
    draw.line([(x,y),(x,y+sy*L)],fill=GOLD_1,width=3)
    draw.ellipse((x-4,y-4,x+4,y+4),fill=GOLD_1)
    draw.ellipse((x-2,y-2,x+2,y+2),fill=WHITE)
    draw.line([(x+sx*20,y),(x+sx*35,y)],fill=GOLD_3,width=2)
    draw.line([(x,y+sy*20),(x,y+sy*35)],fill=GOLD_3,width=2)

M=38
corner_deco(M,M,+1,+1); corner_deco(W-M,M,-1,+1)
corner_deco(M,H-M,+1,-1); corner_deco(W-M,H-M,-1,-1)

draw.rounded_rectangle((38,38,W-38,108),radius=30,fill=(12,22,38))
draw.line([(60,108),(W-60,108)],fill=GOLD_3,width=1)
draw.text((W-125,73),signal_date,fill=GOLD_1,font=FB(22),anchor="rm",direction="ltr")
draw.line([(W//2+8,52),(W//2+8,92)],fill=GOLD_4,width=1)
draw.text((125,73),signal_time,fill=GREEN_G,font=FB(22),anchor="lm",direction="ltr")

bw=230
draw.rounded_rectangle((W//2-bw//2,52,W//2+bw//2,94),radius=20,fill=GOLD_2,outline=GOLD_1,width=2)
star_cx=W//2-bw//2+34
draw.polygon([(star_cx,56),(star_cx+6,67),(star_cx+19,67),(star_cx+9,75),(star_cx+12,88),
    (star_cx,80),(star_cx-12,88),(star_cx-9,75),(star_cx-19,67),(star_cx-6,67)],fill="#0B0B0B")
draw.text((W//2+14,73),"اشارة ذهبية",font=FB(24),fill="#0B0B0B",anchor="mm",direction="rtl",language="ar")

LS=96; LX=W//2-LS//2; LY=122
for r,alpha in [(72,10),(60,18),(48,28),(38,40)]:
    h2=Image.new("RGBA",(W,H),(0,0,0,0))
    ImageDraw.Draw(h2).ellipse((W//2-r,LY+LS//2-r,W//2+r,LY+LS//2+r),fill=(255,215,0,alpha))
    img=Image.alpha_composite(img.convert("RGBA"),h2).convert("RGB")
draw=ImageDraw.Draw(img)

draw.ellipse((LX-8,LY-8,LX+LS+8,LY+LS+8),fill=(6,12,24),outline=GOLD_1,width=3)
try:
    logo=Image.open("assets/logo.png").convert("RGBA")
    logo=logo.resize((LS,LS),Image.LANCZOS)
    mask=Image.new("L",(LS,LS),0)
    ImageDraw.Draw(mask).ellipse((0,0,LS,LS),fill=255)
    img.paste(logo,(LX,LY),mask)
    draw=ImageDraw.Draw(img)
except:
    pass

tc(draw,W//2,262,"مضارب",F(68),GOLD_1)
tc(draw,W//2,316,"تحليل ذكي متعمق - 20 يوم تاريخي",FR(26),SILVER)

def golden_divider(y):
    for i in range(200):
        draw.point((W//2-10-i,y),fill=(255,215,0))
    for i in range(200):
        draw.point((W//2+10+i,y),fill=(255,215,0))
    draw.line([(240,y),(W//2-10,y)],fill=GOLD_2,width=2)
    draw.line([(W//2+10,y),(W-240,y)],fill=GOLD_2,width=2)
    draw.ellipse((W//2-9,y-9,W//2+9,y+9),fill=(6,12,24),outline=GOLD_1,width=2)
    draw.ellipse((W//2-3,y-3,W//2+3,y+3),fill=GOLD_1)

golden_divider(350)
sn=data.get("stock_name",""); sym=data.get("symbol","")
draw.rounded_rectangle((120,362,W-120,410),radius=20,fill=(14,26,48),outline=GOLD_3,width=1)
tc(draw,W//2,386,f"{sn}  -  {sym}",F(50),WHITE)
golden_divider(424)

MX      = 72
PCT_COL = MX + 110
VAL_COL = W // 2 - 20

rows = [
    ("السعر الحالي:", data.get("price",""),  "",       WHITE,   "price"),
    ("نقطة الدخول:", entry,                  "",       GOLD_1,  "entry"),
    ("الهدف الاول:", target1,                pct_t1,   GREEN_G, "target"),
    (f"الهدف الثاني ({t2_pct:.0f}%):", target2, pct_t2, GREEN_G, "target"),
    ("وقف الخسارة:", stop,                   pct_stop, RED_G,   "stop"),
]

y0=440; RH=80

for i,(label,value,percent,color,kind) in enumerate(rows):
    y=y0+i*RH; yc=y+RH//2
    row_bg=(12,24,44) if i%2==0 else (10,20,38)
    draw.rounded_rectangle((MX,y+4,W-MX,y+RH-4),radius=22,fill=row_bg,outline=GOLD_4,width=1)
    draw.rounded_rectangle((MX,y+10,MX+4,y+RH-10),radius=4,fill=color)

    if percent:
        draw.line([(PCT_COL+80,y+14),(PCT_COL+80,y+RH-14)],fill="#1E3A55",width=1)

    ix=W-MX-38; iy=yc
    draw.ellipse((ix-22,iy-22,ix+22,iy+22),fill=row_bg,outline=color,width=2)
    if kind=="price":
        for bx,bh in [(-9,5),(0,12),(9,19)]:
            draw.rectangle((ix+bx,iy+11-bh,ix+bx+6,iy+11),fill=color)
    elif kind in("entry","target"):
        draw.ellipse((ix-10,iy-10,ix+10,iy+10),outline=color,width=2)
        draw.ellipse((ix-4,iy-4,ix+4,iy+4),fill=color)
        draw.line([(ix+7,iy-7),(ix+16,iy-16)],fill=color,width=3)
    elif kind=="stop":
        draw.line([(ix-8,iy-8),(ix+8,iy+8)],fill=color,width=4)
        draw.line([(ix+8,iy-8),(ix-8,iy+8)],fill=color,width=4)

    tr(draw,ix-32,yc,label,F(28),color)
    draw.text((VAL_COL,yc),f"{value} ريال",fill=color,font=F(29),anchor="mm",direction="rtl",language="ar")

    if percent:
        pct_color = GREEN_G if "+" in percent else RED_G
        draw.text((PCT_COL,yc),percent,fill=pct_color,font=FB(27),anchor="mm",direction="ltr")

# مؤشر الإطار الزمني
time_y = y0 + len(rows)*RH + 5
draw.rounded_rectangle((MX,time_y,W-MX,time_y+45),radius=14,
                       fill=(8,18,34),outline=GOLD_2,width=2)
time_text = f"الإطار الزمني: أسبوع — أقصاه {max_days} أيام"
if accel >= 30:
    time_text += f"  |  🚀 تسارع {accel}/50"
tc(draw,W//2,time_y+22,time_text,FR(20),GOLD_2)

metrics_y = time_y + 55
rsi=data.get("rsi","50"); score=data.get("score","80"); rr=data.get("rr","2.5")
draw.rounded_rectangle((MX,metrics_y,W-MX,metrics_y+50),radius=16,fill=(8,16,30),outline=GOLD_3,width=1)
for j,(txt,col) in enumerate([(f"RSI  {rsi}",GOLD_2),(f"R:R  {rr}",GREEN_G),(f"Score  {score}",WHITE)]):
    mx2=MX+140+j*284
    draw.text((mx2,metrics_y+25),txt,fill=col,font=FB(22),anchor="mm",direction="ltr")
    if j<2:
        draw.line([(mx2+130,metrics_y+10),(mx2+130,metrics_y+40)],fill=GOLD_4,width=1)

note_y=metrics_y+60
note=data.get("note","اشارة ذهبية: تراكم Smart Money + ضغط بولينجر + اختبار مقاومة متكرر.")
draw.rounded_rectangle((MX-8,note_y,W-MX+8,note_y+60),radius=18,fill=(8,18,34),outline=GOLD_2,width=2)
draw.rounded_rectangle((W-MX,note_y+10,W-MX+6,note_y+50),radius=4,fill=GOLD_1)
draw.rounded_rectangle((MX-8,note_y+10,MX-2,note_y+50),radius=4,fill=GOLD_1)
tc(draw,W//2,note_y+30,note,FR(21),SILVER)

div_y=note_y+78
golden_divider(div_y)
tc(draw,W//2,div_y+26,"محتوى تعليمي وتحليلي فقط - لا يعد توصية استثمارية",FR(21),SILVER)

pill_y=div_y+56; pw=290
draw.rounded_rectangle((W//2-pw//2,pill_y-20,W//2+pw//2,pill_y+20),radius=20,fill=(10,20,38),outline=GOLD_1,width=2)
draw.text((W//2,pill_y),"t.me/TASI_Smart",fill=GOLD_1,font=F(24),anchor="mm",direction="ltr")

img.save("output.png",quality=98)
print("Golden post generated successfully.")
