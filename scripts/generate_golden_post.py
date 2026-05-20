#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rasid Auto Posting - Golden Signal Image Generator
Generates professional golden trading signal images
"""

import sys
from generate_post import SignalImageGenerator


def main():
    """الدالة الرئيسية للإشارة الذهبية"""
    print("=" * 60)
    print("⭐ Rasid Auto Posting - Golden Signal Generator")
    print("=" * 60)
    
    # تحديد مسار المخرج من المعاملات
    output_file = "output_golden.png"
    
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    # إنشاء المولد مع تفعيل وضع الإشارة الذهبية
    generator = SignalImageGenerator("data/daily.json", is_golden=True)
    
    # التوليد
    success = generator.generate(output_file)
    
    if success:
        print("\n✅ تم توليد الإشارة الذهبية بنجاح!")
        sys.exit(0)
    else:
        print("\n❌ فشل التوليد")
        sys.exit(1)


if __name__ == "__main__":
    main()

