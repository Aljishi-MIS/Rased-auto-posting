#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rased Auto Posting - Image Generator
مُولّد صور إشارات راصد الاحترافية
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
    print("💡 قم بتثبيتها عبر: pip install Pillow")
    sys.exit(1)

# استيراد إعدادات راصد
try:
    from config import BRAND, FONT, BRANDING, IMAGE, DATA
except ImportError:
    print("⚠️ تحذير: ملف config.py غير موجود - استخدام الإعدادات الافتراضية")
    BRAND = {
        "primary": "#0F1A3C",
        "accent": "#D4AF37",
        "success": "#27AE60",
        "danger": "#E74C3C",
        "text_primary": "#F8F9FA",
        "text_secondary": "#A4B0BE",
        "muted": "#64748B",
        "card_bg": "#1A2744",
    }
    FONT = {
        "arabic": "Tajawal",
        "path": "assets/fonts",
        "sizes": {"title": 48, "large": 32, "medium": 24, "small": 18, "tiny": 14}
    }
    BRANDING = {
        "name": "راصد",
        "slogan": "عينك على الفرص",
        "watermark": "بواسطة راصد | عينك على الفرص"
    }
    IMAGE = {
        "width": 1080,
        "height": 1920,
        "padding": 80,
        "card_radius": 15,
    }
    DATA = {
        "daily_file": "data/daily.json",
        "output_image": "output.png",
    }


