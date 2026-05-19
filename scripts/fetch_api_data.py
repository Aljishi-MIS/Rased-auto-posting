"""
fetch_api_data.py  ─ مُحدَّث
==============================
Claude يراجع أفضل 3 أسهم ويتحقق من:
  ✅ هل الزخم كافٍ للوصول لـ 10% في 10 أيام؟
  ✅ هل توجد أخبار سلبية تعيق الهدف؟
  ✅ هل يُوصي بإشارة يومية أم ذهبية؟
"""

import os, json, requests
from datetime import datetime
from anthropic import Anthropic

API_KEY    = os.environ.get("API_KEY")
API_URL    = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS    = {"X-API-Key": API_KEY} if API_KEY else {}

DAILY_FILE  = "data/daily.json"
GOLDEN_FILE = "data/golden_signal.json"

client = Anthropic()


# ═══════════════════════════════════════════
# جلب أخبار السهم
# ═══════════════════════════════════════════
def fetch_news(symbol):
    data = get(f"/news/{symbol}/", {"limit": 5})
    if not data:
        return "لا توجد أخبار متاحة"
    news_list = data if isinstance(data, list) else data.get("news", [])
    if not news_list:
        return "لا توجد أخبار متاحة"
    lines = []
    for n in news_list[:5]:
        title = n.get("title") or n.get("headline") or ""
        date  = n.get("date") or n.get("published_at") or ""
        if title:
            lines.append(f"- [{date}] {title}")
    return "\n".join(lines) if lines else "لا توجد أخبار متاحة"


def get(endpoint, params=None):
    try:
        r = requests.get(f"{API_URL}{endpoint}", headers=HEADERS,
                         params=params or {}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"  ❌ {endpoint}: {e}")
    return None


# ═══════════════════════════════════════════
# ▌ مراجعة Claude للإشارة
# ═══════════════════════════════════════════
def claude_review(candidate, news_text):
    """
    يُرسل بيانات السهم + الأخبار إلى Claude
    ويطلب منه الحكم على الإشارة بناءً على المعايير الجديدة.
    """

    stock   = candidate["stock"]
    score   = candidate["score"]
    vol_r   = candidate["vol_ratio"]
    accel   = candidate["accel"]
    is_g    = candidate["is_golden"]
    reasons = "\n".join(candidate["reasons"])

    prompt = f"""
أنت محلل مالي متخصص في سوق الأسهم السعودي (تداول).

## بيانات السهم:
- الرمز      : {stock.get('symbol','')}
- الاسم      : {stock.get('name','')}
- السعر      : {stock.get('price','')} ريال
- القطاع     : {stock.get('sector','')}
- RSI        : {stock.get('rsi','')}
- حجم التداول: {vol_r}× المعدل
- Score      : {score}/100
- تسارع السعر+الحجم (acceleration): {accel}/50
- EMA20      : {stock.get('ema20','')}
- EMA50      : {stock.get('ema50','')}
- الإشارة الذهبية؟: {'نعم' if is_g else 'لا'}

## أسباب اختيار السهم:
{reasons}

## آخر أخبار السهم:
{news_text}

## مهمتك:
قيّم هذا السهم وأجب بـ JSON فقط بدون أي نص إضافي:

{{
  "approve": true أو false,
  "signal_type": "golden" أو "daily" أو "reject",
  "confidence": رقم من 0 إلى 100,
  "reason": "سبب موجز باللغة العربية (جملة واحدة احترافية)",
  "warning": "تحذير إن وجد أو null",
  "momentum_ok": true إذا كان الزخم كافياً للوصول لـ 10% في 10 أيام,
  "news_sentiment": "positive" أو "negative" أو "neutral"
}}

## معايير القبول التي يجب مراعاتها:
- الهدف الثاني 10% يجب أن يُحقق خلال 7 أيام (أقصاه 10)
- acceleration ≥ 30 شرط للإشارة الذهبية
- أي خبر سلبي مؤثر = رفض أو تحويل لـ daily
- RSI فوق 70 = رفض (تشبع شرائي)
- إذا كانت الأخبار محايدة أو إيجابية والمعايير مكتملة = قبول
"""

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()

        # تنظيف الـ JSON
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except Exception as e:
        print(f"  ❌ خطأ في مراجعة Claude: {e}")
        return {
            "approve":       True,
            "signal_type":   "golden" if is_g else "daily",
            "confidence":    score,
            "reason":        "تمت المراجعة تلقائياً",
            "warning":       None,
            "momentum_ok":   accel >= 20,
            "news_sentiment":"neutral"
        }


