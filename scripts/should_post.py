import json
import sys
from datetime import datetime

DATA_FILE = "data/daily.json"

# ─── معايير الإشارة اليومية ───────────────────────────
MIN_SCORE          = 75
RSI_MIN            = 45
RSI_MAX            = 70
MIN_VOLUME_RATIO   = 1.3
MIN_VOLUME_HIGH_RR = 1.1
MIN_RR             = 1.2

# ─── معايير الإشارة الذهبية (قبل السوق) ──────────────
GOLDEN_MIN_SCORE = 45   # أقل لأن التحليل تاريخي
GOLDEN_RSI_MIN   = 35
GOLDEN_RSI_MAX   = 75
GOLDEN_MIN_RR    = 0.8  # مرن — البيانات تاريخية


def check_golden(data):
    """قواعد خاصة للإشارة الذهبية قبل السوق"""
    score  = data.get("score", 0)
    rsi    = data.get("rsi", 50)
    rr     = data.get("rr", 0)
    symbol = data.get("symbol", "")
    name   = data.get("stock_name", "")
    stype  = data.get("signal_type", "")

    reasons_fail = []

    if score < GOLDEN_MIN_SCORE:
        reasons_fail.append(f"Score {score} < {GOLDEN_MIN_SCORE}")
    if not (GOLDEN_RSI_MIN <= rsi <= GOLDEN_RSI_MAX):
        reasons_fail.append(f"RSI {rsi:.0f} خارج النطاق ({GOLDEN_RSI_MIN}-{GOLDEN_RSI_MAX})")
    if rr < GOLDEN_MIN_RR:
        reasons_fail.append(f"R:R {rr:.2f} < {GOLDEN_MIN_RR}")

    print(f"\n{'='*55}")
    print(f"فحص الإشارة الذهبية: {name} ({symbol})")
    print(f"النوع: {stype}")
    print(f"{'='*55}")
    print(f"  Score : {score:>6}  {'OK' if score >= GOLDEN_MIN_SCORE else 'X':>3} (min {GOLDEN_MIN_SCORE})")
    print(f"  RSI   : {rsi:>6.0f}  {'OK' if GOLDEN_RSI_MIN <= rsi <= GOLDEN_RSI_MAX else 'X':>3} ({GOLDEN_RSI_MIN}-{GOLDEN_RSI_MAX})")
    print(f"  R:R   : {rr:>6.2f}  {'OK' if rr >= GOLDEN_MIN_RR else 'X':>3} (min {GOLDEN_MIN_RR})")
    print(f"  Volume: تُتجاهل للإشارة الذهبية (بيانات تاريخية)")

    if reasons_fail:
        print(f"\nالإشارة الذهبية لا تستوفي المعايير:")
        for r in reasons_fail:
            print(f"   - {r}")
        print(f"\nتم تخطي النشر\n")
        return False

    print(f"\nالإشارة الذهبية تستوفي المعايير — سيتم النشر!\n")
    return True


def check_daily(data):
    """قواعد الإشارة اليومية الاعتيادية"""
    score        = data.get("score", 0)
    rsi          = data.get("rsi", 50)
    volume_ratio = data.get("volume_ratio", 0)
    rr           = data.get("rr", 0)
    symbol       = data.get("symbol", "")
    name         = data.get("stock_name", "")

    vol_threshold = MIN_VOLUME_HIGH_RR if rr >= 3 else MIN_VOLUME_RATIO
    reasons_fail  = []

    if score < MIN_SCORE:
        reasons_fail.append(f"Score {score} < {MIN_SCORE}")
    if not (RSI_MIN <= rsi <= RSI_MAX):
        reasons_fail.append(f"RSI {rsi:.0f} خارج النطاق ({RSI_MIN}-{RSI_MAX})")
    if volume_ratio < vol_threshold:
        if score >= 85 and volume_ratio == 0.0:
            print(f"  ** Volume = 0 (مشكلة API) — مقبول لـ Score {score}")
        else:
            reasons_fail.append(f"Volume {volume_ratio:.1f}x < {vol_threshold}x")
    if rr < MIN_RR:
        if score >= 85 and rr >= 1.0:
            print(f"  ** R:R {rr:.2f} مقبول لـ Score {score} — Claude يقرر")
        else:
            reasons_fail.append(f"R:R {rr:.2f} < {MIN_RR} (الربح أقل من الخسارة)")

    print(f"\n{'='*55}")
    print(f"فحص جودة الاشارة: {name} ({symbol})")
    print(f"{'='*55}")
    print(f"  Score        : {score:>6}  {'OK' if score >= MIN_SCORE else 'X':>3} (min {MIN_SCORE})")
    print(f"  RSI          : {rsi:>6.0f}  {'OK' if RSI_MIN <= rsi <= RSI_MAX else 'X':>3} ({RSI_MIN}-{RSI_MAX})")
    vol_ok = volume_ratio >= vol_threshold or (score >= 85 and volume_ratio == 0.0)
    print(f"  Volume Ratio : {volume_ratio:>5.1f}x  {'OK' if vol_ok else 'X':>3} (min {vol_threshold}x)")
    rr_ok = rr >= MIN_RR or (score >= 85 and rr >= 1.0)
    print(f"  R:R          : {rr:>6.2f}  {'OK' if rr_ok else 'X':>3} (min {MIN_RR})")

    if rr >= 3:
        print(f"  ** R:R ممتاز — تخفيف معيار الحجم إلى {MIN_VOLUME_HIGH_RR}x")

    if reasons_fail:
        print(f"\nالاشارة لا تستوفي المعايير:")
        for r in reasons_fail:
            print(f"   - {r}")
        print(f"\nتم تخطي النشر اليوم\n")
        return False

    print(f"\nالاشارة تستوفي جميع المعايير — سيتم النشر!\n")
    return True


if __name__ == "__main__":
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"خطا في قراءة {DATA_FILE}: {e}")
        sys.exit(1)

    # فحص حداثة البيانات
    generated_at = data.get("generated_at", "")
    today = datetime.now().strftime("%Y-%m-%d")
    if not generated_at.startswith(today):
        print(f"البيانات قديمة ({generated_at or 'غير محدد'}) — تم الانتهاء")
        sys.exit(1)

    # توجيه حسب نوع الإشارة
    signal_type = data.get("type", "")
    is_golden   = signal_type == "اشارة ذهبية"

    if is_golden:
        print("  نوع الإشارة: ذهبية — تطبيق معايير ما قبل السوق")
        passed = check_golden(data)
    else:
        print("  نوع الإشارة: يومية — تطبيق المعايير الاعتيادية")
        passed = check_daily(data)

    sys.exit(0 if passed else 1)