class RasedSignalGenerator:
    """مُولّد صور إشارات راصد الاحترافية"""

    def __init__(self, data_file: str = None):
        self.data_file = Path(data_file or DATA["daily_file"])
        self.data = None
        self.img = None
        self.draw = None
        self._load_fonts()

    def _load_fonts(self):
        """تحميل خطوط راصد"""
        font_sizes = FONT["sizes"]
        font_path = FONT.get("path", "assets/fonts")
        
        self.fonts = {
            "title": self._load_font(font_path, "Bold", font_sizes["title"]),
            "large": self._load_font(font_path, "Bold", font_sizes["large"]),
            "medium": self._load_font(font_path, "Regular", font_sizes["medium"]),
            "small": self._load_font(font_path, "Regular", font_sizes["small"]),
            "tiny": self._load_font(font_path, "Light", font_sizes["tiny"]),
        }

    def _load_font(self, base_path: str, weight: str, size: int):
        """تحميل الخط مع fallback"""
        font_name = FONT["arabic"]
        font_paths = [
            f"{base_path}/{font_name}-{weight}.ttf",
            f"{base_path}/{weight}.ttf",
            f"assets/fonts/{font_name}-{weight}.ttf",
            f"assets/fonts/{weight}.ttf",
        ]
        
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        
        # Fallback للنظام
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def load_data(self) -> bool:
        """تحميل البيانات من ملف JSON"""
        try:
            if not self.data_file.exists():
                print(f"❌ ملف البيانات غير موجود: {self.data_file}")
                return False

            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            required_fields = ['stock_name', 'stock_symbol', 'current_price',
                             'entry_point', 'target1', 'stop_loss']
            
            for field in required_fields:
                if field not in self.data:
                    print(f"❌ الحقل المطلوب مفقود: {field}")
                    return False

            print(f"✅ تم تحميل البيانات: {self.data['stock_name']} ({self.data['stock_symbol']})")
            return True

        except json.JSONDecodeError as e:
            print(f"❌ خطأ في تنسيق JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            return False

    def create_base_image(self):
        """إنشاء الصورة الأساسية مع خلفية راصد"""
        self.img = Image.new('RGB', (IMAGE["width"], IMAGE["height"]), BRAND["primary"])
        self.draw = ImageDraw.Draw(self.img)
        self._add_gradient_background()

    def _add_gradient_background(self):
        """إضافة تدرج لوني للخلفية"""
        for y in range(IMAGE["height"]):
            ratio = y / IMAGE["height"]
            r = int(BRAND["primary"][1:3], 16) * (1 - ratio * 0.3)
            g = int(BRAND["primary"][3:5], 16) * (1 - ratio * 0.3)
            b = int(BRAND["primary"][5:7], 16) * (1 - ratio * 0.3)
            self.draw.line([(0, y), (IMAGE["width"], y)], fill=(int(r), int(g), int(b)))

    def draw_header(self):
        """رسم الرأس مع شعار راصد"""
        padding = IMAGE["padding"]
        
        # أيقونة العين
        self.draw.text((padding, 50), "👁️", 
                      font=self.fonts["title"], fill=BRAND["accent"])
        
        # العنوان
        title = f"{BRANDING['name']} | إشارة اليوم"
        self.draw.text((IMAGE["width"]//2, 60), title,
                      font=self.fonts["large"], fill=BRAND["text_primary"], anchor="mm")
        
        # خط فاصل ذهبي
        self.draw.line([(padding, 110), (IMAGE["width"]-padding, 110)],
                      fill=BRAND["accent"], width=3)

    def draw_stock_info(self):
        """رسم معلومات السهم"""
        if not self.data:
            return

        y_start = 180
        padding = IMAGE["padding"]

        # اسم السهم
        stock_text = f"{self.data['stock_name']} — {self.data['stock_symbol']}"
        self.draw.text((IMAGE["width"]//2, y_start), stock_text,
                      font=self.fonts["large"], fill=BRAND["success"], anchor="mm")

        # القطاع
        if 'sector' in self.data:
            y_start += 50
            sector_text = f"🏢 القطاع: {self.data['sector']}"
            self.draw.text((IMAGE["width"]//2, y_start), sector_text,
                          font=self.fonts["medium"], fill=BRAND["text_secondary"], anchor="mm")

        # السعر الحالي
        y_start += 90
        price_text = f"💰 السعر الحالي: {self.data['current_price']} ريال"
        self._draw_card(price_text, y_start, BRAND["accent"], highlight=True)

    def _draw_card(self, text: str, y: int, color: str = None, highlight: bool = False):
        """رسم بطاقة نصية"""
        padding = IMAGE["padding"]
        card_width = IMAGE["width"] - (padding * 2)
        card_height = 80 if not highlight else 90
        radius = IMAGE["card_radius"]

        x1 = padding
        y1 = y - card_height // 2
        x2 = x1 + card_width
        y2 = y1 + card_height

        # خلفية البطاقة
        bg_color = BRAND["accent"] if highlight else BRAND["card_bg"]
        self.draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, fill=bg_color)

        # حدود للبطاقات المميزة
        if highlight:
            self.draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, 
                                       outline=BRAND["text_primary"], width=2)

        # النص
        text_color = BRAND["primary"] if highlight else (color or BRAND["text_primary"])
        font = self.fonts["large"] if highlight else self.fonts["medium"]
        
        # توسيط النص
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x_text = (x1 + x2) // 2
        y_text = (y1 + y2) // 2

        self.draw.text((x_text, y_text), text, font=font,
                      fill=text_color, anchor="mm")

    def draw_targets(self):
        """رسم الأهداف ووقف الخسارة"""
        if not self.data:
            return

        y_start = 520
        padding = IMAGE["padding"]

        # عنوان الأهداف
        self.draw.text((padding, y_start), "🎯 الأهداف",
                      font=self.fonts["medium"], fill=BRAND["text_primary"])

        # الهدف الأول
        if 'target1' in self.data:
            y_start += 70
            target1_text = f"🟢 الهدف الأول: {self.data['target1']} ريال"
            if 'target1_percent' in self.data:
                target1_text += f" (+{self.data['target1_percent']}%)"
            self._draw_card(target1_text, y_start, BRAND["success"])

        # الهدف الثاني
        if 'target2' in self.data:
            y_start += 90
            target2_text = f"🟢 الهدف الثاني: {self.data['target2']} ريال"
            if 'target2_percent' in self.data:
                target2_text += f" (+{self.data['target2_percent']}%)"
            self._draw_card(target2_text, y_start, BRAND["success"])

        # وقف الخسارة
        if 'stop_loss' in self.data:
            y_start += 90
            stop_text = f"🔴 وقف الخسارة: {self.data['stop_loss']} ريال"
            if 'stop_loss_percent' in self.data:
                stop_text += f" (-{self.data['stop_loss_percent']}%)"
            self._draw_card(stop_text, y_start, BRAND["danger"])

    def draw_analysis(self):
        """رسم التحليل الفني"""
        if not self.data:
            return

        y_start = 950
        padding = IMAGE["padding"]

        # الإطار الزمني
        if 'timeframe' in self.data:
            self.draw.text((padding, y_start), 
                          f"⏱ الإطار الزمني: {self.data['timeframe']}",
                          font=self.fonts["small"], fill=BRAND["text_secondary"])
            y_start += 45

        # الزخم
        if 'momentum' in self.data:
            self.draw.text((padding, y_start), 
                          f"⚡ الزخم: {self.data['momentum']}",
                          font=self.fonts["small"], fill=BRAND["accent"])
            y_start += 40

        # RS Rank
        if 'rs_rank' in self.data:
            self.draw.text((padding, y_start), 
                          f"📈 RS Rank: {self.data['rs_rank']}",
                          font=self.fonts["small"], fill=BRAND["text_primary"])
            y_start += 35

        # Score
        if 'score' in self.data:
            score_color = BRAND["success"] if self.data['score'] >= 80 else BRAND["accent"]
            self.draw.text((padding, y_start), 
                          f"🔢 Score: {self.data['score']}/100",
                          font=self.fonts["small"], fill=score_color)
            y_start += 50

        # القراءة الفنية
        if 'technical_reading' in self.data:
            self.draw.text((padding, y_start), "📌 قراءة فنية:",
                          font=self.fonts["small"], fill=BRAND["text_primary"])
            y_start += 40

            reading = self.data['technical_reading']
            lines = self._wrap_text(reading, max_width=IMAGE["width"]-(padding*2), 
                                   font=self.fonts["tiny"])
            
            for line in lines[:6]:
                self.draw.text((padding, y_start), f" • {line}",
                              font=self.fonts["tiny"], fill=BRAND["text_secondary"])
                y_start += 32

        # الثقة
        if 'confidence' in self.data:
            y_start += 30
            conf = self.data['confidence']
            conf_color = BRAND["success"] if conf in ['عالية', 'متوسطة'] else BRAND["accent"]
            self.draw.text((padding, y_start), f"🟡 الثقة: {conf}",
                          font=self.fonts["small"], fill=conf_color)

    def _wrap_text(self, text: str, max_width: int, font) -> list:
        """تقسيم النص الطويل إلى أسطر"""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = self.draw.textbbox((0, 0), test_line, font=font)
            
            if bbox[2] < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def draw_footer(self):
        """رسم التذييل مع هوية راصد"""
        padding = IMAGE["padding"]
        y_start = IMAGE["height"] - 180

        # خط فاصل
        self.draw.line([(padding, y_start), (IMAGE["width"]-padding, y_start)],
                      fill=BRAND["muted"], width=1)
        y_start += 30

        # التحذير
        warning_text = "⚠️ محتوى تعليمي وتحليلي فقط — لا يعد توصية استثمارية"
        self.draw.text((IMAGE["width"]//2, y_start), warning_text,
                      font=self.fonts["tiny"], fill=BRAND["muted"], anchor="mm")
        y_start += 35

        # التاريخ والوقت
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_text = f"🕐 {timestamp}"
        self.draw.text((IMAGE["width"]//2, y_start), time_text,
                      font=self.fonts["tiny"], fill=BRAND["text_secondary"], anchor="mm")
        y_start += 40

        # هوية راصد
        branding_text = f"👁️ {BRANDING['name']} | {BRANDING['slogan']}"
        self.draw.text((IMAGE["width"]//2, y_start), branding_text,
                      font=self.fonts["small"], fill=BRAND["accent"], anchor="mm")

    def save_image(self, output_path: str = None) -> bool:
        """حفظ الصورة"""
        output_path = output_path or DATA["output_image"]
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            self.img.save(output_file, "PNG", quality=95)
            print(f"✅ تم حفظ الصورة: {output_file.absolute()}")
            return True
        except Exception as e:
            print(f"❌ خطأ في حفظ الصورة: {e}")
            return False

    def generate(self, output_path: str = None) -> bool:
        """توليد الصورة الكاملة"""
        try:
            print("=" * 60)
            print(f"👁️ {BRANDING['name']} - مولّد الصور")
            print("=" * 60)
            print("🎨 بدء توليد الصورة...")

            if not self.load_data():
                return False

            self.create_base_image()
            self.draw_header()
            self.draw_stock_info()
            self.draw_targets()
            self.draw_analysis()
            self.draw_footer()

            return self.save_image(output_path)

        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """الدالة الرئيسية"""
    output_file = DATA["output_image"]
    if len(sys.argv) > 1:
        output_file = sys.argv[1]

    generator = RasedSignalGenerator("data/daily.json")
    success = generator.generate(output_file)

    if success:
        print("\n✅ تم التوليد بنجاح!")
        sys.exit(0)
    else:
        print("\n❌ فشل التوليد")
        sys.exit(1)


if __name__ == "__main__":
    main()
