import os, json, requests
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("API_KEY")
API_URL = os.environ.get("API_URL", "https://app.sahmk.sa/api/v1")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

OUTPUT_FILE  = "data/daily.json"
GOLDEN_FILE  = "data/golden_signal.json"
INTEL_FILE   = "data/market_intel.json"

GOLDEN_SCORE_MIN     = 72
MIN_HISTORY_DAYS     = 15
GOLDEN_EARLIEST_HOUR = 9
GOLDEN_LATEST_HOUR   = 15
KSA = timezone(timedelta(hours=3))

SECTORS = {
    "البنوك":         ["1010","1020","1030","1050","1060","1080","1120","1150"],
    "البتروكيماويات": ["2010","2020","2060","2090","2100","2150","2160","2170","2222","2223","2230"],
    "الاتصالات":      ["7010","7020","7030","7040","7203","7204"],
    "الطاقة":         ["5110","2040","2050"],
    "التجزئة":        ["4190","4200","4210","4220","4230","4240","4250","4261"],
    "العقار":         ["4020","4031","4040","4050","4100","4150","4300","4320","4321","4322","4323","4324"],
    "الصحة":          ["4002","4005","4007","4009","4013","4017","4019","4061"],
    "الصناعة":        ["1211","1212","2030","2080","2082","2083","2110","2120","2130","2140","2180",
                      "2190","2200","2210","2220","2240","2250","2290","2310","2320","2330","2340",
                      "2350","2360","2370","2380","2381","2382"],
    "التامين":        ["8010","8020","8030","8040","8050","8060","8070","8100","8120","8150","8160",
                      "8170","8180","8190","8200","8210","8230","8240","8250","8260","8270","8280",
                      "8300","8310","8311","8320","8330","8340"],
    "الاستثمار":      ["1111","4280","4290","4310","4349","4330","4331","4332","4333","4334","4335",
                      "4336","4337","4338","4339","4340","4341","4342","4344","4345","4346","4347","4348"],
    "التقنية":        ["9516","9526","9527","9528","9529","9536","9543","9544","9545","9546","9547",
                      "9548","9549","9553","9554","9555","9556","9557","9558","9559","9560","9561",
                      "9562","9563","9564","9565","9566","9567","9568"],
    "الغذاء":         ["2060","2070","6001","6002","6010","6013","6014","6015","6020","6040","6050","6060","6070"],
    "التعليم":        ["4001","4003","4004","4006","4008","4010","4011","4012","4014","4015","4016","4018","4021"],
    "الترفيه":        ["4160","4161","4162","4163","4164","4170","4180"],
    "النقل":          ["1301","1302","1303","1304","1320","1321","5010","5020"],
}


def safe_float(v, d=0.0):
    try: return float(v)
    except: return d

def get_sector(sym):
    for n,s in SECTORS.items():
        if str(sym) in s: return n
    return "اخرى"

def api_get(ep, params=None):
    try:
        r = requests.get(f"{API_URL}{ep}", headers=HEADERS, params=params or {}, timeout=15)
        if r.status_code == 200: return r.json()
    except Exception as e: print(f"  error {ep}: {e}")
    return None

def get_rs(symbol):
    try:
        with open(INTEL_FILE,"r",encoding="utf-8") as f: intel=json.load(f)
        for s in intel.get("top_stocks",[]):
            if str(s.get("symbol",""))==str(symbol): return s.get("rs_rank",0)
    except: pass
    return 0

def fetch_candidates():
    seen={}; stocks=[]
    for ep,k in [("/market/gainers/","gainers"),("/market/volume/","stocks")]:
        data=api_get(ep,{"limit":60,"index":"TASI"})
        if data:
            items=data if isinstance(data,list) else data.get(k,data.get("data",[]))
            for s in items:
                sym=str(s.get("symbol",""))
                if sym and sym not in seen: seen[sym]=s; stocks.append(s)
    return stocks

def fetch_hist(symbol, period=30):
    data=api_get(f"/historical/{symbol}/",{"period":period})
    if not data: return None
    h=data.get("data",[])
    if len(h)<MIN_HISTORY_DAYS: return None
    h=sorted(h,key=lambda x:x.get("date",""))
    return {"closes":[safe_float(d.get("close")) for d in h],
            "highs": [safe_float(d.get("high"))  for d in h],
            "lows":  [safe_float(d.get("low"))   for d in h],
            "volumes":[safe_float(d.get("volume")) for d in h],
            "count":len(h)}


