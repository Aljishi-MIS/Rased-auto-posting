import csv
import os
from datetime import datetime

LOG_FILE = "data/signals_log.csv"
REPORT_FILE = "data/weekly_report.txt"

if not os.path.exists(LOG_FILE):
    report = "لا يوجد سجل إشارات حتى الآن."
else:
    signals = []

    with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            signals.append(row)

    total = len(signals)
    wins = len([s for s in signals if s.get("status") == "win"])
    losses = len([s for s in signals if s.get("status") == "loss"])
    open_signals = len([s for s in signals if s.get("status") == "open"])

    closed = wins + losses
    success_rate = round((wins / closed) * 100, 2) if closed > 0 else 0

    report = f"""📊 تقرير مضارب الأسبوعي

━━━━━━━━━━━━━━━
📌 إجمالي الإشارات: {total}
✅ رابحة: {wins}
❌ خاسرة: {losses}
⏳ مفتوحة: {open_signals}

🎯 نسبة النجاح: {success_rate}%

━━━━━━━━━━━━━━━
📈 أفضلية النظام:
نحن لا نكثّر الإشارات، نحن ننتقيها.

⚠️ محتوى تعليمي وتحليلي فقط — لا يُعد توصية استثمارية
"""

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(report)
