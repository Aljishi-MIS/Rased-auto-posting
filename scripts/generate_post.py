#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rased Auto Posting - Normal Signal Generator
مولّد صور إشارات راصد العادية (أثناء السوق)
تصميم: أزرق/رمادي — مضغوط — احترافي
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
    print("💡 ثبّتها عبر: pip install Pillow")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# 🎨 ألوان التصميم العادي
# ═══════════════════════════════════════════════════════════════
NORMAL_COLORS = {
    "bg": "#0B1120",
    "card": "#151E32",
    "accent": "#3498DB",
    "gold": "#D4AF37",
    "green": "#2ECC71",
    "red": "#E74C3C",
    "white": "#FFFFFF",
    "gray": "#95A5A6",
    "border": "#2C3E50",
    "divider": "#1F2937"
}

# ═══════════════════════════════════════════════════════════════
# 🔤 إعدادات الخطوط
# ═══════════════════════════════════════════════════════════════
FONTS = {
    "path": "assets/fonts",
    "sizes": {
        "title": 36,
        "stock": 48,
        "label": 26,
        "value": 32,
        "price": 42,
        "footer": 20,
        "tiny": 18
    }
}

# ═══════════════════════════════════════════════════════════════
# 🏷️ الهوية
# ═══════════════════════════════════════════════════════════════
BRANDING = {
    "name": "راصد",
    "channel": "@RasedSA",
    "watermark": "بواسطة راصد | عينك على الفرص"
}

# ═══════════════════════════════════════════════════════════════
# 📐 أبعاد الصورة
# ═══════════════════════════════════════════════════════════════
IMG_WIDTH = 1080
IMG_HEIGHT = 1350
PADDING = 60