# ══════════════════════════════════════════════════
# ١ — RSI Momentum (15 نقطة)
# ══════════════════════════════════════════════════

def calc_rsi(closes, p=14):
    if len(closes)<p+1: return 50.0
    g,l=[],[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]; g.append(max(d,0)); l.append(max(-d,0))
    ag=sum(g[:p])/p; al=sum(l[:p])/p
    for i in range(p,len(g)): ag=(ag*(p-1)+g[i])/p; al=(al*(p-1)+l[i])/p
    return 100.0 if al==0 else round(100-(100/(1+ag/al)),2)

def score_rsi(closes):
    r=calc_rsi(closes)
    if 45<=r<=60:  return 15,r,f"RSI {r:.0f} المنطقة الذهبية للانفجار"
    elif 60<r<=70: return 10,r,f"RSI {r:.0f} قوي"
    elif 35<=r<45: return 8, r,f"RSI {r:.0f} تراجع صحي"
    elif r>75:     return -5,r,f"RSI {r:.0f} تشبع شرائي"
    else:          return 3, r,f"RSI {r:.0f} محايد"


# ══════════════════════════════════════════════════
# ٢ — Bollinger Squeeze (20 نقطة)
# ══════════════════════════════════════════════════

def calc_ema(closes, p):
    if len(closes)<p: return closes[-1] if closes else 0
    k=2/(p+1); e=sum(closes[:p])/p
    for c in closes[p:]: e=c*k+e*(1-k)
    return round(e,4)

def calc_bb(closes, p=20, m=2.0):
    if len(closes)<p: p=max(5,len(closes))
    rec=closes[-p:]; mid=sum(rec)/p
    std=(sum((c-mid)**2 for c in rec)/p)**0.5
    up=mid+m*std; lo=mid-m*std
    w=(up-lo)/mid if mid>0 else 0
    return up,mid,lo,round(w,4)

def score_bollinger(closes):
    if len(closes)<20: return 0,0,"بيانات غير كافية"
    price=closes[-1]; up,mid,lo,cw=calc_bb(closes)
    ws=[calc_bb(closes[:i])[3] for i in range(20,len(closes)+1)]
    aw=sum(ws)/len(ws) if ws else cw
    ratio=cw/aw if aw>0 else 1.0
    if ratio<=0.50:   pts=20; d=f"ضغطة شديدة {ratio:.2f}x — انفجار وشيك"
    elif ratio<=0.70: pts=14; d=f"ضغطة قوية {ratio:.2f}x"
    elif ratio<=0.85: pts=8;  d=f"بداية ضغطة {ratio:.2f}x"
    else:             pts=2;  d=f"لا ضغطة {ratio:.2f}x"
    if price>=up: pts=min(pts+10,20); d+=" + اختراق البولينجر"
    return pts,round(ratio,3),d


# ══════════════════════════════════════════════════
# ٣ — OBV Divergence (15 نقطة)
# ══════════════════════════════════════════════════

def calc_obv(closes, vols):
    o=[0.0]
    for i in range(1,len(closes)):
        if closes[i]>closes[i-1]:   o.append(o[-1]+vols[i])
        elif closes[i]<closes[i-1]: o.append(o[-1]-vols[i])
        else:                        o.append(o[-1])
    return o

def score_obv(closes, vols):
    if len(closes)<10: return 0,"بيانات غير كافية"
    obv=calc_obv(closes,vols); lb=min(10,len(closes)-1)
    pc=(closes[-1]-closes[-lb])/closes[-lb]*100
    oc=(obv[-1]-obv[-lb])/(abs(obv[-lb])+1)*100
    if pc<-1 and oc>5:   return 15,f"Divergence ايجابي: سعر {pc:.1f}% OBV +{oc:.1f}% (تراكم خفي)"
    elif pc>1 and oc>5:  return 10,f"تأكيد صعود: سعر +{pc:.1f}% OBV +{oc:.1f}%"
    elif pc>1 and oc<-5: return -5,f"تحذير: سعر +{pc:.1f}% OBV {oc:.1f}%"
    else:                return 3, f"OBV محايد"


