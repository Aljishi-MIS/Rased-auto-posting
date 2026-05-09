import json
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

def F(s):  return ImageFont.truetype("assets/Cairo-Bold.ttf",    s)
def FR(s): return ImageFont.truetype("assets/Tajawal-Regular.ttf",s)

def tc(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="mm",direction="rtl",language="ar")
def tr(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="rm",direction="rtl",language="ar")
def tl(draw,x,y,text,font,color):
    draw.text((x,y),str(text),fill=color,font=font,anchor="lm",direction="rtl",language="ar")

img  = Image.new("RGB",(W,H),BG)
draw = ImageDraw.Draw(img)

glow = Image.new("RGBA",(W,H),(0,0,0,0))
ImageDraw.Draw(glow).ellipse((260,-180,820,330),fill=(240,180,41,38))
glow = glow.filter(ImageFilter.GaussianBlur(75))
img  = Image.alpha_composite(img.convert("RGBA"),glow).convert("RGB")
draw = ImageDraw.Draw(img)

draw.rounded_rectangle((55,38,W-55,H-38),radius=46,fill=CARD,outline=BORDER,width=3)

LS=108; LX=W//2-LS//2; LY=74
try:
    logo=Image.open("assets/logo.png").convert("RGBA")
    logo=logo.resize((LS,LS),Image.LANCZOS)
    mask=Image.new("L",(LS,LS),0)
    ImageDraw.Draw(mask).ellipse((0,0,LS,LS),fill=255)
    img.paste(logo,(LX,LY),mask)
    draw=ImageDraw.Draw(img)
except:
    pass

tc(draw,W//2,220,"مضارب",F(68),GOLD)
tc(draw,W//2,280,"تحليل فني وتعليمي لسوق الأسهم السعودية",FR(29),WHITE)

def divider(y):
    draw.line([(240,y),(W//2-12,y)],fill=BORDER,width=2)
    draw.line([(W//2+12,y),(W-240,y)],fill=BORDER,width=2)
    draw.ellipse((W//2-7,y-7,W//2+7,y+7),fill=GOLD)

divider(330)

sn=data.get("stock_name",""); sym=data.get("symbol","")
tc(draw,W//2,392,f"{sn} - {sym}",F(60),WHITE)

divider(444)

rows=[
    ("السعر الحالي:",data.get("price",""),   WHITE,"price"),
    ("نقطة الدخول:", data.get("entry",""),   GOLD, "entry"),
    ("الهدف الأول:", data.get("target1",""), GREEN,"target"),
    ("الهدف الثاني:",data.get("target2",""), GREEN,"target"),
    ("وقف الخسارة:", data.get("stop_loss",""),RED, "stop"),
]

y0=466; RH=78; MX=95

for i,(label,value,color,kind) in enumerate(rows):
    y=y0+i*RH; yc=y+RH//2
    draw.rounded_rectangle((MX,y+4,W-MX,y+RH-4),radius=20,fill=ROW,outline="#2A3F55",width=2)
    ix=W-MX-40
    draw.ellipse((ix-26,yc-26,ix+26,yc+26),outline=color,width=3)
    if kind=="price":
        for bx,bh in [(-11,7),(0,14),(11,21)]:
            draw.rectangle((ix+bx,yc+13-bh,ix+bx+8,yc+13),fill=WHITE)
    elif kind in("entry","target"):
        draw.ellipse((ix-13,yc-13,ix+13,yc+13),outline=color,width=3)
        draw.ellipse((ix-5,yc-5,ix+5,yc+5),fill=color)
        draw.line([(ix+9,yc-9),(ix+19,yc-19)],fill=color,width=4)
    elif kind=="stop":
        pts=[(ix,yc-18),(ix+15,yc-7),(ix+11,yc+13),(ix,yc+20),(ix-11,yc+13),(ix-15,yc-7)]
        draw.polygon(pts,outline=color)
        draw.line([(ix-8,yc-8),(ix+8,yc+8)],fill=color,width=4)
        draw.line([(ix+8,yc-8),(ix-8,yc+8)],fill=color,width=4)
    tr(draw,ix-34,yc,label,F(30),color)
    tl(draw,MX+28,yc,f"{value} ريال",F(32),color)

note_y=y0+len(rows)*RH+16
note=data.get("note","قراءة فنية تعليمية لسهم قريب من منطقة مقاومة مع متابعة السيولة.")
draw.rounded_rectangle((MX-10,note_y,W-MX+10,note_y+66),radius=18,fill="#07111E",outline=BORDER,width=2)
tc(draw,W//2,note_y+33,note,FR(22),MUTED)

div_y=note_y+88
divider(div_y)
tc(draw,W//2,div_y+28,"محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية",FR(22),MUTED)

pill_y=div_y+60; pw=295
draw.rounded_rectangle((W//2-pw//2,pill_y-22,W//2+pw//2,pill_y+22),radius=22,fill=CARD,outline=BORDER,width=2)
draw.text((W//2,pill_y),"t.me/TASI_Smart",fill=GOLD,font=F(26),anchor="mm",direction="ltr")

img.save("output.png",quality=97)
print("✅ Post generated successfully.")
