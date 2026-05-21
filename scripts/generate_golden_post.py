#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rased Auto Posting - Golden Signal Generator
مولّد إشارات راصد الذهبية المميزة (تصميم خاص)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ خطأ: المكتبة Pillow غير مثبتة")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# إعدادات التصميم الذهبي (مخصصة للإشارات القوية)
# ═══════════════════════════════════════════════════════════════
GOLDEN_COLORS = {
    "bg": "#1A0F0A",            # خلفية داكنة غنية (بني/أسود)
    "card": "#2D1F1A",          # خلفية البطاقات الداخلية
    "accent": "#FFD700",        # ذهبي لامع (اللون الرئيسي)
    "green": "#2ECC71",         # أخضر للأهداف
    "red": "#E74C3C",           # أحمر للوقف
    "white": "#FFF8DC",         # أبيض كريمي للنصوص
    "gray": "#B8A898",          # رمادي دافئ للعناوين
    "border": "#FFD700"         # لون الإطار الذهبي
}

FONTS = {
    "sizes": {
        "title": 36,
        "stock": 48,
        "label": 26,
        "value": 32,
        "price": 42,
        "footer": 20,
        "badge": 24
    }
}

BRANDING = {
    "name": "راصد",
    "channel": "@RasedSA"
}

# أبعاد الصورة
IMG_WIDTH = 1080
IMG_HEIGHT = 1350
PADDING = 60
BORDER_WIDTH = 12