# ══════════════════════════════════════════════════
# ٤ — MACD Crossover (15 نقطة)
# ══════════════════════════════════════════════════

def score_macd(closes):
    if len(closes)<26: return 0,0,"بيانات غير كافية"
    ef=calc_ema(closes,12); es=calc_ema(closes,26); macd=ef-es
    ms=[calc_ema(closes[:i],12)-calc_ema(closes[:i],26) for i in range(26,len(closes)+1)]
    sig=calc_ema(ms,9) if len(ms)>=9 else macd; hist=macd-sig
    cross=False
    if len(closes)>=29:
        m3=calc_ema(closes[:-3],12)-calc_ema(closes[:-3],26)
        ms3=[calc_ema(closes[:-3][:i],12)-calc_ema(closes[:-3][:i],26) for i in range(26,len(closes)-2)]
        s3=calc_ema(ms3,9) if len(ms3)>=9 else m3
        cross=m3<s3 and macd>sig
    if cross:                 return 15,round(hist,4),f"تقاطع صعودي حديث MACD {macd:.3f}"
    elif macd>sig and hist>0: return 12,round(hist,4),"MACD صاعد + Histogram يتوسع"
    elif macd>sig:            return 8, round(hist,4),"MACD فوق Signal"
    elif macd<sig and hist>-0.01: return 3,round(hist,4),"MACD يقترب من التقاطع"
    else:                     return 0, round(hist,4),"MACD تحت Signal"


# ══════════════════════════════════════════════════
# ٥ — Volume Surge (15 نقطة)
# ══════════════════════════════════════════════════

def score_volume(vols):
    if len(vols)<20: return 0,0,"بيانات غير كافية"
    a5=sum(vols[-5:])/5; a20=sum(vols[-20:])/20
    r=a5/a20 if a20>0 else 1.0
    grad=all(vols[-i]>=vols[-(i+1)]*0.85 for i in range(1,min(5,len(vols))))
    if r>=3.0:   pts=15; d=f"تراكم استثنائي {r:.1f}x"
    elif r>=2.0: pts=12; d=f"حجم عالٍ {r:.1f}x"
    elif r>=1.5: pts=8;  d=f"حجم جيد {r:.1f}x"
    elif r>=1.2: pts=5;  d=f"فوق المتوسط {r:.1f}x"
    else:        pts=0;  d=f"حجم طبيعي {r:.1f}x"
    if grad and pts>0: pts=min(pts+3,15); d+=" (تراكم تدريجي)"
    return pts,round(r,2),d


# ══════════════════════════════════════════════════
# ٦ — CANSLIM (20 نقطة)
# ══════════════════════════════════════════════════

def score_canslim(stock, closes, vols, rs):
    pts=0; dets=[]
    if rs>=90:    pts+=6; dets.append(f"قائد السوق RS {rs}")
    elif rs>=80:  pts+=4; dets.append(f"RS Rank {rs} قوي")
    elif rs>=60:  pts+=2; dets.append(f"RS Rank {rs}")
    elif 0<rs<40: pts-=3
    if len(closes)>=20:
        chg=(closes[-1]-closes[-20])/closes[-20]*100
        if chg>=10:   pts+=4; dets.append(f"+{chg:.1f}% (20 يوم)")
        elif chg>=5:  pts+=3; dets.append(f"+{chg:.1f}% (20 يوم)")
        elif chg>=0:  pts+=1
        elif chg<-10: pts-=3
    if len(closes)>=10 and len(vols)>=10:
        h20=max(closes[-20:]) if len(closes)>=20 else max(closes)
        near=closes[-1]>=h20*0.97
        vr=vols[-1]/(sum(vols[-20:])/20) if vols[-20:] else 1
        if near and vr>=1.5: pts+=6; dets.append(f"اختراق مع حجم {vr:.1f}x")
        elif near:            pts+=3; dets.append("قريب من الاختراق")
        elif vr>=2:           pts+=2; dets.append(f"حجم {vr:.1f}x")
    sec=get_sector(str(stock.get("symbol","")))
    if sec in ["البتروكيماويات","البنوك","التقنية","الطاقة","الاتصالات"]:
        pts+=4; dets.append(f"قطاع {sec} قوي")
    elif sec!="اخرى": pts+=2
    return max(min(pts,20),-5),dets