class RasedNormalGenerator:
    """مولّد صور الإشارات العادية"""

    def __init__(self):
        self.data = None
        self.img = None
        self.draw = None
        self.fonts = {}
        self._load_fonts()

    def _load_fonts(self):
        """تحميل الخطوط العربية مع fallback ذكي"""
        sizes = FONTS["sizes"]
        font_dir = Path(FONTS["path"])
        
        # قائمة الخطوط بالترتيب (الأفضل أولاً)
        font_candidates = [
            ("Cairo", "Cairo"),
            ("Tajawal", "Tajawal"),
            ("Arial", "arial"),
        ]
        
        fonts_loaded = False
        
        for font_name, file_prefix in font_candidates:
            try:
                # جرب المسارات المختلفة
                font_paths = {
                    "Bold": [
                        font_dir / f"{file_prefix}-Bold.ttf",
                        font_dir / f"{font_name}-Bold.ttf",
                        Path(f"C:/Windows/Fonts/{file_prefix}-Bold.ttf"),
                        Path(f"/usr/share/fonts/{file_prefix}-Bold.ttf"),
                    ],
                    "Regular": [
                        font_dir / f"{file_prefix}-Regular.ttf",
                        font_dir / f"{font_name}-Regular.ttf",
                        Path(f"C:/Windows/Fonts/{file_prefix}-Regular.ttf"),
                        Path(f"/usr/share/fonts/{file_prefix}-Regular.ttf"),
                    ],
                    "Light": [
                        font_dir / f"{file_prefix}-Light.ttf",
                        font_dir / f"{font_name}-Light.ttf",
                    ],
                }
                
                # ابحث عن الخطوط
                bold_found = None
                reg_found = None
                light_found = None
                
                for bold_path in font_paths["Bold"]:
                    if bold_path.exists():
                        bold_found = bold_path
                        break
                
                for reg_path in font_paths["Regular"]:
                    if reg_path.exists():
                        reg_found = reg_path
                        break
                
                for light_path in font_paths["Light"]:
                    if light_path.exists():
                        light_found = light_path
                        break
                
                # إذا وجدنا الخطوط
                if bold_found and reg_found:
                    self.fonts = {
                        "title": ImageFont.truetype(bold_found, sizes["title"]),
                        "stock": ImageFont.truetype(bold_found, sizes["stock"]),
                        "label": ImageFont.truetype(reg_found, sizes["label"]),
                        "value": ImageFont.truetype(bold_found, sizes["value"]),
                        "price": ImageFont.truetype(bold_found, sizes["price"]),
                        "footer": ImageFont.truetype(reg_found, sizes["footer"]),
                        "tiny": ImageFont.truetype(light_found or reg_found, sizes["tiny"])
                    }
                    print(f"✅ تم تحميل خط: {font_name}")
                    fonts_loaded = True
                    break
                    
            except Exception as e:
                print(f"⚠️ فشل تحميل {font_name}: {e}")
                continue
        
        # Fallback نهائي
        if not fonts_loaded:
            print("⚠️ لم يتم العثور على خطوط عربية - استخدام الخط الافتراضي")
            try:
                self.fonts = {
                    "title": ImageFont.truetype("arial.ttf", sizes["title"]),
                    "stock": ImageFont.truetype("arialbd.ttf", sizes["stock"]),
                    "label": ImageFont.truetype("arial.ttf", sizes["label"]),
                    "value": ImageFont.truetype("arialbd.ttf", sizes["value"]),
                    "price": ImageFont.truetype("arialbd.ttf", sizes["price"]),
                    "footer": ImageFont.truetype("arial.ttf", sizes["footer"]),
                    "tiny": ImageFont.truetype("arial.ttf", sizes["tiny"])
                }
                print("✅ تم استخدام Arial كخط بديل")
            except:
                self.fonts = {k: ImageFont.load_default() for k in sizes.keys()}
                print("❌ استخدام الخط الافتراضي (قد لا يدعم العربية)")

    def load_data(self, file_path):
        """تحميل البيانات من ملف JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except FileNotFoundError:
            print(f"❌ الملف غير موجود: {file_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ خطأ في تنسيق JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            return False

    def create_background(self):
        """إنشاء الخلفية الداكنة مع تدرج خفيف"""
        self.img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), NORMAL_COLORS["bg"])
        self.draw = ImageDraw.Draw(self.img)
        
        # تدرج خفيف في الأعلى
        for y in range(150):
            alpha = int(60 * (1 - y/150))
            color = (52, 152, 219, alpha)
            self.draw.line([(0, y), (IMG_WIDTH, y)], fill=color)

    def draw_header(self):
        """رسم الرأس"""
        header = f"{BRANDING['name']} | إشارة اليوم"
        bbox = self.draw.textbbox((0, 0), header, font=self.fonts["title"])
        w = bbox[2] - bbox[0]
        x = (IMG_WIDTH - w) // 2
        
        self.draw.text((x, 40), header, 
                      font=self.fonts["title"], fill=NORMAL_COLORS["accent"])
        
        # خط فاصل
        line_y = 40 + bbox[3] + 15
        self.draw.line([(PADDING, line_y), (IMG_WIDTH-PADDING, line_y)], 
                      fill=NORMAL_COLORS["accent"], width=3)
        
        # التاريخ
        now = datetime.now().strftime("%Y/%m/%d - %H:%M")
        self.draw.text((PADDING, line_y + 12), now, 
                      font=self.fonts["footer"], fill=NORMAL_COLORS["gray"])

    def draw_stock_info(self):
        """رسم معلومات السهم"""
        if not self.data:
            return
        
        y = 160
        
        name = self.data.get('stock_name', '')
        symbol = self.data.get('stock_symbol', '')
        title = f"{name} — {symbol}"
        
        bbox = self.draw.textbbox((0, 0), title, font=self.fonts["stock"])
        w = bbox[2] - bbox[0]
        x = (IMG_WIDTH - w) // 2
        
        self.draw.text((x, y), title, 
                      font=self.fonts["stock"], fill=NORMAL_COLORS["white"])
        
        sector = self.data.get('sector', '')
        if sector:
            sector_text = f"🏢 القطاع: {sector}"
            bbox_sec = self.draw.textbbox((0, 0), sector_text, font=self.fonts["label"])
            w_sec = bbox_sec[2] - bbox_sec[0]
            self.draw.text(((IMG_WIDTH - w_sec)//2, y + 60), 
                          sector_text, font=self.fonts["label"], 
                          fill=NORMAL_COLORS["gray"])

    def _draw_price_row(self, label, value, color, icon="", y_start=None):
        """رسم صف سعر واحد"""
        if y_start is