class RasedGoldenGenerator:
    def __init__(self):
        self.data = None
        self.img = None
        self.draw = None
        self.fonts = {}
        self._load_fonts()

    def _load_fonts(self):
        """تحميل الخطوط من المجلد الرئيسي"""
        sizes = FONTS["sizes"]
        # المسار النسبي للمجلد الرئيسي (أعلى مجلد scripts)
        base_dir = Path(__file__).parent.parent
        font_dir = base_dir / "assets" / "fonts"
        
        # نجرب Tajawal ثم Cairo
        font_names = ["Tajawal", "Cairo", "Arial"]
        
        for name in font_names:
            try:
                bold_path = font_dir / f"{name}-Bold.ttf"
                reg_path = font_dir / f"{name}-Regular.ttf"
                
                if bold_path.exists() and reg_path.exists():
                    self.fonts = {
                        "title": ImageFont.truetype(bold_path, sizes["title"]),
                        "stock": ImageFont.truetype(bold_path, sizes["stock"]),
                        "label": ImageFont.truetype(reg_path, sizes["label"]),
                        "value": ImageFont.truetype(bold_path, sizes["value"]),
                        "price": ImageFont.truetype(bold_path, sizes["price"]),
                        "footer": ImageFont.truetype(reg_path, sizes["footer"]),
                        "badge": ImageFont.truetype(bold_path, sizes["badge"])
                    }
                    print(f"✅ تم تحميل خط: {name}")
                    return
            except Exception:
                continue
        
        print("⚠️ لم يتم العثور على الخطوط، استخدام الافتراضي")
        self.fonts = {k: ImageFont.load_default() for k in sizes.keys()}

    def load_data(self, file_path):
        """تحميل البيانات من ملف JSON محدد"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ خطأ في قراءة الملف {file_path}: {e}")
            return False

    def create_base(self):
        """إنشاء الخلفية الداكنة مع تأثير توهج ذهبي"""
        self.img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), GOLDEN_COLORS["bg"])
        self.draw = ImageDraw.Draw(self.img)
        
        # توهج ذهبي خفيف في الأعلى
        for y in range(200):
            alpha = int(80 * (1 - y/200))
            color = (255, 215, 0, alpha) # ذهبي شفاف
            self.draw.line([(0, y), (IMG_WIDTH, y)], fill=color)

    def draw_frame(self):
        """رسم الإطار الذهبي المزدوج"""
        # الإطار الخارجي
        self.draw.rectangle(
            [(0, 0), (IMG_WIDTH, IMG_HEIGHT)],
            outline=GOLDEN_COLORS["border"],
            width=BORDER_WIDTH
        )
        # إطار داخلي رفيع للزينة
        self.draw.rectangle(
            [(BORDER_WIDTH + 10, BORDER_WIDTH + 10), 
             (IMG_WIDTH - BORDER_WIDTH - 10, IMG_HEIGHT - BORDER_WIDTH - 10)],
            outline=GOLDEN_COLORS["gray"],
            width=2
        )

    def draw_header(self):
        """رأس الصورة: الشعار + التاريخ + شارة ذهبية"""
        # 1. شارة "إشارة ذهبية"
        badge_text = "✨ إشارة ذهبية مميزة ✨"
        bbox = self.draw.textbbox((0, 0), badge_text, font=self.fonts["badge"])
        badge_w = bbox[2] - bbox[0]
        badge_h = bbox[3] - bbox[1]
        badge_x = (IMG_WIDTH - badge_w) // 2
        badge_y = 40
        
        # خلفية الشارة (كبسولة ذهبية)
        self.draw.rounded_rectangle(
            [(badge_x - 15, badge_y), (badge_x + badge_w + 15, badge_y + badge_h + 10)],
            radius=20,
            fill=GOLDEN_COLORS["accent"]
        )
        
        # نص الشارة (أسود)
        self.draw.text((badge_x, badge_y + 5), badge_text, 
                      font=self.fonts["badge"], fill="#000000")

        # 2. اسم القناة في الأعلى
        header_text = f"{BRANDING['name']} | إشارة اليوم"
        bbox_h = self.draw.textbbox((0, 0), header_text, font=self.fonts["title"])
        w_h = bbox_h[2] - bbox_h[0]
        x_h = (IMG_WIDTH - w_h) // 2
        
        self.draw.text((x_h, badge_y + 80), header_text, 
                      font=self.fonts["title"], fill=GOLDEN_COLORS["accent"])
        
        # خط فاصل ذهبي
        line_y = badge_y + 80 + 50
        self.draw.line([(PADDING, line_y), (IMG_WIDTH-PADDING, line_y)], 
                      fill=GOLDEN_COLORS["accent"], width=3)
        
        # التاريخ
        now = datetime.now().strftime("%Y/%m/%d - %H:%M")
        self.draw.text((PADDING, line_y + 15), now, 
                      font=self.fonts["footer"], fill=GOLDEN_COLORS["gray"])

    def draw_stock_info(self):
        """معلومات السهم"""
        if not self.data: return
        
        y_start = 260
        symbol = self.data.get('stock_symbol', '')
        name = self.data.get('stock_name', '')
        title_text = f"{name} — {symbol}"
        
        bbox = self.draw.textbbox((0, 0), title_text, font=self.fonts["stock"])
        w = bbox[2] - bbox[0]
        x = (IMG_WIDTH - w) // 2
        
        self.draw.text((x, y_start), title_text, 
                      font=self.fonts["stock"], fill=GOLDEN_COLORS["white"])
        
        # القطاع
        sector = self.data.get('sector', '')
        if sector:
            sector_text = f"القطاع: {sector}"
            bbox_sec = self.draw.textbbox((0, 0), sector_text, font=self.fonts["label"])
            w_sec = bbox_sec[2] - bbox_sec[0]
            self.draw.text(((IMG_WIDTH-w_sec)//2, y_start + 60), 
                          sector_text, font=self.fonts["label"], fill=GOLDEN_COLORS["gray"])

    def draw_price_row(self, label, value, color, icon=""):
        """رسم صف سعر واحد بتصميم بطاقات فاخرة"""
        start_y = self.current_y
        
        # خلفية البطاقة
        self.draw.rounded_rectangle(
            [(PADDING, start_y), (IMG_WIDTH-PADDING, start_y + 80)],
            radius=15,
            fill=GOLDEN_COLORS["card"]
        )
        
        # شريط جانبي ملون
        self.draw.rectangle(
            [(PADDING, start_y), (PADDING+10, start_y + 80)],
            fill=color
        )
        
        # التسمية
        label_text = f"{icon} {label}"
        self.draw.text((PADDING + 30, start_y + 20), 
                      label_text, font=self.fonts["label"], fill=GOLDEN_COLORS["gray"])
        
        # القيمة (يمين)
        val_text = f"{value}"
        bbox_val = self.draw.textbbox((0, 0), val_text, font=self.fonts["price"])
        w_val = bbox_val[2] - bbox_val[0]
        x_val = IMG_WIDTH - PADDING - 30 - w_val
        
        self.draw.text((x_val, start_y + 20), 
                      val_text, font=self.fonts["price"], fill=color)
        
        self.current_y += 95

    def draw_prices(self):
        """رسم جدول الأسعار"""
        if not self.data: return
        
        self.current_y = 420
        
        # السعر الحالي
        current = self.data.get('current_price', 0)
        self.draw_price_row("السعر الحالي", f"{current} ريال", GOLDEN_COLORS["accent"], "📊")
        
        # نقطة الدخول
        entry = self.data.get('entry_point', 0)
        self.draw_price_row("نقطة الدخول", f"{entry} ريال", GOLDEN_COLORS["accent"], "🎯")
        
        # الأهداف
        t1 = self.data.get('target1', 0)
        t1_pct = self.data.get('target1_percent', 0)
        self.draw_price_row("الهدف الأول", f"{t1} ريال (+{t1_pct}%)", GOLDEN_COLORS["green"], "🟢")
        
        t2 = self.data.get('target2', 0)
        t2_pct = self.data.get('target2_percent', 0)
        if t2:
            self.draw_price_row("الهدف الثاني", f"{t2} ريال (+{t2_pct}%)", GOLDEN_COLORS["green"], "🟢")
        
        # الوقف
        sl = self.data.get('stop_loss', 0)
        sl_pct = self.data.get('stop_loss_percent', 0)
        self.draw_price_row("وقف الخسارة", f"{sl} ريال (-{sl_pct}%)", GOLDEN_COLORS["red"], "")

    def draw_footer(self):
        """التذييل"""
        footer_y = IMG_HEIGHT - 140
        
        # خط فاصل
        self.draw.line([(PADDING, footer_y), (IMG_WIDTH-PADDING, footer_y)], 
                      fill=GOLDEN_COLORS["gray"], width=2)
        
        # التحذير
        warning = "️ محتوى تعليمي وتحليلي فقط — لا يعد توصية استثمارية"
        bbox_w = self.draw.textbbox((0, 0), warning, font=self.fonts["footer"])
        w_w = bbox_w[2] - bbox_w[0]
        self.draw.text(((IMG_WIDTH-w_w)//2, footer_y + 15), 
                      warning, font=self.fonts["footer"], fill=GOLDEN_COLORS["gray"])
        
        # العلامة المائية
        watermark = f"👁️ {BRANDING['name']} | {BRANDING['channel']}"
        bbox_wm = self.draw.textbbox((0, 0), watermark, font=self.fonts["label"])
        w_wm = bbox_wm[2] - bbox_wm[0]
        self.draw.text(((IMG_WIDTH-w_wm)//2, footer_y + 55), 
                      watermark, font=self.fonts["label"], fill=GOLDEN_COLORS["accent"])

    def generate(self, input_file, output_file):
        """التنفيذ الكامل"""
        if not self.load_data(input_file):
            return False
            
        print("🎨 بدء رسم التصميم الذهبي...")
        self.create_base()
        self.draw_frame()
        self.draw_header()
        self.draw_stock_info()
        self.draw_prices()
        self.draw_footer()
        
        # الحفظ
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        self.img.save(output_file, "PNG", quality=95)
        print(f"✅ تم حفظ الصورة الذهبية: {output_file}")
        return True

def main():
    # المسارات الافتراضية (نسبية لمجلد المشروع)
    base_dir = Path(__file__).parent.parent
    
    # الافتراضي: يبحث عن golden.json
    input_default = base_dir / "data" / "golden.json"
    output_default = base_dir / "output_golden.png"
    
    # السماح بتحديد الملفات عبر الأوامر
    input_file = sys.argv[1] if len(sys.argv) > 1 else str(input_default)
    output_file = sys.argv[2] if len(sys.argv) > 2 else str(output_default)
    
    generator = RasedGoldenGenerator()
    generator.generate(input_file, output_file)

if __name__ == "__main__":
    main()
