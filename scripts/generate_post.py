#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rasid Auto Posting - Image Generator
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
    WIDTH = 900
    HEIGHT = 1200
    BG_COLOR = (10, 14, 39)
    CARD_BG = (26, 31, 58)
    GREEN_COLOR = (0, 208, 156)
    RED_COLOR = (255, 71, 87)
    GOLD_COLOR = (255, 165, 2)
    TEXT_COLOR = (255, 255, 255)
    TEXT_SECONDARY = (164, 176, 190)
    BORDER_COLOR = (255, 165, 2)
    
    def __init__(self, data_file: str = "data/daily.json", is_golden: bool = False):
        """
        تهيئة المولد
        
        Args:
            data_file: مسار ملف البيانات JSON
            is_golden: هل هذه إشارة ذهبية
        """
        self.data_file = Path(data_file)
        self.is_golden = is_golden
        self.data = None
        self.img = None
        self.draw = None
        
        # تحميل الخطوط
        self.font_xxlarge = self._load_font(48, bold=True)
        self.font_xlarge = self._load_font(36, bold=True)
        self.font_large = self._load_font(28, bold=True)
        self.font_medium = self._load_font(24)
        self.font_small = self._load_font(20)
        self.font_tiny = self._load_font(16)
    
    def _load_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """تحميل الخط مع fallback للخط الافتراضي"""
        font_paths = [
            f"fonts/Tajawal-{'Bold' if bold else 'Regular'}.ttf",
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        
        for path in font_paths:
            try:
                if Path(path).exists():
                    return ImageFont.truetype(path, size)
            except Exception:
                pass
        
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
            
            print(f"✅ تم تحميل البيانات بنجاح: {self.data.get('stock_name', '')}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ خطأ في تنسيق JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}")
            return False
    
    def create_base_image(self):
        """إنشاء الصورة الأساسية مع الخلفية والإطار"""
        self.img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        self.draw = ImageDraw.Draw(self.img)
        
        # رسم الإطار الذهبي الخارجي
        border_width = 3
        self.draw.rectangle(
            [(border_width, border_width), 
             (self.WIDTH - border_width, self.HEIGHT - border_width)],
            outline=self.BORDER_COLOR,
            width=border_width
        )
    
    def draw_header(self):
        """رسم الرأس (الشعار والعنوان)"""
        y_offset = 40
        
        # الشعار الدائري
        logo_size = 70
        logo_x = self.WIDTH // 2
        logo_y = y_offset + logo_size // 2
        
        # الدائرة الذهبية
        self.draw.ellipse(
            [(logo_x - logo_size//2, logo_y - logo_size//2),
             (logo_x + logo_size//2, logo_y + logo_size//2)],
            outline=self.GOLD_COLOR,
            width=3
        )
        
        # أيقونة داخل الدائرة (مبسطة)
        self.draw.text(
            (logo_x, logo_y),
            "📊",
            font=self.font_large,
            fill=self.GOLD_COLOR,
            anchor="mm"
        )
        
        # اسم المشروع
        y_offset += logo_size + 15
        self.draw.text(
            (self.WIDTH // 2, y_offset),
            "راصد",
            font=self.font_xlarge,
            fill=self.GOLD_COLOR,
            anchor="mm"
        )
        
        # النص تحت الشعار
        y_offset += 45
        if self.is_golden:
            subtitle = "تحليل ذكي متعمق - 20 يوم تاريخي"
            badge_text = "⭐ اشارة ذهبية"
        else:
            subtitle = "تحليل فني وتعليمي لسوق الأسهم السعودية"
            badge_text = "📊 اشارة يومية"
        
        self.draw.text(
            (self.WIDTH // 2, y_offset),
            subtitle,
            font=self.font_small,
            fill=self.TEXT_SECONDARY,
            anchor="mm"
        )
        
        # شارة نوع الإشارة
        y_offset += 35
        badge_width = 180
        badge_height = 35
        badge_x1 = (self.WIDTH - badge_width) // 2
        badge_y1 = y_offset - badge_height // 2
        
        self.draw.rounded_rectangle(
            [(badge_x1, badge_y1), (badge_x1 + badge_width, badge_y1 + badge_height)],
            radius=18,
            fill=self.GOLD_COLOR
        )
        
        self.draw.text(
            ((self.WIDTH) // 2, y_offset),
            badge_text,
            font=self.font_medium,
            fill=self.BG_COLOR,
            anchor="mm"
        )
        
        # التاريخ والوقت
        now = datetime.now()
        date_text = now.strftime("%Y/%m/%d")
        time_text = now.strftime("%I:%M %p")
        
        self.draw.text(
            (self.WIDTH - 90, 30),
            date_text,
            font=self.font_tiny,
            fill=self.TEXT_SECONDARY,
            anchor="rm"
        )
        
        self.draw.text(
            (90, 30),
            time_text,
            font=self.font_tiny,
            fill=self.TEXT_SECONDARY,
            anchor="lm"
        )
        
        # خط فاصل
        y_offset += 55
        self.draw.line(
            [(80, y_offset), (self.WIDTH - 80, y_offset)],
            fill=self.GOLD_COLOR,
            width=2
        )
    
    def draw_stock_name(self):
        """رسم اسم السهم والرمز"""
        if not self.data:
            return
        
        y_offset = 330
        
        # اسم السهم والرمز
        stock_name = self.data.get('stock_name', '')
        symbol = self.data.get('symbol', '')
        stock_text = f"{stock_name} - {symbol}"
        
        self.draw.text(
            (self.WIDTH // 2, y_offset),
            stock_text,
            font=self.font_xxlarge,
            fill=self.TEXT_COLOR,
            anchor="mm"
        )
        
        # خط فاصل تحت الاسم
        y_offset += 50
        self.draw.line(
            [(self.WIDTH // 2 - 150, y_offset), (self.WIDTH // 2 + 150, y_offset)],
            fill=self.GOLD_COLOR,
            width=2
        )
    
    def _draw_data_row(self, y: int, label: str, value: str, 
                       value_color: tuple = None, icon: str = "",
                       left_badge: str = None):
        """رسم صف بيانات مع بطاقة"""
        
        card_height = 70
        card_margin = 60
        card_x1 = card_margin
        card_y1 = y - card_height // 2
        card_x2 = self.WIDTH - card_margin
        card_y2 = y + card_height // 2
        
        # خلفية البطاقة
        self.draw.rounded_rectangle(
            [(card_x1, card_y1), (card_x2, card_y2)],
            radius=12,
            fill=self.CARD_BG
        )
        
        # الأيقونة على اليمين
        if icon:
            self.draw.text(
                (card_x2 - 40, y),
                icon,
                font=self.font_medium,
                fill=self.TEXT_SECONDARY,
                anchor="rm"
            )
            label_x = card_x2 - 70
        else:
            label_x = card_x2 - 30
        
        # النص (label على اليمين، value على اليسار)
        self.draw.text(
            (label_x, y),
            label,
            font=self.font_medium,
            fill=self.TEXT_SECONDARY,
            anchor="rm"
        )
        
        # القيمة
        value_color = value_color or self.TEXT_COLOR
        value_x = card_x1 + 30
        
        # إذا كان هناك badge على اليسار (للنسبة المئوية)
        if left_badge:
            # حساب عرض القيمة
            bbox = self.draw.textbbox((0, 0), value, font=self.font_large)
            value_width = bbox[2] - bbox[0]
            
            # رسم القيمة
            self.draw.text(
                (value_x, y),
                value,
                font=self.font_large,
                fill=value_color,
                anchor="lm"
            )
            
            # رسمbadge
            badge_x = value_x + value_width + 15
            badge_width = 70
            badge_height = 30
            
            badge_color = self.GREEN_COLOR if '+' in left_badge else self.RED_COLOR
            
            self.draw.rounded_rectangle(
                [(badge_x, y - badge_height//2), 
                 (badge_x + badge_width, y + badge_height//2)],
                radius=8,
                outline=badge_color,
                width=2
            )
            
            self.draw.text(
                (badge_x + badge_width//2, y),
                left_badge,
                font=self.font_small,
                fill=badge_color,
                anchor="mm"
            )
        else:
            self.draw.text(
                (value_x, y),
                value,
                font=self.font_large,
                fill=value_color,
                anchor="lm"
            )
        
        return y + card_height + 12
    
    def draw_price_data(self):
        """رسم بيانات الأسعار"""
        if not self.data:
            return
        
        y_offset = 420
        
        # السعر الحالي
        current_price = self.data.get('current_price', '')
        self._draw_data_row(
            y_offset,
            "السعر الحالي:",
            f"{current_price} ريال",
            icon="📊",
            value_color=self.GOLD_COLOR
        )
        
        # نقطة الدخول
        y_offset += 82
        entry_point = self.data.get('entry_point', '')
        self._draw_data_row(
            y_offset,
            "نقطة الدخول:",
            f"{entry_point} ريال",
            icon="🎯",
            value_color=self.GOLD_COLOR
        )
        
        # الهدف الأول
        y_offset += 82
        target1 = self.data.get('target1', '')
        target1_pct = self.data.get('target1_percent', '')
        self._draw_data_row(
            y_offset,
            "الهدف الأول:",
            f"{target1} ريال",
            icon="🎯",
            value_color=self.GREEN_COLOR,
            left_badge=f"+{target1_pct}%" if target1_pct else None
        )
        
        # الهدف الثاني
        y_offset += 82
        target2 = self.data.get('target2', '')
        target2_pct = self.data.get('target2_percent', '')
        self._draw_data_row(
            y_offset,
            "الهدف الثاني:",
            f"{target2} ريال",
            icon="🎯",
            value_color=self.GREEN_COLOR,
            left_badge=f"+{target2_pct}%" if target2_pct else None
        )
        
        # وقف الخسارة
        y_offset += 82
        stop_loss = self.data.get('stop_loss', '')
        stop_loss_pct = self.data.get('stop_loss_percent', '')
        self._draw_data_row(
            y_offset,
            "وقف الخسارة:",
            f"{stop_loss} ريال",
            icon="❌",
            value_color=self.RED_COLOR,
            left_badge=f"-{stop_loss_pct}%" if stop_loss_pct else None
        )
    
    def draw_indicators(self):
        """رسم المؤشرات الفنية"""
        if not self.data:
            return
        
        y_offset = 920
        
        # بطاقة المؤشرات
        card_height = 60
        card_margin = 60
        card_x1 = card_margin
        card_y1 = y_offset - card_height // 2
        card_x2 = self.WIDTH - card_margin
        card_y2 = y_offset + card_height // 2
        
        self.draw.rounded_rectangle(
            [(card_x1, card_y1), (card_x2, card_y2)],
            radius=12,
            fill=self.CARD_BG
        )
        
        # RSI
        rsi = self.data.get('rsi', '')
        rsi_x = card_x1 + 100
        self.draw.text(
            (rsi_x, y_offset),
            f"RSI {rsi}",
            font=self.font_medium,
            fill=self.TEXT_COLOR,
            anchor="mm"
        )
        
        # Volume
        volume = self.data.get('volume_ratio', '')
        vol_x = self.WIDTH // 2
        self.draw.text(
            (vol_x, y_offset),
            f"Vol {volume}x",
            font=self.font_medium,
            fill=self.GOLD_COLOR,
            anchor="mm"
        )
        
        # Score
        score = self.data.get('score', '')
        score_x = card_x2 - 100
        self.draw.text(
            (score_x, y_offset),
            f"Score {score}",
            font=self.font_medium,
            fill=self.TEXT_COLOR,
            anchor="mm"
        )
    
    def draw_technical_reading(self):
        """رسم القراءة الفنية"""
        if not self.data:
            return
        
        y_offset = 1010
        
        technical_reading = self.data.get('technical_reading', '')
        
        if technical_reading:
            # تقسيم النص إلى أسطر
            words = technical_reading.split()
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
            
            # رسم القراءة في صندوق
            card_margin = 60
            card_x1 = card_margin
            card_x2 = self.WIDTH - card_margin
            
            # حساب ارتفاع البطاقة
            line_height = 28
            total_height = len(lines) * line_height + 30
            
            card_y1 = y_offset - 15
            card_y2 = y_offset + total_height
            
            self.draw.rounded_rectangle(
                [(card_x1, card_y1), (card_x2, card_y2)],
                radius=10,
                outline=self.GOLD_COLOR,
                width=1
            )
            
            # رسم الأسطر
            for i, line in enumerate(lines[:4]):  # الحد الأقصى 4 أسطر
                line_y = y_offset + i * line_height
                self.draw.text(
                    (card_x1 + 15, line_y),
                    line,
                    font=self.font_tiny,
                    fill=self.TEXT_SECONDARY,
                    anchor="lm"
                )
    
    def draw_footer(self):
        """رسم التذييل"""
        y_offset = self.HEIGHT - 90
        
        # خط فاصل
        self.draw.line(
            [(self.WIDTH // 2 - 150, y_offset), (self.WIDTH // 2 + 150, y_offset)],
            fill=self.GOLD_COLOR,
            width=2
        )
        
        y_offset += 25
        
        # نص التحذير
        warning_text = "محتوى تعليمي وتحليلي فقط - لا يعد توصية استثمارية"
        self.draw.text(
            (self.WIDTH // 2, y_offset),
            warning_text,
            font=self.font_tiny,
            fill=self.TEXT_SECONDARY,
            anchor="mm"
        )
        
        # رابط القناة
        y_offset += 35
        channel_text = "t.me/TASI_Smart"
        
        badge_width = 200
        badge_height = 30
        badge_x1 = (self.WIDTH - badge_width) // 2
        badge_y1 = y_offset - badge_height // 2
        
        self.draw.rounded_rectangle(
            [(badge_x1, badge_y1), (badge_x1 + badge_width, badge_y1 + badge_height)],
            radius=15,
            outline=self.GOLD_COLOR,
            width=2
        )
        
        self.draw.text(
            (self.WIDTH // 2, y_offset),
            channel_text,
            font=self.font_small,
            fill=self.GOLD_COLOR,
            anchor="mm"
        )
    
    def save_image(self, output_path: str = "output.png") -> bool:
        """
        حفظ الصورة
        
        Args:
            output_path: مسار الحفظ
        
        Returns:
            bool: True إذا نجح الحفظ
        """
        try:
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
            self.draw_stock_name()
            self.draw_price_data()
            self.draw_indicators()
            self.draw_technical_reading()
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
    print("📊 Rasid Auto Posting - Image Generator")
    print("=" * 60)
    
    # تحديد مسار المخرج من المعاملات
    output_file = "output.png"
    is_golden = False
    
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        is_golden = sys.argv[2].lower() in ['golden', 'true', '1']
    
    # إنشاء المولد
    generator = SignalImageGenerator("data/daily.json", is_golden=is_golden)
    
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