# ══════════════════════════════════════════════════
# الحساب الكلي
# ══════════════════════════════════════════════════

def calc_radar(stock, hist):
    c=hist["closes"]; v=hist["volumes"]; rs=get_rs(str(stock.get("symbol","")))
    comp={}; sigs=[]; tot=0

    p,rv,d=score_rsi(c)
    comp["rsi_momentum"]={"score":p,"max":15,"detail":d,"rsi":rv}; tot+=p
    if p>=8: sigs.append(d)

    p,br,d=score_bollinger(c)
    comp["bollinger_squeeze"]={"score":p,"max":20,"detail":d,"ratio":br}; tot+=p
    if p>=8: sigs.append(d)

    p,d=score_obv(c,v)
    comp["obv_divergence"]={"score":p,"max":15,"detail":d}; tot+=p
    if p>=8: sigs.append(d)

    p,mh,d=score_macd(c)
    comp["macd_crossover"]={"score":p,"max":15,"detail":d,"histogram":mh}; tot+=p
    if p>=8: sigs.append(d)

    p,vr,d=score_volume(v)
    comp["volume_surge"]={"score":p,"max":15,"detail":d,"ratio":vr}; tot+=p
    if p>=5: sigs.append(d)

    p,csd=score_canslim(stock,c,v,rs)
    comp["canslim"]={"score":p,"max":20,"detail":" + ".join(csd)}; tot+=p
    if p>=8: sigs.extend(csd)

    tot=max(0,min(tot,100))
    return tot, comp, sigs, comp["rsi_momentum"]["rsi"], comp["volume_surge"]["ratio"]


# ══════════════════════════════════════════════════
# بناء الإشارة الذهبية
# ══════════════════════════════════════════════════

def calc_atr(hi, lo, cl, p=14):
    trs=[]
    for i in range(1,len(cl)):
        trs.append(max(hi[i]-lo[i],abs(hi[i]-cl[i-1]),abs(lo[i]-cl[i-1])))
    if not trs: return cl[-1]*0.01
    atr=sum(trs[:p])/min(p,len(trs))
    for t in trs[p:]: atr=(atr*(p-1)+t)/p
    return round(atr,4)

def find_res(hi, cl):
    price=cl[-1]; local=[]
    for i in range(1,len(hi)-1):
        if hi[i]>=hi[i-1] and hi[i]>=hi[i+1]: local.append(hi[i])
    above=[h for h in local if h>price*1.002]
    return min(above) if above else max(hi[-10:])

def build_signal(stock, hist, sc, comp, sigs, rv, vr):
    c=hist["closes"]; hi=hist["highs"]; lo=hist["lows"]
    price=safe_float(stock.get("price") or stock.get("close"))
    sym=str(stock.get("symbol","")); name=stock.get("name") or stock.get("name_ar") or sym
    sector=get_sector(sym); atr=calc_atr(hi,lo,c)
    res=find_res(hi,c); entry=round(res*1.005,2)
    t1=round(min(entry+atr*2,entry*1.05),2); t2=round(min(entry+atr*3.5,entry*1.09),2)
    sl=round(max(entry-atr*2,entry*0.96),2)
    if sl>=entry: sl=round(entry*0.97,2)
    risk=entry-sl; rew=t1-entry; rr=round(rew/risk,2) if risk>0 else 0
    if sc>=80:   st="انفجار وشيك";  sc_col="red"
    elif sc>=65: st="راقب عن كثب"; sc_col="yellow"
    else:        st="تشكّل مبكر";  sc_col="green"
    now=datetime.now(KSA)
    note_parts=(sigs or ["تحليل فني متكامل"])[:3]
    return {
        "brand":"مضارب","mode":"golden","type":"اشارة ذهبية",
        "signal_type":st,"signal_color":sc_col,
        "stock_name":name,"symbol":sym,"sector":sector,
        "price":f"{price:.2f}","entry":f"{entry:.2f}",
        "target1":f"{t1:.2f}","target2":f"{t2:.2f}","stop_loss":f"{sl:.2f}",
        "score":sc,"rsi":round(rv,1),"rr":rr,"volume_ratio":vr,
        "rs_rank":get_rs(sym),"momentum":"قوي جداً" if sc>=80 else "قوي" if sc>=65 else "متوسط",
        "components":comp,"source":"radar_analysis",
        "generated_at":now.strftime("%Y-%m-%d %H:%M"),
        "note":f"قراءة فنية: {' + '.join(note_parts)}.",
        "signals":sigs,
    }


