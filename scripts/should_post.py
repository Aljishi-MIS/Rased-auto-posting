## “””
should_post.py

يقرر هل الإشارة تستحق النشر أم لا.
“””

import json
import sys
import os
from datetime import datetime, date

DATA_FILE = “data/daily.json”
LOG_FILE  = “data/signals_log.csv”

# ─── شروط الجودة ───────────────────────────────────────────

MIN_SCORE        = 75
RSI_MIN          = 45
RSI_MAX          = 70
MIN_VOLUME_RATIO = 1.8

def check(data):
score        = data.get(“score”, 0)
rsi          = data.get(“rsi”, 50)
volume_ratio = data.get(“volume_ratio”, 0)
rr           = data.get(“rr”, 0)
symbol       = data.get(“symbol”, “”)
name         = data.get(“stock_name”, “”)

```
reasons_fail = []

if score < MIN_SCORE:
    reasons_fail.append(f"Score {score} < {MIN_SCORE}")
if not (RSI_MIN <= rsi <= RSI_MAX):
    reasons_fail.append(f"RSI {rsi:.0f} خارج النطاق ({RSI_MIN}-{RSI_MAX})")
if volume_ratio < MIN_VOLUME_RATIO:
    reasons_fail.append(f"Volume {volume_ratio:.1f}x < {MIN_VOLUME_RATIO}x")

print(f"\n{'═'*55}")
print(f"🔍 فحص جودة الإشارة: {name} ({symbol})")
print(f"{'═'*55}")
print(f"  Score        : {score:>6}  {'✅' if score >= MIN_SCORE else '❌'} (min {MIN_SCORE})")
print(f"  RSI          : {rsi:>6.0f}  {'✅' if RSI_MIN <= rsi <= RSI_MAX else '❌'} ({RSI_MIN}-{RSI_MAX})")
print(f"  Volume Ratio : {volume_ratio:>6.1f}x {'✅' if volume_ratio >= MIN_VOLUME_RATIO else '❌'} (min {MIN_VOLUME_RATIO}x)")
print(f"  R:R          : {rr:>6.1f}  ℹ️  (معلوماتي فقط — لا يوقف النشر)")

if reasons_fail:
    print(f"\n🚫 الإشارة لا تستوفي المعايير:")
    for r in reasons_fail:
        print(f"   • {r}")
    print(f"\n⏭️  تم تخطي النشر اليوم — انتظار فرصة أفضل\n")
    return False

print(f"\n✅ الإشارة تستوفي جميع المعايير — سيتم النشر!\n")
return True
```

if **name** == “**main**”:
try:
with open(DATA_FILE, “r”, encoding=“utf-8”) as f:
data = json.load(f)
except Exception as e:
print(f”❌ خطأ في قراءة {DATA_FILE}: {e}”)
sys.exit(1)

```
if check(data):
    sys.exit(0)
else:
    sys.exit(1)
```