#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아산시 강소형 스마트시티 통합 포털 대시보드 생성기 v4.2
═══════════════════════════════════════════════════════
● 100% 하위시스템 JSON 기반 (Notion 의존 제거)
  - BMS budget.json → 비목별 예산 + 단위사업별 예산 (매핑)
  - WBS summary-data.json + wbs-data.json → 공정률
● Notion은 보조 소스로만 사용 (사용 가능 시)
● GitHub Actions 30분 자동 실행
"""

import os, json, sys, time
from datetime import date, datetime
from zoneinfo import ZoneInfo
import urllib.request as UR

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
KST = ZoneInfo("Asia/Seoul")
NOW_KST = datetime.now(KST)
TODAY = date.today()
PROJECT_START = date(2023, 12, 1)
PROJECT_END = date(2026, 12, 31)

URL_BMS = "https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/data/budget.json"
URL_WBS_SUMMARY = "https://leesungho-ai.github.io/Asan-Smartcity-WBS/data/summary-data.json"
URL_WBS_DATA = "https://leesungho-ai.github.io/Asan-Smartcity-WBS/data/wbs-data.json"

# ── BMS 항목 → 단위사업 매핑 ──
BMS_UNIT_MAP = {
    "스마트 공공 WIFI": 1,
    "아산시 강소형 스마트시티 네트워크 구축": 1,
    "모바일 전자시민증 플랫폼 / 인프라": 2,
    "이노베이션 센터/ 관제 시스템 구축": 3,
    "디지털 OASIS SPOT": 4,
    "무인매장": 4,
    "SDDC Platform 구축": 5,
    "AI통합관제 및 운영 플랫폼 / 인프라": 6,
    "디지털OASIS 정보관리 시스템": 7,
    "수요응답형 DRT 서비스 운영 플랫폼 구축": 8,
    "수요응답형 DRT 서비스 운영 HW 구축": 8,
    "정보통신감리": 9,
    "스마트폴&디스플레이": 10,
    "메타버스 플랫폼": 11,
    "디지털 노마드접수/운영 및 거래관리": 12,
    "데이터기반 AI 융복합 서비스 구축": 13,
    "국제표준 디지털링크 공유 플랫폼": 14,
}

# ── 공통경비로 집계할 비목 (인건비·운영비·여비·사업비배분) ──
# ※ '매핑 안 된 나머지'를 잔여로 쓸어담으면 건설비/무형자산 등이 섞여 과다집계됨.
#    반드시 아래 비목만 공통경비로 한정한다.
COMMON_BIMOK = {
    "인건비(110)", "운영비(210)", "여비(220)",
    "사업비 배분(320)", "사업비배분(320)",
}

UNIT_DEF = {
    1:  {"name":"유무선 네트워크 구축",    "vendor":"싸인텔레콤 컨소시엄",   "zone":"공통인프라",          "icon":"📡","color":"#2e80e8"},
    2:  {"name":"모바일 전자시민증(ECC)",  "vendor":"한국정보기술 컨소시엄", "zone":"공통인프라",          "icon":"📱","color":"#7c3aed"},
    3:  {"name":"이노베이션 센터 구축",    "vendor":"호서대학교",            "zone":"배방 이노베이션존",   "icon":"🏢","color":"#22c55e"},
    4:  {"name":"디지털 OASIS SPOT",       "vendor":"(발주준비중)",          "zone":"도고 디지털 OASIS존","icon":"🌿","color":"#f59e0b"},
    5:  {"name":"SDDC Platform 구축",      "vendor":"한국정보기술 컨소시엄", "zone":"공통인프라",          "icon":"☁️","color":"#06b6d4"},
    6:  {"name":"AI 통합관제 플랫폼",      "vendor":"한국정보기술 컨소시엄", "zone":"공통인프라",          "icon":"🤖","color":"#ec4899"},
    7:  {"name":"디지털 OASIS 정보관리",   "vendor":"한국정보기술 컨소시엄", "zone":"도고 디지털 OASIS존","icon":"📊","color":"#10b981"},
    8:  {"name":"DRT 수요응답형 교통",     "vendor":"(미선정)",              "zone":"도고 디지털 OASIS존","icon":"🚌","color":"#f97316"},
    9:  {"name":"감리용역 (신설)",          "vendor":"(업체선정 준비)",       "zone":"공통인프라",          "icon":"🔍","color":"#a78bfa"},
    10: {"name":"스마트폴&디스플레이",      "vendor":"(발주준비중)",          "zone":"공통인프라",          "icon":"🔔","color":"#14b8a6"},
    11: {"name":"메타버스 플랫폼",          "vendor":"(발주준비중)",          "zone":"공통인프라",          "icon":"🌐","color":"#8b5cf6"},
    12: {"name":"디지털 노마드(NOP)",       "vendor":"한국정보기술 컨소시엄", "zone":"도고 디지털 OASIS존","icon":"💻","color":"#0ea5e9"},
    13: {"name":"AI 융복합 서비스",         "vendor":"한국정보기술 컨소시엄", "zone":"공통인프라",          "icon":"🧠","color":"#d946ef"},
    14: {"name":"디지털링크 플랫폼",        "vendor":"한국정보기술 컨소시엄", "zone":"공통인프라",          "icon":"🔗","color":"#84cc16"},
}

# ══════ HTTP FETCH ══════
def fetch_json(url, label=""):
    try:
        req = UR.Request(url, headers={"User-Agent":"Asan-Portal/4.2"})
        with UR.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        print(f"  ✅ {label}: OK")
        return data
    except Exception as e:
        print(f"  ⚠️  {label}: 실패 ({e})")
        return None

# ══════ DATA SOURCING ══════
def source_all():
    """BMS + WBS JSON에서 모든 데이터 추출"""
    sources = {}
    bms_info = None
    cats = []
    projects = []
    wbs_data = {"overall":0,"services":[],"summary":None}

    # ── 1. BMS ──
    print("\n📦 [BMS] 예산 데이터 로딩...")
    bms = fetch_json(URL_BMS, "BMS budget.json")
    if bms and "summary" in bms:
        sources["예산"] = "BMS"
        s = bms["summary"]
        bms_info = {
            "total_budget": s.get("총사업비",0)/1e8,
            "total_exec": s.get("총집행액",0)/1e8,
            "total_remain": s.get("총잔액",0)/1e8,
            "exec_rate": s.get("전체집행률",0),
        }
        # 비목별
        cats = parse_bms_cats(bms)
        # 단위사업별 (BMS 항목 매핑)
        projects = parse_bms_projects(bms)
    else:
        sources["예산"] = "Fallback"
        bms_info = {"total_budget":240,"total_exec":98.8,"total_remain":141.2,"exec_rate":41.16}
        cats = FALLBACK_CATS
        projects = FALLBACK_PROJECTS

    # ── 2. WBS ──
    print("\n📋 [WBS] 공정률 데이터 로딩...")
    ws = fetch_json(URL_WBS_SUMMARY, "WBS summary")
    if ws and "total" in ws:
        sources["WBS"] = "WBS-JSON"
        t = ws["total"]
        wbs_data["overall"] = t.get("actualRate",0)
        wbs_data["summary"] = ws
        wd = fetch_json(URL_WBS_DATA, "WBS data")
        if wd and "items" in wd:
            svcs = []
            for r in wd["items"]:
                if r.get("level")=="1" and r.get("weight",0)>0:
                    svcs.append({"name":r["name"],"rate":round(r.get("actualRate",0)),
                                 "planned":round(r.get("plannedRate",0)),
                                 "weight":r.get("weight",0)})
            svcs.sort(key=lambda x: -x["rate"])
            wbs_data["services"] = svcs
    else:
        sources["WBS"] = "Fallback"
        wbs_data = {"overall":52.3,"services":[],"summary":None}

    return projects, cats, wbs_data, bms_info, sources


def parse_bms_cats(bms):
    CLEAN = {"인건비(110)":"인건비","운영비(210)":"운영비","여비(220)":"여비",
             "연구개발비(260)":"연구개발비","사업비배분(320)":"사업비배분",
             "사업비 배분(320)":"사업비배분","유형자산(430)":"유형자산",
             "무형자산(440)":"무형자산(SW)","건설비(420)":"건설비","기타":"기타"}
    merged = {}
    for b in bms.get("bimok_summary",[]):
        name = CLEAN.get(b.get("비목","기타"), b.get("비목","기타"))
        if name in merged:
            merged[name]["b"] += b["예산"]/1e8; merged[name]["e"] += b["집행"]/1e8
        else:
            merged[name] = {"b": b["예산"]/1e8, "e": b["집행"]/1e8}
    cats = []
    for name in ["인건비","운영비","여비","연구개발비","유형자산","무형자산(SW)","건설비","사업비배분","기타"]:
        if name not in merged: continue
        m = merged[name]
        rate = round(m["e"]/m["b"]*100,1) if m["b"] else 0
        if rate > 100: st,sc = "🟠 초과","#f97316"
        elif rate >= 50: st,sc = "🟢 정상","#22c55e"
        elif rate > 0: st,sc = "🟡 주의","#eab308"
        else: st,sc = "🔴 미집행","#ef4444"
        cats.append({"name":name,"budget":round(m["b"],2),"executed":round(m["e"],2),
                     "rate":rate,"status":st,"status_color":sc,"note":""})
    return cats


def parse_bms_projects(bms):
    """BMS 항목을 단위사업에 매핑하여 집행현황 생성"""
    units = {}
    common_budget = common_exec = 0
    for it in bms.get("items",[]):
        name = it["항목명"]
        num = BMS_UNIT_MAP.get(name)
        if num:
            if num not in units:
                units[num] = {"budget":0,"exec":0}
            units[num]["budget"] += (it.get("총예산") or 0)/1e8
            units[num]["exec"] += (it.get("집행액") or it.get("사용금액합계") or it.get("사용금액") or 0)/1e8
        elif it.get("비목", "") in COMMON_BIMOK:
            # 공통경비: 인건비·운영비·여비·사업비배분 비목만 집계
            common_budget += (it.get("총예산") or 0)/1e8
            common_exec += (it.get("집행액") or it.get("사용금액합계") or it.get("사용금액") or 0)/1e8

    projects = []
    for num in sorted(UNIT_DEF.keys()):
        ud = UNIT_DEF[num]
        u = units.get(num, {"budget":0,"exec":0})
        budget = round(u["budget"],2)
        ex = round(u["exec"],2)
        rate = round(ex/budget*100,1) if budget else 0
        if rate >= 90: status = "✅ 완료"
        elif ex > 0: status = "🔄 진행중"
        elif budget > 0: status = "⏸️ 미착수"
        else: status = "🆕 신설"
        projects.append({
            "num": num, "name": ud["name"], "budget": budget, "executed": ex,
            "exec_rate": rate, "wbs_rate": 0, "status": status,
            "vendor": ud["vendor"], "note": "", "zone": ud["zone"],
            "icon": ud["icon"], "color": ud["color"],
        })

    # 공통경비는 별도 표시용으로 저장
    if common_budget > 0:
        projects.append({
            "num": 0, "name": "공통경비 (인건비·운영비·여비 등)",
            "budget": round(common_budget,2), "executed": round(common_exec,2),
            "exec_rate": round(common_exec/common_budget*100,1) if common_budget else 0,
            "wbs_rate": 0, "status": "🔄 진행중", "vendor": "제일엔지니어링 등",
            "note": "인건비·운영비·여비·사업비배분", "zone": "공통",
            "icon": "🏛️", "color": "#64748b",
        })

    projects.sort(key=lambda x: (x["num"]==0, x["num"]))
    print(f"  ✅ 단위사업 {len(projects)}개 (매핑 {len(units)}개 + 공통경비)")
    return projects


def generate_issues(projects, cats, wbs_data, dday, bms_info=None):
    issues = []
    if bms_info:
        tb,te,er = bms_info["total_budget"],bms_info["total_exec"],bms_info["exec_rate"]
    else:
        tb = sum(p["budget"] for p in projects)
        te = sum(p["executed"] for p in projects)
        er = round(te/tb*100,1) if tb else 0
    tp = dday["pct"]
    gap = tp - er
    if gap > 30:
        issues.append({"level":"🔴 긴급","c":"#ef4444",
            "content":f"예산 집행률({er:.1f}%)이 기간 소진율({tp:.0f}%) 대비 {gap:.0f}%p 부족 — 잔여 {round(tb-te,1)}억 집중 집행 필요","amt":f"{round(tb-te,1)}억"})
    for p in projects:
        if p["num"]==0: continue
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
    {"num":2,"name":"서비스 인프라 플랫폼","budget":45.33,"executed":18.03,"exec_rate":39.8,"wbs_rate":60,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#7c3aed","zone":"공통인프라","icon":"🖥️"},
    {"num":3,"name":"이노베이션 센터 구축","budget":13.00,"executed":11.86,"exec_rate":91.2,"wbs_rate":100,"status":"✅ 완료","vendor":"호서대학교","note":"구축완료","color":"#22c55e","zone":"배방 이노베이션존","icon":"🏢"},
    {"num":4,"name":"디지털 OASIS SPOT","budget":42.00,"executed":0.15,"exec_rate":0.4,"wbs_rate":5,"status":"🔄 진행중","vendor":"(발주준비중)","note":"","color":"#f59e0b","zone":"도고 디지털 OASIS존","icon":"🌿"},
    {"num":5,"name":"SDDC Platform 구축","budget":27.00,"executed":7.09,"exec_rate":26.3,"wbs_rate":43,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#06b6d4","zone":"공통인프라","icon":"☁️"},
    {"num":6,"name":"AI 통합관제 플랫폼","budget":16.00,"executed":9.29,"exec_rate":58.1,"wbs_rate":60,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#ec4899","zone":"공통인프라","icon":"🤖"},
    {"num":7,"name":"디지털 OASIS 정보관리","budget":22.60,"executed":10.93,"exec_rate":48.4,"wbs_rate":43,"status":"🔄 진행중","vendor":"한국정보기술","note":"","color":"#10b981","zone":"도고 디지털 OASIS존","icon":"📊"},
    {"num":8,"name":"DRT 수요응답형 교통","budget":10.00,"executed":0.0,"exec_rate":0.0,"wbs_rate":0,"status":"⏸️ 미착수","vendor":"(미선정)","note":"","color":"#f97316","zone":"도고 디지털 OASIS존","icon":"🚌"},
    {"num":9,"name":"감리용역 (신설)","budget":1.50,"executed":0.0,"exec_rate":0.0,"wbs_rate":0,"status":"🆕 신설","vendor":"(준비중)","note":"","color":"#a78bfa","zone":"공통인프라","icon":"🔍"},
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

def build_html(projects, cats, wbs_data, dday, sources, bms_info):
    ts = NOW_KST.strftime("%Y-%m-%d %H:%M")
    wo = wbs_data.get("overall",0)
    svcs = wbs_data.get("services",[])

    if bms_info and bms_info.get("total_budget"):
        tb=round(bms_info["total_budget"],1); te=round(bms_info["total_exec"],1)
        tr=round(bms_info["total_remain"],1); rate=bms_info["exec_rate"]
    else:
        tb=sum(p["budget"] for p in projects); te=sum(p["executed"] for p in projects)
        tr=round(tb-te,2); rate=round(te/tb*100,1) if tb else 0

    # 단위사업 카드 (공통경비 제외)
    main_projects = [p for p in projects if p["num"]>0]
    common = next((p for p in projects if p["num"]==0), None)
    dc = sum(1 for p in main_projects if "완료" in p["status"])
    pc = sum(1 for p in main_projects if "진행" in p["status"])
    wc = len(main_projects)-dc-pc
    issues = generate_issues(projects, cats, wbs_data, dday, bms_info)
    uc = sum(1 for i in issues if "긴급" in i["level"])
    hc = sum(1 for i in issues if "높음" in i["level"])
    sl = " + ".join(set(sources.values()))

    # Project cards
    ph = ""
    for p in main_projects:
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
  <div class="pcard-note">{str(p.get("note",""))[:65]}</div>
</div>'''

    # 공통경비 요약
    common_html = ""
    if common:
        common_html = f'''<div style="background:rgba(100,116,139,.08);border:1px solid var(--bdr);border-radius:10px;padding:12px 16px;margin-top:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
  <div><span style="font-size:.82rem;font-weight:600">🏛️ 공통경비</span><span style="font-size:.70rem;color:var(--muted);margin-left:8px">{common["note"]}</span></div>
  <div style="display:flex;gap:16px;font-size:.80rem"><span>예산 <b>{common["budget"]:.1f}억</b></span><span>집행 <b>{common["executed"]:.1f}억</b></span><span style="color:#22c55e;font-weight:700">{common["exec_rate"]:.1f}%</span></div>
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
.dbar{{height:10px;background:var(--bdr);border-radius:5px;overflow:hidden}}.dbar div{{height:100%;border-radius:5px}}
.proj-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:10px}}
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
.ict{{flex:1;font-size:.77rem;line-height:1.4}}.iamt{{font-size:.74rem;font-weight:700;white-space:nowrap}}
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
@media(max-width:1100px){{.sys-grid{{grid-template-columns:repeat(3,1fr)}}}}@media(max-width:760px){{.sys-grid{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:480px){{.sys-grid{{grid-template-columns:1fr}}}}
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
  <div class="card"><div class="kl">단위사업 현황</div><div class="kv" style="color:#22c55e">{len(main_projects)}개</div><div class="ks">✅ 완료 {dc}개 · 🔄 진행중 {pc}개<br>⏸️ 미착수·신설 {wc}개</div><div class="kb"><div style="width:{round(dc/max(len(main_projects),1)*100)}%;background:#22c55e"></div></div></div>
</div>
<div class="dual-bar-wrap"><div class="dual-bar-title">📊 사업 진척 현황 비교</div>
  <div class="dual-item"><div class="dual-lbl">⏱ 기간 소진율</div><div class="dbar"><div style="width:{dday["pct"]}%;background:linear-gradient(90deg,#f59e0b,#ef4444)"></div></div><div class="dual-pct" style="color:#f59e0b">{dday["pct"]:.1f}%</div></div>
  <div class="dual-item"><div class="dual-lbl">📋 WBS 공정률</div><div class="dbar"><div style="width:{wo}%;background:linear-gradient(90deg,#7c3aed,#2e80e8)"></div></div><div class="dual-pct" style="color:#7c3aed">{wo:.1f}%</div></div>
  <div class="dual-item"><div class="dual-lbl">💰 예산 집행률</div><div class="dbar"><div style="width:{min(rate,100)}%;background:linear-gradient(90deg,#2e80e8,#06b6d4)"></div></div><div class="dual-pct" style="color:#2e80e8">{rate:.1f}%</div></div>
</div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">🏗️ 단위사업별 현황 ({len(main_projects)}개) <span class="sec-sub">BMS 실시간 · 예산집행률</span></div><div class="proj-grid">{ph}</div>{common_html}</div>
<div class="g2"><div class="card"><div class="sec-title">💰 비목별 예산 집행 현황 <span class="sec-sub">{len(cats)}개 비목</span></div>{ch}</div>
<div class="card"><div class="sec-title">⚙️ WBS 공정률 (Level-1) <span class="sec-sub">{len(svcs)}개 분류</span></div>{wsh}{sh}</div></div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">⚠️ 리스크 현황 (자동 분석) <span class="sec-sub">🔴 긴급 {uc}건 · 🟠 높음 {hc}건</span></div>{ih}</div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">🔗 업무 시스템 바로가기</div>
<div class="sys-section-label">📋 프로젝트 관리 (Notion)</div><div class="sys-grid">
<a class="sys-card" href="https://www.notion.so/21650aa9577d80dc8278e0187c54677f" target="_blank" style="--sc:#2e80e8"><span class="sys-icon">📌</span><div class="sys-info"><div class="sys-name">프로젝트 관리</div><div class="sys-desc">사업 총괄 · 단위사업 현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/559654aed9404d9f88225ea0adc7d746?v=3aa59e73-6641-4463-b157-d7c06c129bfb" target="_blank" style="--sc:#7c3aed"><span class="sys-icon">📊</span><div class="sys-info"><div class="sys-name">WBS 관리</div><div class="sys-desc">175개 작업 · 공정률 추적</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/2aa50aa9577d8128b6d4c5c21d845796" target="_blank" style="--sc:#10b981"><span class="sys-icon">💰</span><div class="sys-info"><div class="sys-name">예산관리 시스템</div><div class="sys-desc">비목별 · 단위사업별 집행현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.notion.so/2b850aa9577d8128ad35d86b79f67d12" target="_blank" style="--sc:#f59e0b"><span class="sys-icon">👥</span><div class="sys-info"><div class="sys-name">인력 현황</div><div class="sys-desc">기관별 투입 현황</div></div><span class="sys-arrow">→</span></a>
</div>
<div class="sys-section-label" style="margin-top:16px">📈 GitHub Pages 대시보드</div><div class="sys-grid">
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/" target="_blank" style="--sc:#22c55e"><span class="sys-icon">🌐</span><div class="sys-info"><div class="sys-name">통합 포털 (현재)</div><div class="sys-desc">본 페이지 · 30분 자동 갱신</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smartcity-WBS/" target="_blank" style="--sc:#7c3aed"><span class="sys-icon">📋</span><div class="sys-info"><div class="sys-name">WBS 대시보드</div><div class="sys-desc">Gantt · 공정률 시각화</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/" target="_blank" style="--sc:#10b981"><span class="sys-icon">💳</span><div class="sys-info"><div class="sys-name">BMS 예산 대시보드</div><div class="sys-desc">예산집행 · 비목별 분석</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-asset-management/" target="_blank" style="--sc:#f59e0b"><span class="sys-icon">🏛️</span><div class="sys-info"><div class="sys-name">자산관리 시스템</div><div class="sys-desc">사업 자산 · 물품 현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-HR-Management-Portal/" target="_blank" style="--sc:#ec4899"><span class="sys-icon">👤</span><div class="sys-info"><div class="sys-name">인력관리 시스템</div><div class="sys-desc">투입인력 · 기관별 현황</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://leesungho-ai.github.io/Asan-Report-Generator/" target="_blank" style="--sc:#00d4aa"><span class="sys-icon">📄</span><div class="sys-info"><div class="sys-name">보고서 생성 시스템</div><div class="sys-desc">주간·월간·분기·연간 AI 보고서</div></div><span class="sys-arrow">→</span></a>
</div>
<div class="sys-section-label" style="margin-top:16px">🏛️ 정부 · 💬 협업</div><div class="sys-grid">
<a class="sys-card" href="https://www.g2b.go.kr" target="_blank" style="--sc:#ef4444"><span class="sys-icon">🛒</span><div class="sys-info"><div class="sys-name">나라장터</div><div class="sys-desc">입찰공고 · 계약관리</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://www.gosims.go.kr" target="_blank" style="--sc:#f97316"><span class="sys-icon">💼</span><div class="sys-info"><div class="sys-name">e나라도움</div><div class="sys-desc">보조금 집행 · 정산</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://app.slack.com/client/T070J9TK0MY/C07061F0MFG" target="_blank" style="--sc:#4a154b"><span class="sys-icon">💬</span><div class="sys-info"><div class="sys-name">Slack #wbs</div><div class="sys-desc">WBS 파일 공유</div></div><span class="sys-arrow">→</span></a>
<a class="sys-card" href="https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal" target="_blank" style="--sc:#6e7681"><span class="sys-icon">⚙️</span><div class="sys-info"><div class="sys-name">GitHub 저장소</div><div class="sys-desc">소스코드 · Actions</div></div><span class="sys-arrow">→</span></a>
</div></div>
<div class="card" style="margin-bottom:18px"><div class="sec-title">👥 사업 추진 체계</div><div class="org-grid">
<div class="org-card" style="background:rgba(46,128,232,.08)"><div style="color:#2e80e8;font-weight:700;margin-bottom:6px">🏛️ 시행기관</div><div style="font-weight:600">아산시</div><div style="color:var(--muted);font-size:.69rem">스마트도시팀 박상국 팀장</div></div>
<div class="org-card" style="background:rgba(34,197,94,.08)"><div style="color:#22c55e;font-weight:700;margin-bottom:6px">🏗️ 직접보조사업자</div><div style="font-weight:600">제일엔지니어링</div><div style="color:var(--muted);font-size:.69rem">PMO · 이성호 이사</div></div>
<div class="org-card" style="background:rgba(168,85,247,.08)"><div style="color:#a78bfa;font-weight:700;margin-bottom:6px">🎓 간접보조사업자</div><div style="font-weight:600">호서대학교</div><div style="color:var(--muted);font-size:.69rem">이노베이션센터 운영</div></div>
<div class="org-card" style="background:rgba(6,182,212,.08)"><div style="color:#06b6d4;font-weight:700;margin-bottom:6px">🔬 간접보조사업자</div><div style="font-weight:600">충남연구원 · KAIST</div><div style="color:var(--muted);font-size:.69rem">연구·기술지원</div></div>
</div></div></div>
<footer>아산시 강소형 스마트시티 통합 포털 v4.2 · 제일엔지니어링 PMO팀 · 데이터 기준: {ts} KST · 소스: {sl} · 30분 자동 동기화</footer>
</body></html>'''


# ══════ MAIN ══════
def main():
    print("="*60)
    print(f"🚀 통합 포털 v4.2 — {NOW_KST.strftime('%Y-%m-%d %H:%M')} KST")
    print(f"   100% 하위시스템 JSON 기반 (Notion 의존 제거)")
    print("="*60)
    projects, cats, wbs_data, bms_info, sources = source_all()
    dday = {
        "label": f"D-{(PROJECT_END-TODAY).days}",
        "remain": (PROJECT_END-TODAY).days,
        "elapsed": (TODAY-PROJECT_START).days,
        "total": (PROJECT_END-PROJECT_START).days,
        "pct": round((TODAY-PROJECT_START).days/(PROJECT_END-PROJECT_START).days*100,1),
    }
    print(f"\n📊 결과:")
    print(f"   소스: {sources}")
    print(f"   집행률: {bms_info['exec_rate']}% (BMS), WBS: {wbs_data['overall']:.1f}%")
    mp = [p for p in projects if p["num"]>0]
    print(f"   단위사업: {len(mp)}개")
    for p in mp:
        print(f"     #{p['num']:2d} {p['name']:25s} 예산:{p['budget']:7.2f}억 집행:{p['executed']:7.2f}억 = {p['exec_rate']:5.1f}%")

    os.makedirs("data", exist_ok=True)
    with open("data/snapshot.json","w",encoding="utf-8") as f:
        json.dump({"meta":{"updated":NOW_KST.strftime("%Y-%m-%d %H:%M KST"),"sources":sources,"version":"v4.2"},
                   "dday":dday,"projects":projects,"cats":cats,
                   "wbs_overall":wbs_data["overall"],"wbs_services":wbs_data.get("services",[]),
                   "bms_info":bms_info,
                   "issues":generate_issues(projects,cats,wbs_data,dday,bms_info)},
                  f, ensure_ascii=False, indent=2)
    print("\n✅ data/snapshot.json")
    html = build_html(projects, cats, wbs_data, dday, sources, bms_info)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)
    print(f"✅ index.html ({len(html):,} bytes)\n🎉 완료!")

if __name__ == "__main__":
    main()
