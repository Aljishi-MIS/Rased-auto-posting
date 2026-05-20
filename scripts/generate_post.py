#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modareb Auto Posting - Image Generator
Generates professional trading signal images from JSON data
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


class SignalImageGenerator:
    """فئة لتوليد صور إشارات التداول"""
    
    # الثوابت
    WIDTH = 1080
    HEIGHT = 1920
    BG_COLOR = "#0a0e27"
    CARD_BG = "#1a1f3a"
    GREEN_COLOR = "#00d09c"
    RED_COLOR = "#ff4757"
    GOLD_COLOR = "#ffa502"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#a4b0be"
    
    def __init__(self, data_file: str = "data/daily.json"):
        """
        تهيئة المولد
        
        Args:
            data_file: مسار ملف البيانات JSON
        """
        self.data_file = Path(data_file)
        self.data = None
        self.img = None
        self.draw = None
        
        # تحميل الخطوط (حاول استخدام خطوط عربية إن وجدت)
        self.font_large = self._load_font("fonts/Tajawal-Bold.ttf", 48)
        self.font_medium = self._load_font("fonts/Tajawal-Regular.ttf", 32)
        self.font_small = self._load_font("fonts/Tajawal-Regular.ttf", 24)
        self.font_tiny = self._load_font("fonts/Tajawal-Regular.ttf", 18)
    
    def _load_font(self, font_path: str, size: int) -> ImageFont.FreeTypeFont:
        """تحميل الخط مع fallback للخط الافتراضي"""
        try:
            if Path(font_path).exists():
                return ImageFont.truetype(font_path, size)
        except Exception:
            pass
        
        # الخط الافتراضي
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()
    
    def load_data(self) -> bool:
        """
        تحميل البيانات من ملف JSON
        
        Returns:
            bool: True إذا نجح التحميل
        """
        try:
            if not self.data_file.exists():
                print(f"❌ ملف البيانات غير موجود: {self.data_file}")
                return False
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # التحقق من الحقول المطلوبة
            required_fields = ['stock_name', 'stock_symbol', 'current_price', 
                             'entry_point', 'target1', 'stop_loss']
            
            for field in required_fields:
                if field not in self.data:
                    print(f"❌ الحقل المطلوب مفقود: {field}")
                    return False
            
            print(f"✅ تم تحميل البيانات بنجاح: {self.data['stock_name']}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ خطأ في تنسيق JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            return False
    
    def create_base_image(self):
        """إنشاء الصورة الأساسية مع الخلفية"""
        self.img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        self.draw = ImageDraw.Draw(self.img)
    
    def draw_header(self):
        """رسم الرأس (الشعار والعنوان)"""
        # الشعار
        y_offset = 60
        self.draw.text((self.WIDTH//2, y_offset), "📊 إشارة اليوم — مضارب", 
                      font=self.font_large, fill=self.TEXT_COLOR, anchor="mm")
        
        # الخط الفاصل
        y_offset += 80
        self.draw.line([(80, y_offset), (self.WIDTH-80, y_offset)], 
                      fill=self.GREEN_COLOR, width=3)
    
    def draw_stock_info(self):
        """رسم معلومات السهم"""
        if not self.data:
            return
        
        y_start = 200
        
        # اسم السهم والرمز
        stock_text = f"{self.data['stock_name']} — {self.data['stock_symbol']}"
        self.draw.text((self.WIDTH//2, y_start), stock_text,
                      font=self.font_large, fill=self.GREEN_COLOR, anchor="mm")
        
        # القطاع
        if 'sector' in self.data:
            y_start += 60
            self.draw.text((self.WIDTH//2, y_start), f"🏢 القطاع: {self.data['sector']}",
                          font=self.font_medium, fill=self.TEXT_SECONDARY, anchor="mm")
        
        # السعر الحالي
        y_start += 100
        self._draw_card(f"💰 السعر الحالي: {self.data['current_price']} ريال", 
                       y_start, self.GOLD_COLOR)
    
    def _draw_card(self, text: str, y: int, color: str = None):
        """رسم بطاقة نصية"""
        card_width = self.WIDTH - 160
        card_height = 80
        x1 = 80
        y1 = y - card_height // 2
        x2 = x1 + card_width
        y2 = y1 + card_height
        
        # خلفية البطاقة
        self.draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=15, 
                                   fill=self.CARD_BG)
        
        # النص
        text_color = color or self.TEXT_COLOR
        bbox = self.draw.textbbox((0, 0), text, font=self.font_medium)
        text_width = bbox[2] - bbox[0]
        x_text = (x1 + x2) // 2
        y_text = (y1 + y2) // 2
        
        self.draw.text((x_text, y_text), text, font=self.font_medium, 
                      fill=text_color, anchor="mm")
    
    def draw_targets(self):
        """رسم الأهداف"""
        if not self.data:
            return
        
        y_start = 550
        
        # عنوان الأهداف
        self.draw.text((80, y_start), "🎯 الأهداف",
                      font=self.font_medium, fill=self.TEXT_COLOR)
        
        # الهدف الأول
        if 'target1' in self.data:
            y_start += 70
            target1_text = f"🟢 الهدف الأول: {self.data['target1']} ريال"
            if 'target1_percent' in self.data:
                target1_text += f" (+{self.data['target1_percent']}%)"
            self._draw_card(target1_text, y_start, self.GREEN_COLOR)
        
        # الهدف الثاني
        if 'target2' in self.data:
            y_start += 90
            target2_text = f"🟢 الهدف الثاني: {self.data['target2']} ريال"
            if 'target2_percent' in self.data:
                target2_text += f" (+{self.data['target2_percent']}%)"
            self._draw_card(target2_text, y_start, self.GREEN_COLOR)
        
        # وقف الخسارة
        if 'stop_loss' in self.data:
            y_start += 90
            stop_text = f"🔴 وقف الخسارة: {self.data['stop_loss']} ريال"
            if 'stop_loss_percent' in self.data:
                stop_text += f" (-{self.data['stop_loss_percent']}%)"
            self._draw_card(stop_text, y_start, self.RED_COLOR)
    
    def draw_analysis(self):
        """رسم التحليل الفني"""
        if not self.data:
            return
        
        y_start = 1050
        
        # الإطار الزمني
        if 'timeframe' in self.data:
            self.draw.text((80, y_start), f"⏱ الإطار الزمني: {self.data['timeframe']}",
                          font=self.font_small, fill=self.TEXT_SECONDARY)
            y_start += 50
        
        # الزخم
        if 'momentum' in self.data:
            self.draw.text((80, y_start), f"⚡ الزخم: {self.data['momentum']}",
                          font=self.font_small, fill=self.GOLD_COLOR)
            y_start += 45
        
        # RS Rank
        if 'rs_rank' in self.data:
            self.draw.text((80, y_start), f"📈 RS Rank: {self.data['rs_rank']}",
                          font=self.font_small, fill=self.TEXT_COLOR)
            y_start += 45
        
        # Score
        if 'score' in self.data:
            self.draw.text((80, y_start), f"🔢 Score: {self.data['score']}/100",
                          font=self.font_small, fill=self.TEXT_COLOR)
            y_start += 60
        
        # القراءة الفنية
        if 'technical_reading' in self.data:
            self.draw.text((80, y_start), "📌 قراءة فنية:",
                          font=self.font_small, fill=self.TEXT_COLOR)
            y_start += 40
            
            # تقسيم النص الطويل
            reading = self.data['technical_reading']
            words = reading.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = self.draw.textbbox((0, 0), test_line, font=self.font_tiny)
                if bbox[2] < (self.WIDTH - 160):
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            for line in lines[:6]:  # الحد الأقصى 6 أسطر
                self.draw.text((80, y_start), f"   • {line}",
                              font=self.font_tiny, fill=self.TEXT_SECONDARY)
                y_start += 35
        
        # الثقة
        if 'confidence' in self.data:
            y_start += 30
            conf_color = self.GREEN_COLOR if self.data['confidence'] in ['عالية', 'متوسطة'] else self.GOLD_COLOR
            self.draw.text((80, y_start), f"🟡 الثقة: {self.data['confidence']}",
                          font=self.font_small, fill=conf_color)
    
    def draw_footer(self):
        """رسم التذييل"""
        y_start = self.HEIGHT - 200
        
        # التحذير
        warning_text = "⚠️ محتوى تعليمي وتحليلي فقط — لا يعد توصية استثمارية"
        bbox = self.draw.textbbox((0, 0), warning_text, font=self.font_tiny)
        text_width = bbox[2] - bbox[0]
        x_pos = (self.WIDTH - text_width) // 2
        
        self.draw.text((x_pos, y_start), warning_text,
                      font=self.font_tiny, fill=self.TEXT_SECONDARY)
        
        # التاريخ والوقت
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_text = f"🕐 {timestamp}"
        bbox = self.draw.textbbox((0, 0), time_text, font=self.font_tiny)
        text_width = bbox[2] - bbox[0]
        x_pos = (self.WIDTH - text_width) // 2
        
        self.draw.text((x_pos, y_start + 40), time_text,
                      font=self.font_tiny, fill=self.TEXT_SECONDARY)
        
        # الشعار
        self.draw.text((self.WIDTH//2, y_start + 90), "📈 سجل الأداء",
                      font=self.font_small, fill=self.GREEN_COLOR, anchor="mm")
    
    def save_image(self, output_path: str = "output.png") -> bool:
        """
        حفظ الصورة
        
        Args:
            output_path: مسار الحفظ
            
        Returns:
            bool: True إذا نجح الحفظ
        """
        try:
            # التأكد من وجود المجلد
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.img.save(output_file, "PNG", quality=95)
            print(f"✅ تم حفظ الصورة: {output_file.absolute()}")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في حفظ الصورة: {e}")
            return False
    
    def generate(self, output_path: str = "output.png") -> bool:
        """
        توليد الصورة الكاملة
        
        Args:
            output_path: مسار الحفظ
            
        Returns:
            bool: True إذا نجح التوليد
        """
        try:
            print("🎨 بدء توليد الصورة...")
            
            # تحميل البيانات
            if not self.load_data():
                return False
            
            # إنشاء الصورة
            self.create_base_image()
            self.draw_header()
            self.draw_stock_info()
            self.draw_targets()
            self.draw_analysis()
            self.draw_footer()
            
            # الحفظ
            return self.save_image(output_path)
            
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("📊 Modareb Auto Posting - Image Generator")
    print("=" * 60)
    
    # تحديد مسار المخرج من المعاملات
    output_file = "output.png"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    # إنشاء المولد
    generator = SignalImageGenerator("data/daily.json")
    
    # التوليد
    success = generator.generate(output_file)
    
    if success:
        print("\n✅ تم التوليد بنجاح!")
        sys.exit(0)
    else:
        print("\n❌ فشل التوليد")
        sys.exit(1)


if __name__ == "__main__":
    main()

