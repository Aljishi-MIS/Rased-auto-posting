"""
should_post.py  ─ مُحدَّث
==========================
شروط النشر الجديدة:
  ✅ Score ≥ 78  |  RSI 42-68  |  حجم ≥ 2×  |  R:R ≥ 2.5  |  هدف ثانٍ ≥ 10%
  ⭐ ذهبية: Score ≥ 88  |  حجم ≥ 2.5×  |  R:R ≥ 3  |  هدف ثانٍ ≥ 12%
"""

import json, os, sys
from datetime import datetime

DAILY_FILE  = "data/daily.json"
GOLDEN_FILE = "data/golden_signal.json"

MIN_SCORE        = 78
MIN_RSI          = 42
MAX_RSI          = 68
MIN_VOLUME_RATIO = 2.0
MIN_RR           = 2.5

GOLDEN_MIN_SCORE = 88
GOLDEN_MIN_VOL   = 2.5
GOLDEN_MIN_RR    = 3.0


def load_json(path):
    if not os.path.exists(path): return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except: return None


def check_quality(data, is_golden=False):
    fails      = []
    score      = float(data.get("score",        0))
    rsi        = float(data.get("rsi",          50))
    vol_ratio  = float(data.get("volume_ratio", 0))
    rr         = float(data.get("rr",           0))
    t2_pct     = float(data.get("target2_pct",  0))

    min_score = GOLDEN_MIN_SCORE if is_golden else MIN_SCORE
    min_vol   = GOLDEN_MIN_VOL   if is_golden else MIN_VOLUME_RATIO
    min_rr    = GOLDEN_MIN_RR    if is_golden else MIN_RR
    min_t2    = 12.0             if is_golden else 10.0

    if score     < min_score:              fails.append(f"Score منخفض ({score:.0f} < {min_score})")
    if not (MIN_RSI <= rsi <= MAX_RSI):    fails.append(f"RSI خارج النطاق ({rsi:.1f}) — المقبول: {MIN_RSI}-{MAX_RSI}")
    if vol_ratio < min_vol:                fails.append(f"حجم ضعيف ({vol_ratio:.1f}x < {min_vol}x)")
    if rr        < min_rr:                 fails.append(f"R:R منخفض ({rr:.1f} < {min_rr})")
    if t2_pct    < min_t2:                 fails.append(f"هدف ثانٍ أقل من {min_t2}% (= {t2_pct}%)")

    now_h = datetime.now().hour
    now_m = datetime.now().minute
    if not ((now_h > 10 or (now_h == 10 and now_m >= 0)) and
            (now_h < 15 or (now_h == 15 and now_m <= 0))):
        fails.append("خارج ساعات السوق (10:00 - 15:00)")

    return len(fails) == 0, fails


def main():
    print("=" * 60)
    print("  فحص جودة الإشارة قبل النشر")
    print("=" * 60)

    daily = load_json(DAILY_FILE)
    if not daily:
        print("  ❌ daily.json غير موجود"); sys.exit(1)

    print(f"\n  السهم    : {daily.get('stock_name','')} ({daily.get('symbol','')})")
    print(f"  Score    : {daily.get('score',0)}")
    print(f"  RSI      : {daily.get('rsi',0)}")
    print(f"  حجم×     : {daily.get('volume_ratio',0)}")
    print(f"  R:R      : {daily.get('rr',0)}")
    print(f"  هدف ثانٍ: +{daily.get('target2_pct',0)}%")
    print(f"  ملاحظة  : {daily.get('note','')}")

    passed, fails = check_quality(daily, is_golden=False)

    if passed:
        print("\n  ✅ الإشارة اجتازت الشروط — سيتم النشر")
    else:
        print("\n  ⛔ تم تخطي النشر — الأسباب:")
        for r in fails: print(f"      • {r}")
        sys.exit(1)

    golden = load_json(GOLDEN_FILE)
    if golden:
        g_passed, g_fails = check_quality(golden, is_golden=True)
        print(f"\n  ─── فحص الإشارة الذهبية ⭐ ───────────────────────")
        print(f"  السهم : {golden.get('stock_name','')}  Score: {golden.get('score',0)}  هدف: +{golden.get('target2_pct',0)}%")
        if g_passed: print("  ✅ الإشارة الذهبية جاهزة")
        else:
            for r in g_fails: print(f"      • {r}")
    else:
        print("\n  ℹ️  لا إشارة ذهبية اليوم")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
