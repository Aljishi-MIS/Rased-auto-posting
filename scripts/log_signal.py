"""
log_signal.py — يسجل الإشارة في السجل التاريخي
"""

import json
import csv
import os
from datetime import datetime

DATA_FILE = "data/daily.json"
LOG_FILE  = "data/signals_log.csv"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

file_exists = os.path.exists(LOG_FILE)

row = {
    "date":        datetime.now().strftime("%Y-%m-%d"),
    "time":        datetime.now().strftime("%H:%M"),
    "stock_name":  data.get("stock_name", ""),
    "symbol":      data.get("symbol", ""),
    "price":       data.get("price", ""),
    "entry":       data.get("entry", ""),
    "target1":     data.get("target1", ""),
    "target2":     data.get("target2", ""),
    "stop_loss":   data.get("stop_loss", ""),
    "rsi":         data.get("rsi", ""),
    "volume_ratio":data.get("volume_ratio", ""),
    "score":       data.get("score", ""),
    "rr":          data.get("rr", ""),
    "momentum":    data.get("momentum", ""),
    "source":      data.get("source", ""),
    "status":      "open",
    "close_price": "",
    "close_date":  "",
}

with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=row.keys())
    if not file_exists:
        writer.writeheader()
    writer.writerow(row)

print(f"✅ إشارة {data.get('stock_name')} ({data.get('symbol')}) سُجّلت بنجاح")
