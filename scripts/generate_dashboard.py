#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아산시 강소형 스마트시티 통합 포털 대시보드 생성기 v4.0
═══════════════════════════════════════════════════════
● 3-tier 데이터 소싱:
  1차: 하위 시스템 GitHub Pages JSON (BMS, WBS)
  2차: Notion API 직접 쿼리 (3개 DB)
  3차: Fallback 하드코딩 (최후 수단)
● Notion DB IDs (corrected):
  - 단위사업별 예산현황  c6073bc5-b025-499f-8b89-417319d6a27c
  - 비목별 예산현황      c47fceb7-f639-4cd7-85f9-6c8c4ac89263
  - WBS 2026 DB         559654ae-d940-4d9f-8822-5ea0adc7d746
● GitHub Actions 30분 자동 실행
"""

import os, json, sys, time
from datetime import date, datetime
from zoneinfo import ZoneInfo
import urllib.request as UR
import urllib.error as UE

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
KST = ZoneInfo("Asia/Seoul")
NOW_KST = datetime.now(KST)
TODAY = date.today()
PROJECT_START = date(2023, 12, 1)
PROJECT_END = date(2026, 12, 31)

DB_UNIT = "c6073bc5-b025-499f-8b89-417319d6a27c"
DB_CAT = "c47fceb7-f639-4cd7-85f9-6c8c4ac89263"
DB_WBS = "559654ae-d940-4d9f-8822-5ea0adc7d746"  # FIXED from 0ed4b202

URL_BMS = "https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/data/budget.json"
URL_WBS_SUMMARY = "https://leesungho-ai.github.io/Asan-Smartcity-WBS/data/summary-data.json"
URL_WBS_DATA = "https://leesungho-ai.github.io/Asan-Smartcity-WBS/data/wbs-data.json"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

PROJECT_META = {
    1: {"color":"#2e80e8","zone":"공통인프라","icon":"📡"},
    2: {"color":"#7c3aed","zone":"공통인프라","icon":"🖥️"},
    3: {"color":"#22c55e","zone":"배방 이노베이션존","icon":"🏢"},
    4: {"color":"#f59e0b","zone":"도고 디지털 OASIS존","icon":"🌿"},
    5: {"color":"#06b6d4","zone":"공통인프라","icon":"☁️"},
    6: {"color":"#ec4899","zone":"공통인프라","icon":"🤖"},
    7: {"color":"#10b981","zone":"도고 디지털 OASIS존","icon":"📊"},
    8: {"color":"#f97316","zone":"도고 디지털 OASIS존","icon":"🚌"},
    9: {"color":"#a78bfa","zone":"공통인프라","icon":"🔍"},
}

# ══════ HTTP FETCH ══════
def fetch_json(url, label=""):
    try:
        req = UR.Request(url, headers={"User-Agent":"Asan-Portal/4.0"})
        with UR.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        print(f"  ✅ {label}: OK")
        return data
    except Exception as e:
        print(f"  ⚠️  {label}: 실패 ({e})")
        return None

# ══════ Notion API ══════
def notion_query(db_id, filter_body=None, max_pages=5):
    if not NOTION_TOKEN: return []
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    results, cursor = [], None
    for _ in range(max_pages):
        body = (filter_body or {}).copy()
        body["page_size"] = 100
        if cursor: body["start_cursor"] = cursor
        try:
            req = UR.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
            with UR.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            results.extend(data.get("results", []))
            if not data.get("has_more"): break
            cursor = data.get("next_cursor")
            time.sleep(0.4)
        except Exception as e:
            print(f"  ⚠️  Notion ({db_id[:8]}): {e}"); break
    return results

def prop_num(page, key):
    try:
        v = page["properties"][key]; t = v.get("type")
        if t == "number": return v["number"] or 0.0
        if t == "formula": return v["formula"].get("number") or 0.0
    except: pass
    return 0.0

def prop_txt(page, key):
    try:
        v = page["properties"][key]; t = v.get("type")
        if t == "title": return "".join(x["plain_text"] for x in v["title"])
        if t == "rich_text": return "".join(x["plain_text"] for x in v["rich_text"])
        if t == "select": return v["select"]["name"] if v["select"] else ""
    except: pass
    return ""

# ══════ DATA SOURCING ══════
def source_budget():
    print("\n📦 [예산] 소싱...")
    bms = fetch_json(URL_BMS, "BMS budget.json")
    if bms and "bimok_summary" in bms:
        return parse_bms_cats(bms), "BMS"
    cats = fetch_notion_cats()
    if cats: return cats, "Notion"
    return FALLBACK_CATS, "Fallback"

def parse_bms_cats(bms):
    CLEAN = {"인건비(110)":"인건비","운영비(210)":"운영비","여비(220)":"여비",
             "연구개발비(260)":"연구개발비","사업비배분(320)":"사업비배분",
             "사업비 배분(320)":"사업비배분","유형자산(430)":"유형자산",
             "무형자산(440)":"무형자산(SW)","건설비(420)":"건설비","기타":"기타"}
    merged = {}
    for b in bms.get("bimok_summary", []):
        name = CLEAN.get(b.get("비목","기타"), b.get("비목","기타"))
        if name in merged:
            merged[name]["b"] += b["예산"]/1e8
            merged[name]["e"] += b["집행"]/1e8
        else:
            merged[name] = {"b": b["예산"]/1e8, "e": b["집행"]/1e8}
    cats = []
    ORDER = ["인건비","운영비","여비","연구개발비","유형자산","무형자산(SW)","건설비","사업비배분","기타"]
    for name in ORDER:
        if name not in merged: continue
        m = merged[name]
        rate = round(m["e"]/m["b"]*100,1) if m["b"] else 0.0
        if rate > 100: st,sc = "🟠 초과","#f97316"
        elif rate >= 50: st,sc = "🟢 정상","#22c55e"
        elif rate > 0: st,sc = "🟡 주의","#eab308"
        else: st,sc = "🔴 미집행","#ef4444"
        cats.append({"name":name,"budget":round(m["b"],2),"executed":round(m["e"],2),
                     "rate":rate,"status":st,"status_color":sc,"note":""})
    return cats

def source_wbs():
    print("\n📋 [WBS] 소싱...")
    ws = fetch_json(URL_WBS_SUMMARY, "WBS summary")
    if ws and "total" in ws:
        t = ws["total"]
        overall = t.get("actualRate", 0)
        services = []
        wd = fetch_json(URL_WBS_DATA, "WBS data")
        if wd and "items" in wd:
            for r in wd["items"]:
                if r.get("level") == "1" and r.get("weight",0) > 0:
                    services.append({"name":r["name"],"rate":round(r.get("actualRate",0)),
                                     "planned":round(r.get("plannedRate",0)),
                                     "weight":r.get("weight",0)})
            services.sort(key=lambda x: -x["rate"])
        return {"overall":overall,"services":services,"summary":ws}, "WBS-JSON"
    # Notion fallback
    rows = notion_query(DB_WBS, {"filter":{"property":"Level","select":{"equals":"1"}}})
    if rows:
        tw = wt = 0
        for p in rows:
            w = prop_num(p, "가중치"); r = prop_num(p, "실적공정률")
            if w: tw += w; wt += w*r
        val = round(wt/tw*100,1) if tw else 50.0
        return {"overall":val,"services":[],"summary":None}, "Notion"
    return {"overall":50.0,"services":[],"summary":None}, "Fallback"

def source_projects():
    print("\n🏗️ [단위사업] 소싱...")
    rows = notion_query(DB_UNIT)
    if rows:
        out = []
        for p in rows:
            num = int(prop_num(p, "사업번호") or 0)
            name = prop_txt(p, "사업명")
            budget = prop_num(p, "예산총액(억원)")
            ex = prop_num(p, "집행금액(억원)")
            vendor = prop_txt(p, "담당업체") or "-"
            note = prop_txt(p, "비고") or ""
            status = prop_txt(p, "상태") or "🔄 진행중"
            wbs_r = prop_num(p, "WBS공정률") or 0
            rate = round(ex/budget*100,1) if budget else 0.0
            meta = PROJECT_META.get(num, {"color":"#6b7280","zone":"-","icon":"📋"})
            if num and name:
                out.append({"num":num,"name":name,"budget":budget,"executed":ex,
                            "exec_rate":rate,"wbs_rate":wbs_r,"status":status,
                            "vendor":vendor,"note":note,**meta})
        out.sort(key=lambda x:x["num"])
        if out:
            print(f"  ✅ {len(out)}개")
            return out, "Notion"
    print("  ⚠️  fallback")
    return FALLBACK_PROJECTS, "Fallback"

def generate_issues(projects, cats, wbs_data, dday):
    issues = []
    tb = sum(p["budget"] for p in projects)
    te = sum(p["executed"] for p in projects)
    er = round(te/tb*100,1) if tb else 0
    tp = dday["pct"]
    gap = tp - er
    if gap > 30:
        issues.append({"level":"🔴 긴급","c":"#ef4444",
            "content":f"예산 집행률({er}%)이 기간 소진율({tp:.0f}%) 대비 {gap:.0f}%p 부족 — 잔여 {round(tb-te,1)}억 집중 집행 필요","amt":f"{round(tb-te,1)}억"})
    for p in projects:
        if p["budget"] >= 10 and p["exec_rate"] < 5 and "완료" not in p["status"]:
            issues.append({"level":"🟠 높음","c":"#f59e0b",
                "content":f"#{p['num']} {p['name']}({p['budget']:.0f}억) 집행률 {p['exec_rate']:.1f}%","amt":f"{p['budget']:.0f}억"})
    for c in cats:
        if c["rate"] > 100:
            issues.append({"level":"🟠 높음","c":"#f59e0b",
                "content":f"{c['name']} 초과집행 {c['rate']:.0f}% — 비목간 전용 필요","amt":f"{c['budget']:.1f}억"})
    wo = wbs_data.get("overall",0)
    if wo < tp * 0.6:
        issues.append({"level":"🔴 긴급","c":"#ef4444",
            "content":f"WBS 공정률({wo:.1f}%)이 기간 소진율({tp:.0f}%)의 60% 미만","amt":"-"})
    if dday["remain"] < 365:
        issues.append({"level":"🟡 주의","c":"#eab308",
            "content":f"사업 종료까지 {dday['remain']}일 잔여","amt":f"D-{dday['remain']}"})
    return issues

# ══════ FALLBACK ══════
FALLBACK_PROJECTS = [
    {"num":1,"name":"유무선 네트워크 구축","budget":11.35,"executed":4.15,"exec_rate":36.6,"wbs_rate":67,"status":"🔄 진행중","vendor":"싸인텔레콤","note":"","color":"#2e80e8","zone":"공통인프라","icon":"📡"},
    {"num":2,"name":"서비스 인프라 플랫폼","budget":45.33,"executed":0.0,"exec_rate":0.0,"wbs_rate":60,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#7c3aed","zone":"공통인프라","icon":"🖥️"},
    {"num":3,"name":"이노베이션 센터 구축","budget":13.00,"executed":11.86,"exec_rate":91.2,"wbs_rate":100,"status":"✅ 완료","vendor":"호서대학교","note":"구축완료","color":"#22c55e","zone":"배방 이노베이션존","icon":"🏢"},
    {"num":4,"name":"디지털 OASIS SPOT","budget":35.00,"executed":0.15,"exec_rate":0.4,"wbs_rate":5,"status":"🔄 진행중","vendor":"(발주준비중)","note":"","color":"#f59e0b","zone":"도고 디지털 OASIS존","icon":"🌿"},
    {"num":5,"name":"SDDC Platform 구축","budget":27.00,"executed":7.09,"exec_rate":26.3,"wbs_rate":43,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#06b6d4","zone":"공통인프라","icon":"☁️"},
    {"num":6,"name":"AI 통합관제 플랫폼","budget":16.00,"executed":9.29,"exec_rate":58.1,"wbs_rate":60,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#ec4899","zone":"공통인프라","icon":"🤖"},
    {"num":7,"name":"디지털 OASIS 정보관리","budget":25.00,"executed":10.93,"exec_rate":43.7,"wbs_rate":43,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#10b981","zone":"도고 디지털 OASIS존","icon":"📊"},
    {"num":8,"name":"DRT 수요응답형 교통","budget":10.00,"executed":0.0,"exec_rate":0.0,"wbs_rate":0,"status":"⏸️ 미착수","vendor":"(미선정)","note":"","color":"#f97316","zone":"도고 디지털 OASIS존","icon":"🚌"},
    {"num":9,"name":"감리용역 (신설)","budget":1.60,"executed":0.0,"exec_rate":0.0,"wbs_rate":0,"status":"🆕 신설","vendor":"(준비중)","note":"","color":"#a78bfa","zone":"공통인프라","icon":"🔍"},
]
FALLBACK_CATS = [
    {"name":"인건비","budget":19.0,"executed":19.0,"rate":100.0,"status":"🟢 정상","status_color":"#22c55e","note":""},
    {"name":"운영비","budget":6.4,"executed":4.2,"rate":65.7,"status":"🟢 정상","status_color":"#22c55e","note":""},
    {"name":"여비","budget":1.3,"executed":0.8,"rate":63.7,"status":"🟢 정상","status_color":"#22c55e","note":""},
    {"name":"연구개발비","budget":1.5,"executed":0.0,"rate":0.0,"status":"🔴 미집행","status_color":"#ef4444","note":""},
    {"name":"유형자산","budget":0.2,"executed":0.0,"rate":0.0,"status":"🔴 미집행","status_color":"#ef4444","note":""},
    {"name":"무형자산(SW)","budget":70.1,"executed":29.0,"rate":41.3,"status":"🟡 주의","status_color":"#eab308","note":""},
    {"name":"건설비","budget":86.4,"executed":11.4,"rate":13.2,"status":"🟡 주의","status_color":"#eab308","note":""},
    {"name":"사업비배분","budget":15.0,"executed":13.0,"rate":86.7,"status":"🟢 정상","status_color":"#22c55e","note":""},
]

# ══════ HTML BUILD ══════
SB = {"✅ 완료":("s-done","완료"),"🔄 진행중":("s-prog","진행중"),"⏸️ 미착수":("s-wait","미착수"),"🆕 신설":("s-new","신설")}
def sbadge(s):
    c,l = SB.get(s,("s-etc",s.replace("✅","").replace("🔄","").replace("⏸️","").replace("🆕","").strip()))
    return f'<span class="sbadge {c}">{l}</span>'

def build_html(projects, cats, wbs_data, dday, sources):
    ts = NOW_KST.strftime("%Y-%m-%d %H:%M")
    wo = wbs_data.get("overall",0)
    svcs = wbs_data.get("services",[])
    tb = sum(p["budget"] for p in projects)
    te = sum(p["executed"] for p in projects)
    tr = round(tb-te,2)
    rate = round(te/tb*100,1) if tb else 0
    dc = sum(1 for p in projects if "완료" in p["status"])
    pc = sum(1 for p in projects if "진행" in p["status"])
    wc = len(projects)-dc-pc
    issues = generate_issues(projects, cats, wbs_data, dday)
    uc = sum(1 for i in issues if "긴급" in i["level"])
    hc = sum(1 for i in issues if "높음" in i["level"])
    sl = " + ".join(set(sources.values()))

    # Project cards
    ph = ""
    for p in projects:
        col=p.get("color","#2e80e8"); ic=p.get("icon","📋"); z=p.get("zone","-")
        er=p["exec_rate"]; wr=p["wbs_rate"]; rm=round(p["budget"]-p["executed"],2)
        zc="badge-oasis" if "OASIS" in z else ("badge-inno" if "이노" in z else "badge-common")
        ph += f'''
<div class="pcard" style="border-top:3px solid {col}">
  <div class="pcard-h"><span class="pcard-num" style="color:{col}">{ic} #{p["num"]}</span><span class="pzone {zc}">{z}</span>{sbadge(p["status"])}</div>
  <div class="pcard-name">{p["name"]}</div>
  <div class="pcard-vendor">🏢 {str(p["vendor"])[:24]}</div>
  <div class="pcard-metrics">
    <div class="pm-block"><div class="pm-label">예산총액</div><div class="pm-val" style="color:{col}">{p["budget"]:.2f}<span class="pm-unit">억</span></div></div>
    <div class="pm-block"><div class="pm-label">집행금액</div><div class="pm-val">{p["executed"]:.2f}<span class="pm-unit">억</span></div></div>
    <div class="pm-block"><div class="pm-label">잔액</div><div class="pm-val" style="color:#94a3b8">{rm:.2f}<span class="pm-unit">억</span></div></div>
  </div>
  <div class="pbar-row"><span class="pbar-lbl">예산집행</span><div class="pbar-wrap"><div class="bb"><div style="width:{min(er,100)}%;background:{col};height:100%;border-radius:4px"></div></div></div><span class="pbar-pct" style="color:{col}">{er:.1f}%</span></div>
  <div class="pbar-row"><span class="pbar-lbl">WBS공정</span><div class="pbar-wrap"><div class="bb"><div style="width:{min(wr,100)}%;background:{col}88;height:100%;border-radius:4px"></div></div></div><span class="pbar-pct" style="color:{col}aa">{wr}%</span></div>
  <div class="pcard-note">{str(p.get("note",""))[:65]}</div>
</div>'''

    # Budget categories
    ch = ""
    for c in cats:
        r=min(c["rate"],100); sc=c.get("status_color","#2e80e8")
        ov="⚠️ " if c["rate"]>100 else ""
        ch += f'''<div class="bi"><div class="bih"><span class="bin">{c["name"]}</span><span class="bir" style="color:{sc}">{ov}{c["rate"]:.1f}%</span></div><div class="bb"><div style="width:{r}%;background:{sc};height:100%;border-radius:4px"></div></div><div class="bd">{c["budget"]:.1f}억 예산 / {c["executed"]:.2f}억 집행</div></div>'''

    # WBS services
    COLS = ["#22c55e","#2e80e8","#7c3aed","#ec4899","#06b6d4","#10b981","#f59e0b","#f97316","#a78bfa","#ef4444"]
    sh = ""
    wsh = ""
    ws = wbs_data.get("summary")
    if ws and "total" in ws:
        t = ws["total"]
        wsh = f'''<div class="wbs-summary-grid"><div class="wbs-stat"><div class="wbs-stat-val">{t["total"]}</div><div class="wbs-stat-lbl">전체</div></div><div class="wbs-stat"><div class="wbs-stat-val" style="color:#22c55e">{t["done"]}</div><div class="wbs-stat-lbl">완료</div></div><div class="wbs-stat"><div class="wbs-stat-val" style="color:#2e80e8">{t["inProg"]}</div><div class="wbs-stat-lbl">진행</div></div><div class="wbs-stat"><div class="wbs-stat-val" style="color:#ef4444">{t["delayed"]}</div><div class="wbs-stat-lbl">지연</div></div><div class="wbs-stat"><div class="wbs-stat-val" style="color:#f59e0b">{t["waiting"]}</div><div class="wbs-stat-lbl">대기</div></div><div class="wbs-stat"><div class="wbs-stat-val" style="color:#7c3aed">{t.get("achieveRate",t.get("actualRate",0)):.1f}%</div><div class="wbs-stat-lbl">달성률</div></div></div>'''
    if svcs:
        for i,s in enumerate(svcs):
            cl=COLS[i%len(COLS)]; r=s["rate"]
            sl2="완료" if r>=100 else ("진행중" if r>0 else "대기")
            sc2="#22c55e" if r>=100 else ("#2e80e8" if r>0 else "#f59e0b")
            sh += f'''<div class="bi"><div class="bih"><span class="bin">{s["name"]}</span><span class="bir" style="color:{cl}">{r}%</span></div><div class="bb"><div style="width:{min(r,100)}%;background:{cl};height:100%;border-radius:4px"></div></div><div class="bd"><span style="color:{sc2};font-size:.68rem">{sl2}</span> · 가중치 {s.get("weight",0):.0f}%</div></div>'''
    else:
        sh = '<div style="color:var(--muted);font-size:.78rem;padding:12px">서비스 데이터 없음</div>'

    # Issues
    ih = ""
    for i in issues:
        ih += f'''<div class="irow" style="border-left:3px solid {i["c"]}"><div class="ilv" style="color:{i["c"]}">{i["level"]}</div><div class="ict">{i["content"]}</div><div class="iamt" style="color:{i["c"]}">{i["amt"]}</div></div>'''
    if not ih: ih = '<div style="color:var(--muted);padding:12px">현재 리스크 없음</div>'

    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>아산시 강소형 스마트시티 통합 포털</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net"/>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet"/>
<style>
:root{{--bg:#0f1623;--card:#1a2540;--bdr:#2a3a5a;--txt:#e2e8f0;--muted:#8fa3c0;--acc:#2e80e8;--ok:#22c55e;--pri:#1a3a6b}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Pretendard','Malgun Gothic',sans-serif;background:var(--bg);color:var(--txt);font-size:14px}}
header{{background:linear-gradient(135deg,var(--pri),#0d2444);padding:14px 26px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--acc);flex-wrap:wrap;gap:8px}}
.ht{{font-size:1.25rem;font-weight:700}}.hs{{font-size:.74rem;color:var(--muted);margin-top:3px}}
.hr{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.badge{{background:rgba(46,128,232,.18);border:1px solid var(--acc);border-radius:20px;padding:3px 12px;font-size:.71rem;color:var(--acc)}}
.upd{{font-size:.70rem;color:var(--muted)}}
.src{{font-size:.68rem;color:#22c55e;border:1px solid #22c55e55;border-radius:10px;padding:2px 8px}}
.wrap{{max-width:1440px;margin:0 auto;padding:18px 14px}}
.g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-bottom:18px}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:16px}}
@media(max-width:1000px){{.g4{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:860px){{.g2{{grid-template-columns:1fr}}}}
@media(max-width:580px){{.g4{{grid-template-columns:1fr}}}}
.card{{background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:17px}}
.kl{{font-size:.70rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px}}
.kv{{font-size:1.9rem;font-weight:700;margin-bottom:3px}}
.ks{{font-size:.72rem;color:var(--muted);line-height:1.5}}
.kb{{height:5px;background:var(--bdr);border-radius:3px;overflow:hidden;margin-top:9px}}
.kb div{{height:100%;border-radius:3px}}
.dual-bar-wrap{{background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:14px 20px;margin-bottom:18px}}
.dual-bar-title{{font-size:.82rem;font-weight:600;color:var(--muted);margin-bottom:10px}}
.dual-item{{display:grid;grid-template-columns:130px 1fr 55px;align-items:center;gap:10px;margin-bottom:8px}}
.dual-lbl{{font-size:.78rem;color:var(--txt);font-weight:500}}
.dual-pct{{font-size:.80rem;font-weight:700;text-align:right}}
.dbar{{height:10px;background:var(--bdr);border-radius:5px;overflow:hidden}}
.dbar div{{height:100%;border-radius:5px}}
.proj-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px}}
@media(max-width:1100px){{.proj-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:640px){{.proj-grid{{grid-template-columns:1fr}}}}
.pcard{{background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:15px;display:flex;flex-direction:column;gap:7px}}
.pcard-h{{display:flex;align-items:center;gap:7px;flex-wrap:wrap}}
.pcard-num{{font-size:.78rem;font-weight:700}}
.pzone{{padding:2px 8px;border-radius:8px;font-size:.64rem;font-weight:600;white-space:nowrap}}
.badge-oasis{{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b44}}
.badge-inno{{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid #22c55e44}}
.badge-common{{background:rgba(46,128,232,.12);color:#7ea8d4;border:1px solid #2e80e833}}
.pcard-name{{font-size:.92rem;font-weight:700;line-height:1.3}}
.pcard-vendor{{font-size:.70rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.pcard-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:4px 0}}
.pm-block{{background:rgba(255,255,255,.04);border-radius:7px;padding:7px 8px;text-align:center}}
.pm-label{{font-size:.63rem;color:var(--muted);margin-bottom:2px}}
.pm-val{{font-size:.95rem;font-weight:700}}.pm-unit{{font-size:.65rem;color:var(--muted);font-weight:400}}
.pbar-row{{display:grid;grid-template-columns:52px 1fr 42px;align-items:center;gap:7px}}
.pbar-lbl{{font-size:.67rem;color:var(--muted);text-align:right}}.pbar-wrap{{flex:1}}
.pbar-pct{{font-size:.72rem;font-weight:700;text-align:right}}
.pcard-note{{font-size:.67rem;color:var(--muted);line-height:1.4;background:rgba(255,255,255,.03);border-radius:6px;padding:5px 8px;border-left:2px solid var(--bdr)}}
.bi{{margin-bottom:11px}}
.bih{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;gap:8px}}
.bin{{font-size:.80rem;font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bir{{font-size:.78rem;font-weight:700;white-space:nowrap}}
.bb{{height:7px;background:var(--bdr);border-radius:4px;overflow:hidden}}
.bd{{font-size:.67rem;color:var(--muted);margin-top:3px;line-height:1.4}}
.irow{{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,.03);margin-bottom:6px}}
.ilv{{font-size:.71rem;font-weight:700;white-space:nowrap;width:62px;flex-shrink:0}}
.ict{{flex:1;font-size:.77rem;line-height:1.4}}
.iamt{{font-size:.74rem;font-weight:700;white-space:nowrap}}
.sbadge{{padding:2px 8px;border-radius:10px;font-size:.68rem;font-weight:600;white-space:nowrap}}
.s-done{{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid #22c55e44}}
.s-prog{{background:rgba(46,128,232,.15);color:#2e80e8;border:1px solid #2e80e844}}
.s-wait{{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b44}}
.s-new{{background:rgba(168,85,247,.15);color:#c084fc;border:1px solid #c084fc44}}
.s-etc{{background:rgba(143,163,192,.1);color:var(--muted);border:1px solid #8fa3c044}}
.sec-title{{font-size:.88rem;font-weight:700;color:var(--acc);margin-bottom:14px;display:flex;align-items:center;gap:6px;padding-bottom:8px;border-bottom:1px solid var(--bdr)}}
.sec-sub{{font-size:.68rem;color:var(--muted);margin-left:auto;font-weight:400}}
footer{{text-align:center;padding:16px;color:var(--muted);font-size:.70rem;border-top:1px solid var(--bdr);margin-top:4px}}
.org-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;font-size:.78rem}}
@media(max-width:760px){{.org-grid{{grid-template-columns:repeat(2,1fr)}}}}
.org-card{{border:1px solid var(--bdr);border-radius:8px;padding:12px}}
.wbs-summary-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px;padding:10px;background:rgba(255,255,255,.03);border-radius:8px}}
.wbs-stat{{text-align:center}}.wbs-stat-val{{font-size:1.1rem;font-weight:700}}.wbs-stat-lbl{{font-size:.65rem;color:var(--muted);margin-top:2px}}
@media(max-width:600px){{.wbs-summary-grid{{grid-template-columns:repeat(3,1fr)}}}}
.sys-section-label{{font-size:.74rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:9px;padding-left:2px}}
.sys-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:4px}}
@media(max-width:1100px){{.sys-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:760px){{.sys-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:480px){{.sys-grid{{grid-template-columns:1fr}}}}
.sys-card{{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:9px;border:1px solid var(--bdr);background:rgba(255,255,255,.03);text-decoration:none;color:var(--txt);transition:all .18s;cursor:pointer}}
.sys-card:hover{{background:rgba(var(--sc-rgb,46,128,232),.12);border-color:var(--sc,var(--acc));transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.3)}}
.sys-icon{{font-size:1.35rem;flex-shrink:0;width:32px;text-align:center}}
.sys-info{{flex:1;min-width:0}}.sys-name{{font-size:.79rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sys-desc{{font-size:.66rem;color:var(--muted);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sys-arrow{{font-size:.80rem;color:var(--muted);flex-shrink:0;transition:transform .18s;margin-left:2px}}
.sys-card:hover .sys-arrow{{transform:translateX(3px);color:var(--sc,var(--acc))}}.sys-card:hover .sys-name{{color:var(--sc,var(--acc))}}
</style></head><body>
<header><div><div class="ht">🌆 아산시 강소형 스마트시티 통합 포털</div><div class="hs">디지털 OASIS 구현 · 충남 아산시 도고면·배방읍 일원 · 총 240억원 · '23.12 ~ '26.12</div></div>
<div class="hr"><span class="badge">📅 {dday["label"]}</span><span class="badge">⚡ WBS {wo:.1f}%</span><span class="badge">💰 집행 {rate:.1f}%</span><span class="src">📡 {sl}</span><span class="upd">🕐 {ts} KST</span></div></header>
<div class="wrap">
<div class="g4">
  <div class="card"><div class="kl">예산 집행률</div><div class="kv" style="color:#2e80e8">{rate:.1f}%</div><div class="ks">{te:.1f}억 집행 / {tr:.1f}억 잔액<br>총 {tb:.1f}억원</div><div class="kb"><div style="width:{min(rate,100)}%;background:#2e80e8"></div></div></div>
  <div class="card"><div class="kl">WBS 전체 공정률</div><div class="kv" style="color:#7c3aed">{wo:.1f}%</div><div class="ks">실적공정률 기준<br>Level-1 가중평균</div><div class="kb"><div style="width:{min(wo,100)}%;background:#7c3aed"></div></div></div>
  <div class="card"><div class="kl">사업 기간 / D-Day</div><div class="kv" style="color:#f59e0b">{dday["label"]}</div><div class="ks">경과 {dday["elapsed"]}일 / 총 {dday["total"]}일<br>기간 소진율 {dday["pct"]:.1f}%</div><div class="kb"><div style="width:{dday["pct"]}%;background:#f59e0b"></div></div></div>
  <div class="card"><div class="kl">단위사업 현황</div><div class="kv" style="color:#22c55e">{len(projects)}개</div><div class="ks">✅ 완료 {dc}개 · 🔄 진행중 {pc}개<br>⏸️ 미착수·신설 {wc}개</div><div class="kb"><div style="width:{round(dc/max(len(projects),1)*100)}%;background:#22c55e"></div></div></div>
</div>
<div class="dual-bar-wrap"><div class="dual-bar-title">📊 사업 진척 현황 비교</div>
  <div class="dual-item"><div class="dual-lbl">⏱ 기간 소진율</div><div class="dbar"><div style="width:{dday["pct"]}%;background:linear-gradient(90deg,#f59e0b,#ef4444)"></div></div><div class="dual-pct" style="color:#f59e0b">{dday["pct"]:.1f}%</div></div>
  <div class="dual-item"><div class="dual-lbl">📋 WBS 공정률</div><div class="dbar"><div style="width:{wo}%;background:linear-gradient(90deg,#7c3aed,#2e80e8)"></div></div><div class="dual-pct" style="color:#7c3aed">{wo:.1f}%</div></div>
  <div class="dual-item"><div class="dual-lbl">💰 예산 집행률</div><div class="dbar"><div style="width:{min(rate,100)}%;background:linear-gradient(90deg,#2e80e8,#06b6d4)"></div></div><div class="dual-pct" style="color:#2e80e8">{rate:.1f}%</div></div>
</div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">🏗️ 단위사업별 현황 ({len(projects)}개 사업) <span class="sec-sub">예산집행률 / WBS공정률</span></div><div class="proj-grid">{ph}</div></div>
<div class="g2"><div class="card"><div class="sec-title">💰 비목별 예산 집행 현황 <span class="sec-sub">{len(cats)}개 비목</span></div>{ch}</div>
<div class="card"><div class="sec-title">⚙️ WBS 공정률 (Level-1) <span class="sec-sub">{len(svcs)}개 분류</span></div>{wsh}{sh}</div></div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">⚠️ 리스크 현황 (자동 분석) <span class="sec-sub">🔴 긴급 {uc}건 · 🟠 높음 {hc}건</span></div>{ih}</div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">🔗 업무 시스템 바로가기 <span class="sec-sub">클릭하여 접속</span></div>
<div class="sys-section-label">📋 프로젝트 관리 (Notion)</div><div class="sys-grid">
<a class="sys-card" href="https://www.notion.so/21650aa9577d80dc8278e0187c54677f" target="_blank" style="--sc:#2e80e8"><span class="sys-icon">📌</span><div class="sys-info"><div class="sys-name">프로젝트 관리</div><div class="sys-desc">사업 총괄 · 단위사업 현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/559654aed9404d9f88225ea0adc7d746?v=3aa59e73-6641-4463-b157-d7c06c129bfb" target="_blank" style="--sc:#7c3aed"><span class="sys-icon">📊</span><div class="sys-info"><div class="sys-name">WBS 관리</div><div class="sys-desc">175개 작업 · 공정률 추적</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/2aa50aa9577d8128b6d4c5c21d845796" target="_blank" style="--sc:#10b981"><span class="sys-icon">💰</span><div class="sys-info"><div class="sys-name">예산관리 시스템</div><div class="sys-desc">비목별 · 단위사업별 집행현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/2b850aa9577d8128ad35d86b79f67d12" target="_blank" style="--sc:#f59e0b"><span class="sys-icon">👥</span><div class="sys-info"><div class="sys-name">인력 현황 대시보드</div><div class="sys-desc">기관별 투입 현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/2aa50aa9577d817da233c79ce0c441fe" target="_blank" style="--sc:#06b6d4"><span class="sys-icon">🖥️</span><div class="sys-info"><div class="sys-name">통합 대시보드</div><div class="sys-desc">Notion 통합 현황판</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/2a750aa9577d8080af05e5f952d1c8b4" target="_blank" style="--sc:#ec4899"><span class="sys-icon">🗺️</span><div class="sys-info"><div class="sys-name">프로덕트 로드맵</div><div class="sys-desc">서비스별 개발 로드맵</div></div><span class="sys-arrow">→</span></a>
</div>
<div class="sys-section-label" style="margin-top:16px">📈 GitHub Pages 대시보드</div><div class="sys-grid">
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/" target="_blank" style="--sc:#22c55e"><span class="sys-icon">🌐</span><div class="sys-info"><div class="sys-name">통합 포털 (현재)</div><div class="sys-desc">본 페이지 · 30분 자동 갱신</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smartcity-WBS/" target="_blank" style="--sc:#7c3aed"><span class="sys-icon">📋</span><div class="sys-info"><div class="sys-name">WBS 대시보드</div><div class="sys-desc">Gantt · 공정률 시각화</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/" target="_blank" style="--sc:#10b981"><span class="sys-icon">💳</span><div class="sys-info"><div class="sys-name">BMS 예산 대시보드</div><div class="sys-desc">예산집행 · 비목별 분석</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-asset-management/" target="_blank" style="--sc:#f59e0b"><span class="sys-icon">🏛️</span><div class="sys-info"><div class="sys-name">자산관리 시스템</div><div class="sys-desc">사업 자산 · 물품 현황 관리</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-HR-Management-Portal/" target="_blank" style="--sc:#ec4899"><span class="sys-icon">👤</span><div class="sys-info"><div class="sys-name">인력관리 시스템</div><div class="sys-desc">투입인력 · 기관별 현황</div></div><span class="sys-arrow">→</span></a>
</div>
<div class="sys-section-label" style="margin-top:16px">🏛️ 정부 업무 시스템</div><div class="sys-grid">
<a class="sys-card" href="https://www.g2b.go.kr" target="_blank" style="--sc:#ef4444"><span class="sys-icon">🛒</span><div class="sys-info"><div class="sys-name">나라장터</div><div class="sys-desc">입찰공고 · 계약관리</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.gosims.go.kr" target="_blank" style="--sc:#f97316"><span class="sys-icon">💼</span><div class="sys-info"><div class="sys-name">e나라도움</div><div class="sys-desc">보조금 집행 · 정산</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.smartcity.go.kr" target="_blank" style="--sc:#2e80e8"><span class="sys-icon">🏙️</span><div class="sys-info"><div class="sys-name">국토부 스마트시티</div><div class="sys-desc">사업 정보 · 정책 동향</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.asan.go.kr" target="_blank" style="--sc:#06b6d4"><span class="sys-icon">🌿</span><div class="sys-info"><div class="sys-name">아산시청</div><div class="sys-desc">발주처 · 스마트도시팀</div></div><span class="sys-arrow">→</span></a>
</div>
<div class="sys-section-label" style="margin-top:16px">💬 협업 도구</div><div class="sys-grid">
<a class="sys-card" href="https://app.slack.com/client/T070J9TK0MY/C07061F0MFG" target="_blank" style="--sc:#4a154b"><span class="sys-icon">💬</span><div class="sys-info"><div class="sys-name">Slack #wbs</div><div class="sys-desc">WBS 파일 공유</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://app.slack.com/client/T070J9TK0MY/C0836U9HVU1" target="_blank" style="--sc:#4a154b"><span class="sys-icon">💬</span><div class="sys-info"><div class="sys-name">Slack #플랜예산</div><div class="sys-desc">예산 xlsx 공유</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://docs.google.com/spreadsheets/d/12LVhySV-AkKCOvd2Q2H1qoBclmtpw5894njN_8B2TQI" target="_blank" style="--sc:#34a853"><span class="sys-icon">📗</span><div class="sys-info"><div class="sys-name">WBS 원본 Sheets</div><div class="sys-desc">Google Sheets</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal" target="_blank" style="--sc:#6e7681"><span class="sys-icon">⚙️</span><div class="sys-info"><div class="sys-name">GitHub 저장소</div><div class="sys-desc">소스코드 · Actions</div></div><span class="sys-arrow">→</span></a>
</div></div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">👥 사업 추진 체계</div><div class="org-grid">
<div class="org-card" style="background:rgba(46,128,232,.08)"><div style="color:#2e80e8;font-weight:700;margin-bottom:6px">🏛️ 시행기관</div><div style="font-weight:600">아산시</div><div style="color:var(--muted);font-size:.69rem">스마트도시팀 박상국 팀장<br>오세현 시장</div></div>
<div class="org-card" style="background:rgba(34,197,94,.08)"><div style="color:#22c55e;font-weight:700;margin-bottom:6px">🏗️ 직접보조사업자</div><div style="font-weight:600">제일엔지니어링</div><div style="color:var(--muted);font-size:.69rem">PMO · 이성호 이사<br>임혁 이사 (PMO Lead)</div></div>
<div class="org-card" style="background:rgba(168,85,247,.08)"><div style="color:#a78bfa;font-weight:700;margin-bottom:6px">🎓 간접보조사업자</div><div style="font-weight:600">호서대학교</div><div style="color:var(--muted);font-size:.69rem">이노베이션센터 운영<br>KTX캠퍼스 내</div></div>
<div class="org-card" style="background:rgba(6,182,212,.08)"><div style="color:#06b6d4;font-weight:700;margin-bottom:6px">🔬 간접보조사업자</div><div style="font-weight:600">충남연구원 · KAIST</div><div style="color:var(--muted);font-size:.69rem">연구·기술지원<br>성과지표 관리</div></div>
</div></div></div>
<footer>아산시 강소형 스마트시티 조성사업 통합 포털 v4.0 · 제일엔지니어링 PMO팀 · 데이터 기준: {ts} KST · 소스: {sl} · 30분 자동 동기화</footer>
</body></html>'''

# ══════ MAIN ══════
def main():
    print("="*60)
    print(f"🚀 통합 포털 v4.0 — {NOW_KST.strftime('%Y-%m-%d %H:%M')} KST")
    print("="*60)
    sources = {}
    cats, src_b = source_budget()
    sources["예산"] = src_b
    wbs_data, src_w = source_wbs()
    sources["WBS"] = src_w
    projects, src_p = source_projects()
    sources["단위사업"] = src_p
    dday = {
        "label": f"D-{(PROJECT_END-TODAY).days}",
        "remain": (PROJECT_END-TODAY).days,
        "elapsed": (TODAY-PROJECT_START).days,
        "total": (PROJECT_END-PROJECT_START).days,
        "pct": round((TODAY-PROJECT_START).days/(PROJECT_END-PROJECT_START).days*100,1),
    }
    print(f"\n📊 소스: {sources}")
    tb = sum(p["budget"] for p in projects)
    te = sum(p["executed"] for p in projects)
    print(f"   집행률: {te/tb*100:.1f}%, WBS: {wbs_data['overall']:.1f}%")
    os.makedirs("data", exist_ok=True)
    with open("data/snapshot.json","w",encoding="utf-8") as f:
        json.dump({"meta":{"updated":NOW_KST.strftime("%Y-%m-%d %H:%M KST"),"sources":sources,"version":"v4.0"},
                   "dday":dday,"projects":projects,"cats":cats,
                   "wbs_overall":wbs_data["overall"],"wbs_services":wbs_data.get("services",[]),
                   "issues":generate_issues(projects, cats, wbs_data, dday)},
                  f, ensure_ascii=False, indent=2)
    print("✅ data/snapshot.json")
    html = build_html(projects, cats, wbs_data, dday, sources)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)
    print(f"✅ index.html ({len(html):,} bytes)")
    print("🎉 완료!")

if __name__ == "__main__":
    main()
