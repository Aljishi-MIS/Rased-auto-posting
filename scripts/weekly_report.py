"""
weekly_report.py — تقرير أسبوعي احترافي بنسب النجاح الحقيقية
"""

import csv
import os
from datetime import datetime, timedelta

LOG_FILE    = "data/signals_log.csv"
REPORT_FILE = "data/weekly_report.txt"


def load_signals():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def this_week_signals(signals):
    today      = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    result = []
    for s in signals:
        try:
            d = datetime.strptime(s["date"], "%Y-%m-%d").date()
            if d >= week_start:
                result.append(s)
        except Exception:
            pass
    return result


def build_report(signals, week_signals):
    total  = len(signals)
    wins   = len([s for s in signals if s.get("status") == "win"])
    losses = len([s for s in signals if s.get("status") == "loss"])
    open_s = len([s for s in signals if s.get("status") == "open"])
    expired= len([s for s in signals if s.get("status") == "expired"])

    closed       = wins + losses
    success_rate = round((wins / closed) * 100, 1) if closed > 0 else 0

    # متوسط الـ Score
    scores = [float(s.get("score", 0)) for s in signals if s.get("score")]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    week_lines = ""
    for s in week_signals:
        status_icon = {"win": "✅", "loss": "❌", "open": "⏳", "expired": "⏰"}.get(s.get("status", ""), "•")
        week_lines += f"\n{status_icon} {s.get('stock_name','')} ({s.get('symbol','')}) | دخول: {s.get('entry','')} | هدف: {s.get('target1','')} | وقف: {s.get('stop_loss','')}"

    report = f"""📊 تقرير مضارب الأسبوعي
{datetime.now().strftime('%Y-%m-%d')}

━━━━━━━━━━━━━━━━━━━━━━━━━
📈 إجمالي الإشارات الكلي: {total}
✅ رابحة  : {wins}
❌ خاسرة  : {losses}
⏳ مفتوحة : {open_s}

🎯 نسبة النجاح : {success_rate}%
📊 متوسط الـ Score: {avg_score}/100

━━━━━━━━━━━━━━━━━━━━━━━━━
📅 إشارات هذا الأسبوع ({len(week_signals)}):
{week_lines if week_lines else 'لا توجد إشارات هذا الأسبوع'}

━━━━━━━━━━━━━━━━━━━━━━━━━
💡 منهجيتنا:
نُصدر 3 إشارات أسبوعياً كحد أقصى.
لا إشارة إلا عند توفر جميع شروط الجودة.

⚠️ محتوى تعليمي وتحليلي — ليس توصية استثمارية
"""
    return report


signals      = load_signals()
week_signals = this_week_signals(signals)
report       = build_report(signals, week_signals)

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(report)