# ══════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════

def main():
    import sys
    print("\n" + "="*65)
    print("رادار تاسي — الإشارة الذهبية (منهجية الانفجار)")
    print("="*65)
    if not API_KEY: print("API_KEY missing"); sys.exit(1)
    now=datetime.now(KSA)
    if now.weekday() not in [6,0,1,2,3]: print("  يوم إجازة"); sys.exit(0)
    if not (GOLDEN_EARLIEST_HOUR<=now.hour<GOLDEN_LATEST_HOUR):
        print(f"  خارج النافذة {now.strftime('%H:%M')}"); sys.exit(0)
    try:
        import os as _os; sys.path.insert(0,_os.path.dirname(_os.path.abspath(__file__)))
        from market_intelligence import run as ri; ri()
    except Exception as e: print(f"  Intel: {e}")

    cands=fetch_candidates()
    if not cands: print("لا مرشحون"); sys.exit(1)
    print(f"\n  مرشحون: {len(cands)} سهم")
    print(f"\n  {'السهم':<20} {'Total':>6} {'RSI':>4} {'BB':>4} {'OBV':>4} {'MACD':>4} {'Vol':>4} {'CS':>4}")
    print("  " + "-"*60)

    golden=[]
    for stock in cands[:40]:
        sym=str(stock.get("symbol","")); price=safe_float(stock.get("price") or stock.get("close"))
        name=(stock.get("name") or stock.get("name_ar") or sym)[:18]
        if price<3: continue
        hist=fetch_hist(sym,30)
        if not hist: continue
        sc,comp,sigs,rv,vr=calc_radar(stock,hist)
        icon="🔴" if sc>=80 else "🟡" if sc>=65 else "🟢" if sc>=45 else "  "
        print(f"  {name:<20} {sc:>5} {comp['rsi_momentum']['score']:>4} "
              f"{comp['bollinger_squeeze']['score']:>4} {comp['obv_divergence']['score']:>4} "
              f"{comp['macd_crossover']['score']:>4} {comp['volume_surge']['score']:>4} "
              f"{comp['canslim']['score']:>4} {icon}")
        if sc>=GOLDEN_SCORE_MIN:
            golden.append({"score":sc,"stock":stock,"hist":hist,
                          "components":comp,"signals":sigs,"rv":rv,"vr":vr})

    print(f"\n{'='*65}")
    if not golden: print("  لا توجد إشارات ذهبية اليوم"); sys.exit(1)
    golden.sort(key=lambda x:x["score"],reverse=True)
    b=golden[0]
    sig=build_signal(b["stock"],b["hist"],b["score"],b["components"],
                     b["signals"],b["rv"],b["vr"])
    if sig["rr"]<1.0: print(f"  R:R {sig['rr']} ضعيف"); sys.exit(1)
    for fn in [GOLDEN_FILE, OUTPUT_FILE]:
        with open(fn,"w",encoding="utf-8") as f: json.dump(sig,f,ensure_ascii=False,indent=2)
    print(f"\n  الإشارة الذهبية:")
    print(f"  {sig['stock_name']} ({sig['symbol']}) — {sig['signal_type']} — {sig['score']}/100")
    print(f"  دخول: {sig['entry']} | هدف1: {sig['target1']} | وقف: {sig['stop_loss']} | R:R: {sig['rr']}")
    print(f"\n  المكونات (من 100):")
    labels={"rsi_momentum":"RSI Momentum","bollinger_squeeze":"Bollinger Squeeze",
            "obv_divergence":"OBV Divergence","macd_crossover":"MACD Crossover",
            "volume_surge":"Volume Surge","canslim":"CANSLIM"}
    for k,v in sig["components"].items():
        bar="█"*max(0,v["score"])+"░"*(v["max"]-max(0,v["score"]))
        print(f"    {labels.get(k,k):<20} {v['score']:>3}/{v['max']} [{bar}]")
        print(f"         {v['detail']}")

if __name__ == "__main__":
    main()
