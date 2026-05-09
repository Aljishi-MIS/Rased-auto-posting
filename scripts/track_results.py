"""
track_results.py
----------------
يتحقق من إشارات مفتوحة ويحدث حالتها (win/loss).
يُشغَّل يومياً بعد إغلاق السوق.
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta

LOG_FILE  = "data/signals_log.csv"
API_KEY   = os.environ.get("API_KEY")
BASE_URL  = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS   = {"X-API-Key": API_KEY} if API_KEY else {}
MAX_DAYS  = 5   # أقصى مدة لإغلاق الإشارة


def get_price(symbol):
    try:
        r = requests.get(f"{BASE_URL}/quote/{symbol}/", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return float(r.json().get("price", 0))
    except Exception:
        pass
    return None


def update_signals():
    if not os.path.exists(LOG_FILE):
        print("لا يوجد سجل إشارات بعد.")
        return

    rows = []
    updated = 0

    with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    today = datetime.now().date()

    for row in rows:
        if row.get("status") != "open":
            continue

        try:
            signal_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
        except Exception:
            continue

        days_open = (today - signal_date).days

        # إغلاق الإشارات القديمة جداً بدون نتيجة
        if days_open > MAX_DAYS:
            row["status"] = "expired"
            updated += 1
            print(f"  ⏰ {row['stock_name']} ({row['symbol']}) — انتهت المدة ({days_open} أيام)")
            continue

        # تحقق من السعر الحالي
        price = get_price(row["symbol"])
        if price is None:
            continue

        target1   = float(row.get("target1",   0) or 0)
        stop_loss = float(row.get("stop_loss", 0) or 0)

        if target1 > 0 and price >= target1:
            row["status"]      = "win"
            row["close_price"] = f"{price:.2f}"
            row["close_date"]  = str(today)
            updated += 1
            print(f"  ✅ WIN  {row['stock_name']} ({row['symbol']}) — السعر {price:.2f} >= هدف {target1:.2f}")

        elif stop_loss > 0 and price <= stop_loss:
            row["status"]      = "loss"
            row["close_price"] = f"{price:.2f}"
            row["close_date"]  = str(today)
            updated += 1
            print(f"  ❌ LOSS {row['stock_name']} ({row['symbol']}) — السعر {price:.2f} <= وقف {stop_loss:.2f}")

    # إضافة أعمدة جديدة إذا لم تكن موجودة
    new_fields = list(fieldnames or [])
    for col in ["close_price", "close_date"]:
        if col not in new_fields:
            new_fields.append(col)

    with open(LOG_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=new_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ تم تحديث {updated} إشارة في السجل")


if __name__ == "__main__":
    print("🔄 جارٍ تحديث نتائج الإشارات...\n")
    update_signals()