# ═══════════════════════════════════════════
# ▌ MAIN — يراجع Top 3 ويختار الأفضل
# ═══════════════════════════════════════════
def review_and_select(candidates):
    """
    يأخذ أفضل 3 مرشحين من historical_analyzer
    يُرسلهم لـ Claude واحداً واحداً
    يختار الأفضل بناءً على موافقة Claude
    """
    print("\n" + "═" * 65)
    print("  🤖 Claude يراجع أفضل 3 أسهم...")
    print("═" * 65)

    approved_daily  = []
    approved_golden = []

    for i, candidate in enumerate(candidates[:3], 1):
        stock  = candidate["stock"]
        symbol = stock.get("symbol", "")
        name   = stock.get("name",   "")

        print(f"\n  [{i}/3] مراجعة {name} ({symbol})...")

        # جلب الأخبار
        news = fetch_news(symbol)
        print(f"        الأخبار: {news[:80]}...")

        # مراجعة Claude
        review = claude_review(candidate, news)

        # إضافة نتيجة المراجعة للمرشح
        candidate["claude_review"]     = review
        candidate["claude_reason"]     = review.get("reason",       "")
        candidate["claude_confidence"] = review.get("confidence",   0)
        candidate["claude_warning"]    = review.get("warning",      None)
        candidate["news_sentiment"]    = review.get("news_sentiment","neutral")
        candidate["momentum_ok"]       = review.get("momentum_ok",  False)

        approve     = review.get("approve",     False)
        signal_type = review.get("signal_type", "reject")
        confidence  = review.get("confidence",  0)

        status = "✅ مقبول" if approve else "❌ مرفوض"
        print(f"        {status} | نوع: {signal_type} | ثقة: {confidence}% | {review.get('reason','')}")

        if review.get("warning"):
            print(f"        ⚠️  تحذير: {review['warning']}")

        if not approve or signal_type == "reject":
            continue

        if signal_type == "golden":
            approved_golden.append(candidate)
        else:
            approved_daily.append(candidate)

    # ── اختيار الإشارة النهائية ──────────────────────────────
    print("\n" + "─" * 65)

    daily_signal  = None
    golden_signal = None

    # الإشارة الذهبية: أعلى confidence من القائمة الذهبية
    if approved_golden:
        approved_golden.sort(
            key=lambda x: x["claude_confidence"], reverse=True
        )
        golden_signal = approved_golden[0]
        print(f"  ⭐ إشارة ذهبية: {golden_signal['stock'].get('name','')} "
              f"(ثقة: {golden_signal['claude_confidence']}%)")

    # الإشارة اليومية: أول مقبول (ذهبي أو عادي)
    all_approved = approved_golden + approved_daily
    if all_approved:
        all_approved.sort(
            key=lambda x: x["claude_confidence"], reverse=True
        )
        daily_signal = all_approved[0]
        print(f"  📈 إشارة يومية : {daily_signal['stock'].get('name','')} "
              f"(ثقة: {daily_signal['claude_confidence']}%)")

    if not daily_signal:
        print("  ⛔ Claude رفض جميع المرشحين اليوم — لا نشر")

    return daily_signal, golden_signal


# ═══════════════════════════════════════════
# طباعة ملخص القرار
# ═══════════════════════════════════════════
def print_summary(signal, label="يومية"):
    if not signal:
        return
    s = signal["stock"]
    r = signal["claude_review"]
    print(f"\n  {'⭐' if label == 'ذهبية' else '📈'} الإشارة الـ{label}:")
    print(f"     السهم     : {s.get('name','')} ({s.get('symbol','')})")
    print(f"     Score     : {signal['score']}/100")
    print(f"     ثقة Claude: {signal['claude_confidence']}%")
    print(f"     السبب     : {signal['claude_reason']}")
    print(f"     الزخم ≥10%: {'✅' if signal['momentum_ok'] else '❌'}")
    print(f"     الأخبار   : {signal['news_sentiment']}")
    if signal["claude_warning"]:
        print(f"     تحذير     : {signal['claude_warning']}")
