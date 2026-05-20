# ... (بداية الملف كما هي) ...

def build_caption(data: dict) -> str:
    symbol = data.get("symbol", "")
    name = data.get("stock_name", "")
    entry = data.get("entry", "")
    t1 = data.get("target1", "")
    t2 = data.get("target2", "")
    sl = data.get("stop_loss", "")
    score = data.get("score", 0)
    rr = data.get("rr", 0)
    track_url = "https://aljishi.github.io/modareb-auto-posting"  # يمكن تحديثه لاحقًا
    
    is_golden = data.get("type") == "اشارة ذهبية"
    badge = "⭐ ذهبية" if is_golden else "📊 يومية"
    
    # ✅ التعديل: تغيير "مضارب" إلى "راصد"
    caption = (
        f"🔔 راصد — إشارة {badge}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📌 {name} ({symbol})\n"
        f"💰 الدخول: {entry} ريال\n"
        f"🎯 الهدف 1: {t1} ريال (+5%)\n"
        f"🎯 الهدف 2: {t2} ريال (+10%)\n"
        f"🛑 وقف الخسارة: {sl} ريال (-4%)\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 قوة الإشارة: {score}/100\n"
        f"⚖️ مكافأة/مخاطرة: {rr}:1\n"
        f"━━━━━━━━━━━━━━\n"
        f"📈 لوحة المتابعة: {track_url}\n"
        f"⚠️ محتوى تعليمي — ليس توصية مالية"
    )
    return caption

# ... (باقي دوال النشر كما هي) ...

