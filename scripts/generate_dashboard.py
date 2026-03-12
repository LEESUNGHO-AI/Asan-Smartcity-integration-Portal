#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아산시 강소형 스마트시티 통합 포털 대시보드 생성기 v3.0
═══════════════════════════════════════════════════════
● 단위사업 9개 중심 현황판
● Notion 3개 DB 실시간 연동
  - 단위사업별 예산현황  (collection://c6073bc5-...)
  - 비목별 예산현황     (collection://c47fceb7-...)
  - WBS DB            (collection://0ed4b202-...)
● GitHub Actions 30분 자동 실행
"""

import os, json, sys, time
from datetime import date, datetime
from zoneinfo import ZoneInfo
import urllib.request as UR
import urllib.error   as UE

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
KST          = ZoneInfo("Asia/Seoul")
NOW_KST      = datetime.now(KST)
TODAY        = date.today()
PROJECT_START = date(2023, 12, 1)
PROJECT_END   = date(2026, 12, 31)

DB_UNIT = "c6073bc5-b025-499f-8b89-417319d6a27c"
DB_CAT  = "c47fceb7-f639-4cd7-85f9-6c8c4ac89263"
DB_WBS  = "0ed4b202-7037-400e-96f3-9e3455ba63cd"

HEADERS = {
    "Authorization":  f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type":   "application/json",
}

PROJECT_META = {
    1: {"color":"#2e80e8","zone":"공통인프라",          "icon":"📡"},
    2: {"color":"#7c3aed","zone":"공통인프라",          "icon":"🖥️"},
    3: {"color":"#22c55e","zone":"배방 이노베이션존",   "icon":"🏢"},
    4: {"color":"#f59e0b","zone":"도고 디지털 OASIS존","icon":"🌿"},
    5: {"color":"#06b6d4","zone":"공통인프라",          "icon":"☁️"},
    6: {"color":"#ec4899","zone":"공통인프라",          "icon":"🤖"},
    7: {"color":"#10b981","zone":"도고 디지털 OASIS존","icon":"📊"},
    8: {"color":"#f97316","zone":"도고 디지털 OASIS존","icon":"🚌"},
    9: {"color":"#a78bfa","zone":"공통인프라",          "icon":"🔍"},
}

WBS_SERVICES = [
    {"name":"이노베이션 관제센터",    "rate":100,"color":"#22c55e","status":"완료",  "note":"준공완료·운영중"},
    {"name":"유무선 네트워크",        "rate": 67,"color":"#2e80e8","status":"진행중","note":"변경계약 완료, 구축 67%"},
    {"name":"NOP (OASIS 운영서비스)", "rate": 60,"color":"#7c3aed","status":"진행중","note":"상세설계 30%, 7/31 완료목표"},
    {"name":"ECC (모바일 전자시민증)","rate": 60,"color":"#7c3aed","status":"진행중","note":"상세설계 30%, 7/31 완료목표"},
    {"name":"ACP (AI시티관제)",       "rate": 60,"color":"#ec4899","status":"진행중","note":"상세설계 30%, 7/31 완료목표"},
    {"name":"BIS (AI융복합서비스)",   "rate": 60,"color":"#7c3aed","status":"진행중","note":"상세설계 30%, 7/31 완료목표"},
    {"name":"OIM (데이터허브)",       "rate": 43,"color":"#10b981","status":"진행중","note":"계약완료, 상세설계 30%"},
    {"name":"SDDC 기반인프라",        "rate": 43,"color":"#06b6d4","status":"진행중","note":"분리망 완료, 코어구축 30%"},
    {"name":"DRT (수요응답형교통)",   "rate":  0,"color":"#f97316","status":"착수",  "note":"3/16 발주공고 착수"},
    {"name":"메타버스 플랫폼",        "rate":  0,"color":"#f59e0b","status":"착수",  "note":"3/16 발주공고 착수"},
    {"name":"시설물위치기반 플랫폼",  "rate":  0,"color":"#f59e0b","status":"착수",  "note":"3/16 발주공고 착수"},
]

ISSUES = [
    {"level":"🔴 긴급","c":"#ef4444","content":"예산 집행률 저조 (40.9%) — 잔여 142억, 2026년 집중 집행 필요","amt":"142억원"},
    {"level":"🔴 긴급","c":"#ef4444","content":"OASIS SPOT 착공 지연 — 3/16 발주공고 착수, 4월 착공 목표","amt":"35억원"},
    {"level":"🟠 높음","c":"#f59e0b","content":"서비스 인프라(45.33억) 선급금 미집행 — 조속 집행 필요","amt":"45.33억"},
    {"level":"🟠 높음","c":"#f59e0b","content":"SDDC 코어구축 30% — 납품·설치 일정 집중 관리 필요","amt":"27억원"},
    {"level":"🟠 높음","c":"#f59e0b","content":"여비 초과집행 200% — 비목간 전용 또는 실시계획 변경 필요","amt":"0.4억원"},
    {"level":"🟡 주의","c":"#eab308","content":"DRT·메타버스·무인매장·스마트폴 3/16 발주착수 — 4/30 계약 목표","amt":"10억+"},
    {"level":"🟡 주의","c":"#eab308","content":"감리용역 업체선정 지연 — 서비스 인프라 착수 전 선정 필요","amt":"1.6억"},
    {"level":"🟡 주의","c":"#eab308","content":"유무선 네트워크 세목별 초과집행 지속 — 정산 필요","amt":"-"},
]

TIMELINE = [
    {"date":"03/09","type":"완료","done":True, "content":"서비스 인프라 7~9주차 공정보고서 제출"},
    {"date":"03/09","type":"완료","done":True, "content":"[4.6.2] 분리망(보안망·서비스망) 설계/구현 완료"},
    {"date":"03/12","type":"완료","done":True, "content":"Notion WBS DB 현행화 (전체 공정률 49.6%)"},
    {"date":"03/16","type":"발주","done":False,"content":"OASIS SPOT·DRT·메타버스·무인매장·스마트폴 발주공고 착수"},
    {"date":"03/31","type":"마감","done":False,"content":"NOP·ACP·ECC·BIS·OIM 상세설계 1차 완료"},
    {"date":"03/31","type":"마감","done":False,"content":"1분기 예산 집행 점검 (50% 달성 목표)"},
    {"date":"04/30","type":"계약","done":False,"content":"신규 발주 5건 계약 완료 (DRT, 메타버스 등)"},
    {"date":"07/31","type":"완료","done":False,"content":"서비스 플랫폼 전체 개발 완료 (NOP·ECC·ACP·BIS·OIM)"},
    {"date":"10/31","type":"완료","done":False,"content":"통합시험·시범운영·안정화 완료"},
]

FALLBACK_CATS = [
    {"name":"인건비",       "budget":19.0,  "executed":18.3,  "rate":96.3,  "status":"🟢 정상",   "note":"정규직+계약직 (2024년)",       "status_color":"#22c55e"},
    {"name":"운영비",       "budget":7.5,   "executed":4.3,   "rate":57.3,  "status":"🟡 주의",   "note":"부스제작비 초과 184%",          "status_color":"#eab308"},
    {"name":"여비",         "budget":0.4,   "executed":0.8,   "rate":200.0, "status":"🟠 초과",   "note":"⚠️ 초과집행 200%, 비목간 전용", "status_color":"#f97316"},
    {"name":"연구개발비",   "budget":10.0,  "executed":0.0,   "rate":0.0,   "status":"🔴 미집행",  "note":"DRT 플랫폼 (미착수)",           "status_color":"#ef4444"},
    {"name":"유형자산",     "budget":0.2,   "executed":0.16,  "rate":80.0,  "status":"🟢 정상",   "note":"이노베이션센터 PC",             "status_color":"#22c55e"},
    {"name":"무형자산(SW)", "budget":90.5,  "executed":38.25, "rate":42.3,  "status":"🟡 주의",   "note":"6개 플랫폼 개발 진행중",        "status_color":"#eab308"},
    {"name":"건설비",       "budget":99.4,  "executed":23.25, "rate":23.4,  "status":"🟡 주의",   "note":"OASIS SPOT 착공 추진 중",       "status_color":"#eab308"},
    {"name":"사업비배분",   "budget":13.0,  "executed":13.0,  "rate":100.0, "status":"🟢 정상",   "note":"간접보조 교부완료",             "status_color":"#22c55e"},
]

FALLBACK_PROJECTS = [
    {"num":1,"name":"유무선 네트워크 구축",  "budget":11.35,"executed":4.15, "exec_rate":36.6,"wbs_rate":67, "status":"🔄 진행중","vendor":"싸인텔레콤 컨소시엄",   "note":"변경계약·연장 합의서 체결(2/25), 7월 완료 목표",             "color":"#2e80e8","zone":"공통인프라",          "icon":"📡"},
    {"num":2,"name":"서비스 인프라 플랫폼",  "budget":45.33,"executed":0.0,  "exec_rate":0.0, "wbs_rate":60, "status":"🔄 진행중","vendor":"한국정보기술 컨소시엄", "note":"7~9주차 공정보고 완료, NOP·ACP·ECC·BIS 상세설계 진행",      "color":"#7c3aed","zone":"공통인프라",          "icon":"🖥️"},
    {"num":3,"name":"이노베이션 센터 구축",  "budget":13.00,"executed":11.86,"exec_rate":91.2,"wbs_rate":100,"status":"✅ 완료",  "vendor":"호서대학교",            "note":"구축완료·운영중 (리빙랩·관제센터·테스트베드)",               "color":"#22c55e","zone":"배방 이노베이션존",   "icon":"🏢"},
    {"num":4,"name":"디지털 OASIS SPOT",     "budget":35.00,"executed":0.15, "exec_rate":0.4, "wbs_rate":5,  "status":"🔄 진행중","vendor":"(발주준비중)",           "note":"부지확정(도고면 기곡리 296-4), 3/16 발주공고 착수",           "color":"#f59e0b","zone":"도고 디지털 OASIS존","icon":"🌿"},
    {"num":5,"name":"SDDC Platform 구축",    "budget":27.00,"executed":7.09, "exec_rate":26.3,"wbs_rate":43, "status":"🔄 진행중","vendor":"한국정보기술 컨소시엄", "note":"분리망 설계 완료(3/31), 코어구축 30% 진행",                  "color":"#06b6d4","zone":"공통인프라",          "icon":"☁️"},
    {"num":6,"name":"AI 통합관제 플랫폼",    "budget":16.00,"executed":9.29, "exec_rate":58.1,"wbs_rate":60, "status":"🔄 진행중","vendor":"한국정보기술 컨소시엄", "note":"선급금 9.29억 집행완료, 상세설계 30%",                       "color":"#ec4899","zone":"공통인프라",          "icon":"🤖"},
    {"num":7,"name":"디지털 OASIS 정보관리", "budget":25.00,"executed":10.93,"exec_rate":43.7,"wbs_rate":43, "status":"🔄 진행중","vendor":"한국정보기술 컨소시엄", "note":"선급금 10.93억 집행완료, OIM 상세설계 30%",                  "color":"#10b981","zone":"도고 디지털 OASIS존","icon":"📊"},
    {"num":8,"name":"DRT 수요응답형 교통",   "budget":10.00,"executed":0.0,  "exec_rate":0.0, "wbs_rate":0,  "status":"⏸️ 미착수","vendor":"(미선정)",              "note":"3/16 발주공고 착수, 4/30 계약 완료 목표",                    "color":"#f97316","zone":"도고 디지털 OASIS존","icon":"🚌"},
    {"num":9,"name":"감리용역 (신설)",        "budget":1.60, "executed":0.0,  "exec_rate":0.0, "wbs_rate":0,  "status":"🆕 신설",  "vendor":"(업체선정 준비)",       "note":"실시계획 7차 변경 신설, 업체선정 준비 중",                   "color":"#a78bfa","zone":"공통인프라",          "icon":"🔍"},
]

# ══════════════════════════════════════════ Notion API
def notion_query(db_id, filter_body=None, max_pages=3):
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
            print(f"  ⚠️  Notion API 오류 ({db_id[:8]}): {e}"); break
    return results

def prop_num(page, key):
    try:
        v = page["properties"][key]
        t = v.get("type")
        if t == "number": return v["number"] or 0.0
        if t == "formula": return v["formula"].get("number") or 0.0
    except: pass
    return 0.0

def prop_txt(page, key):
    try:
        v = page["properties"][key]
        t = v.get("type")
        if t == "title":     return "".join(x["plain_text"] for x in v["title"])
        if t == "rich_text": return "".join(x["plain_text"] for x in v["rich_text"])
        if t == "select":    return v["select"]["name"] if v["select"] else ""
    except: pass
    return ""

# ══════════════════════════════════════════ 데이터 수집
def fetch_projects():
    print("  📦 단위사업별 예산현황 로딩...")
    rows = notion_query(DB_UNIT)
    if not rows: print("  ⚠️  fallback"); return FALLBACK_PROJECTS
    out = []
    for p in rows:
        num    = int(prop_num(p, "사업번호") or 0)
        name   = prop_txt(p, "사업명")
        budget = prop_num(p, "예산총액(억원)")
        exec_  = prop_num(p, "집행금액(억원)")
        vendor = prop_txt(p, "담당업체") or "-"
        note   = prop_txt(p, "비고") or ""
        status = prop_txt(p, "상태") or "🔄 진행중"
        rate   = round(exec_/budget*100,1) if budget else 0.0
        meta   = PROJECT_META.get(num, {"color":"#6b7280","zone":"-","icon":"📋"})
        fb     = next((x for x in FALLBACK_PROJECTS if x["num"]==num), {})
        if num and name:
            out.append({"num":num,"name":name,"budget":budget,"executed":exec_,
                        "exec_rate":rate,"wbs_rate":fb.get("wbs_rate",0),
                        "status":status,"vendor":vendor,"note":note,
                        **meta})
    out.sort(key=lambda x:x["num"])
    print(f"  ✅ {len(out)}개")
    return out or FALLBACK_PROJECTS

def fetch_cats():
    print("  💰 비목별 예산현황 로딩...")
    rows = notion_query(DB_CAT)
    if not rows: print("  ⚠️  fallback"); return FALLBACK_CATS
    SC = {"🟢 정상":"#22c55e","🟡 주의":"#eab308","🟠 초과":"#f97316","🔴 미집행":"#ef4444"}
    out = []
    for p in rows:
        name  = prop_txt(p, "비목명")
        bgt   = prop_num(p, "예산(억원)")
        ex    = prop_num(p, "집행(억원)")
        st    = prop_txt(p, "상태") or "🟢 정상"
        note  = prop_txt(p, "비고") or ""
        rate  = round(ex/bgt*100,1) if bgt else 0.0
        if name:
            out.append({"name":name,"budget":bgt,"executed":ex,"rate":rate,
                        "status":st,"note":note,"status_color":SC.get(st,"#6b7280")})
    ORDER = ["인건비","운영비","여비","연구개발비","유형자산","무형자산(SW)","건설비","사업비배분"]
    out.sort(key=lambda x: ORDER.index(x["name"]) if x["name"] in ORDER else 99)
    print(f"  ✅ {len(out)}개")
    return out or FALLBACK_CATS

def fetch_wbs():
    print("  📋 WBS Level-1 로딩...")
    rows = notion_query(DB_WBS,{"filter":{"property":"Level","select":{"equals":"1"}}})
    if not rows: print("  ⚠️  fallback 49.6%"); return 49.6
    total_w = weighted = 0
    for p in rows:
        w = prop_num(p, "가중치")
        r = prop_num(p, "실적공정률")
        if w: total_w += w; weighted += w*r
    result = round(weighted/total_w*100,1) if total_w else 49.6
    print(f"  ✅ WBS 공정률: {result}%")
    return result

# ══════════════════════════════════════════ HTML 빌드
STATUS_BADGE = {
    "✅ 완료":("s-done","완료"), "🔄 진행중":("s-prog","진행중"),
    "⏸️ 미착수":("s-wait","미착수"), "🆕 신설":("s-new","신설"),
}
def sbadge(s):
    cls, lbl = STATUS_BADGE.get(s, ("s-etc", s.replace("✅","").replace("🔄","").replace("⏸️","").replace("🆕","").strip()))
    return f'<span class="sbadge {cls}">{lbl}</span>'

def build_html(projects, cats, wbs_overall, dday, source_mode):
    ts = NOW_KST.strftime("%Y-%m-%d %H:%M")

    total_budget = sum(p["budget"]   for p in projects)
    total_exec   = sum(p["executed"] for p in projects)
    total_remain = round(total_budget - total_exec, 2)
    total_rate   = round(total_exec/total_budget*100,1) if total_budget else 0

    done_c = sum(1 for p in projects if "완료" in p["status"])
    prog_c = sum(1 for p in projects if "진행" in p["status"])
    wait_c = len(projects) - done_c - prog_c
    urg_c  = sum(1 for i in ISSUES if "긴급" in i["level"])
    high_c = sum(1 for i in ISSUES if "높음" in i["level"])

    # ── 프로젝트 카드 ──
    proj_html = ""
    for p in projects:
        col = p.get("color","#2e80e8"); icon = p.get("icon","📋"); zone = p.get("zone","-")
        er  = p["exec_rate"]; wr = p["wbs_rate"]
        remain = round(p["budget"]-p["executed"],2)
        zone_cls = "badge-oasis" if "OASIS" in zone else ("badge-inno" if "이노" in zone else "badge-common")
        proj_html += f"""
<div class="pcard" style="border-top:3px solid {col}">
  <div class="pcard-h">
    <span class="pcard-num" style="color:{col}">{icon} #{p['num']}</span>
    <span class="pzone {zone_cls}">{zone}</span>
    {sbadge(p['status'])}
  </div>
  <div class="pcard-name">{p['name']}</div>
  <div class="pcard-vendor">🏢 {str(p['vendor'])[:24]}</div>
  <div class="pcard-metrics">
    <div class="pm-block">
      <div class="pm-label">예산총액</div>
      <div class="pm-val" style="color:{col}">{p['budget']:.2f}<span class="pm-unit">억</span></div>
    </div>
    <div class="pm-block">
      <div class="pm-label">집행금액</div>
      <div class="pm-val">{p['executed']:.2f}<span class="pm-unit">억</span></div>
    </div>
    <div class="pm-block">
      <div class="pm-label">잔액</div>
      <div class="pm-val" style="color:#94a3b8">{remain:.2f}<span class="pm-unit">억</span></div>
    </div>
  </div>
  <div class="pbar-row">
    <span class="pbar-lbl">예산집행</span>
    <div class="pbar-wrap"><div class="bb"><div style="width:{min(er,100)}%;background:{col};height:100%;border-radius:4px"></div></div></div>
    <span class="pbar-pct" style="color:{col}">{er:.1f}%</span>
  </div>
  <div class="pbar-row">
    <span class="pbar-lbl">WBS공정</span>
    <div class="pbar-wrap"><div class="bb"><div style="width:{min(wr,100)}%;background:{col}88;height:100%;border-radius:4px"></div></div></div>
    <span class="pbar-pct" style="color:{col}aa">{wr}%</span>
  </div>
  <div class="pcard-note">{str(p['note'])[:65]}</div>
</div>"""

    # ── 비목별 예산 ──
    cat_html = ""
    for c in cats:
        r = min(c["rate"],100); sc = c.get("status_color","#2e80e8")
        over = "⚠️ " if c["rate"]>100 else ""
        cat_html += f"""<div class="bi">
  <div class="bih"><span class="bin">{c['name']}</span><span class="bir" style="color:{sc}">{over}{c['rate']:.1f}%</span></div>
  <div class="bb"><div style="width:{r}%;background:{sc};height:100%;border-radius:4px"></div></div>
  <div class="bd">{c['budget']:.1f}억 예산 / {c['executed']:.2f}억 집행 · {str(c['note'])[:30]}</div>
</div>"""

    # ── WBS 서비스 ──
    svc_html = ""
    for s in WBS_SERVICES:
        col = s["color"]; r = s["rate"]
        st_c = "#22c55e" if s["status"]=="완료" else ("#2e80e8" if s["status"]=="진행중" else "#f59e0b")
        svc_html += f"""<div class="bi">
  <div class="bih"><span class="bin">{s['name']}</span><span class="bir" style="color:{col}">{r}%</span></div>
  <div class="bb"><div style="width:{r}%;background:{col};height:100%;border-radius:4px"></div></div>
  <div class="bd"><span style="color:{st_c};font-size:.68rem">{s['status']}</span> · {s['note']}</div>
</div>"""

    # ── 이슈 ──
    issue_html = ""
    for i in ISSUES:
        issue_html += f"""<div class="irow" style="border-left:3px solid {i['c']}">
  <div class="ilv" style="color:{i['c']}">{i['level']}</div>
  <div class="ict">{i['content']}</div>
  <div class="iamt" style="color:{i['c']}">{i['amt']}</div>
</div>"""

    # ── 타임라인 ──
    tl_html = ""
    TC = {"완료":"#22c55e","발주":"#2e80e8","마감":"#f59e0b","계약":"#7c3aed"}
    for t in TIMELINE:
        tc = TC.get(t["type"],"#8fa3c0"); mk = "✅" if t["done"] else "📋"
        tl_html += f"""<div class="tli">
  <div class="tld">{t['date']}</div>
  <span class="tlt" style="background:{tc}22;color:{tc}">{t['type']}</span>
  <div class="tlc">{mk} {t['content']}</div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>아산시 강소형 스마트시티 통합 포털</title>
<style>
:root{{--bg:#0f1623;--card:#1a2540;--bdr:#2a3a5a;--txt:#e2e8f0;--muted:#8fa3c0;--acc:#2e80e8;--ok:#22c55e;--pri:#1a3a6b}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Malgun Gothic','맑은 고딕',sans-serif;background:var(--bg);color:var(--txt);font-size:14px}}
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
.pcard-name{{font-size:.92rem;font-weight:700;color:var(--txt);line-height:1.3}}
.pcard-vendor{{font-size:.70rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.pcard-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:4px 0}}
.pm-block{{background:rgba(255,255,255,.04);border-radius:7px;padding:7px 8px;text-align:center}}
.pm-label{{font-size:.63rem;color:var(--muted);margin-bottom:2px}}
.pm-val{{font-size:.95rem;font-weight:700}}.pm-unit{{font-size:.65rem;color:var(--muted);font-weight:400}}
.pbar-row{{display:grid;grid-template-columns:52px 1fr 42px;align-items:center;gap:7px}}
.pbar-lbl{{font-size:.67rem;color:var(--muted);text-align:right}}
.pbar-wrap{{flex:1}}
.pbar-pct{{font-size:.72rem;font-weight:700;text-align:right}}
.pcard-note{{font-size:.67rem;color:var(--muted);line-height:1.4;background:rgba(255,255,255,.03);border-radius:6px;padding:5px 8px;border-left:2px solid var(--bdr)}}
.bi{{margin-bottom:11px}}
.bih{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;gap:8px}}
.bin{{font-size:.80rem;font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bir{{font-size:.78rem;font-weight:700;white-space:nowrap}}
.bb{{height:7px;background:var(--bdr);border-radius:4px;overflow:hidden}}
.bd{{font-size:.67rem;color:var(--muted);margin-top:3px;line-height:1.4}}
.irow{{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border-radius:8px;background:rgba(255,255,255,.03);margin-bottom:6px}}
.ilv{{font-size:.71rem;font-weight:700;white-space:nowrap;width:62px;flex-shrink:0;margin-top:1px}}
.ict{{flex:1;font-size:.77rem;line-height:1.4}}
.iamt{{font-size:.74rem;font-weight:700;white-space:nowrap;margin-top:1px}}
.tli{{display:flex;align-items:flex-start;gap:7px;padding:6px 0;border-bottom:1px solid var(--bdr);font-size:.77rem}}
.tli:last-child{{border-bottom:none}}
.tld{{color:#2e80e8;font-weight:700;width:32px;flex-shrink:0}}
.tlt{{border-radius:8px;padding:1px 6px;font-size:.66rem;flex-shrink:0;margin-top:1px}}
.tlc{{flex:1;line-height:1.4}}
.sbadge{{padding:2px 8px;border-radius:10px;font-size:.68rem;font-weight:600;white-space:nowrap;flex-shrink:0}}
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
/* ── 시스템 바로가기 ── */
.sys-section-label{{font-size:.74rem;font-weight:700;color:var(--muted);text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:9px;padding-left:2px}}
.sys-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:4px}}
@media(max-width:1100px){{.sys-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:760px){{.sys-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:480px){{.sys-grid{{grid-template-columns:1fr}}}}
.sys-card{{display:flex;align-items:center;gap:10px;padding:10px 12px;
  border-radius:9px;border:1px solid var(--bdr);
  background:rgba(255,255,255,.03);
  text-decoration:none;color:var(--txt);
  transition:all .18s;cursor:pointer}}
.sys-card:hover{{background:rgba(var(--sc-rgb,46,128,232),.12);
  border-color:var(--sc,var(--acc));
  transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.3)}}
.sys-icon{{font-size:1.35rem;flex-shrink:0;width:32px;text-align:center}}
.sys-info{{flex:1;min-width:0}}
.sys-name{{font-size:.79rem;font-weight:700;color:var(--txt);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sys-desc{{font-size:.66rem;color:var(--muted);margin-top:1px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sys-arrow{{font-size:.80rem;color:var(--muted);flex-shrink:0;
  transition:transform .18s;margin-left:2px}}
.sys-card:hover .sys-arrow{{transform:translateX(3px);color:var(--sc,var(--acc))}}
.sys-card:hover .sys-name{{color:var(--sc,var(--acc))}}
</style>
</head>
<body>
<header>
  <div>
    <div class="ht">🌆 아산시 강소형 스마트시티 통합 포털</div>
    <div class="hs">디지털 OASIS 구현 · 충남 아산시 도고면·배방읍 일원 · 총 240억원 · '23.12 ~ '26.12</div>
  </div>
  <div class="hr">
    <span class="badge">📅 {dday['label']}</span>
    <span class="badge">⚡ WBS {wbs_overall}%</span>
    <span class="src">{source_mode}</span>
    <span class="upd">🕐 {ts} KST</span>
  </div>
</header>
<div class="wrap">

<!-- KPI 4종 -->
<div class="g4">
  <div class="card">
    <div class="kl">예산 집행률</div>
    <div class="kv" style="color:#2e80e8">{total_rate:.1f}%</div>
    <div class="ks">{total_exec:.1f}억 집행 / {total_remain:.1f}억 잔액<br>총 {total_budget:.1f}억원</div>
    <div class="kb"><div style="width:{min(total_rate,100)}%;background:#2e80e8"></div></div>
  </div>
  <div class="card">
    <div class="kl">WBS 전체 공정률</div>
    <div class="kv" style="color:#7c3aed">{wbs_overall:.1f}%</div>
    <div class="ks">계획 대비 진행 수준<br>Level-1 가중평균 기준</div>
    <div class="kb"><div style="width:{min(wbs_overall,100)}%;background:#7c3aed"></div></div>
  </div>
  <div class="card">
    <div class="kl">사업 기간 / D-Day</div>
    <div class="kv" style="color:#f59e0b">{dday['label']}</div>
    <div class="ks">경과 {dday['elapsed']}일 / 총 {dday['total']}일<br>기간 소진율 {dday['pct']:.1f}%</div>
    <div class="kb"><div style="width:{dday['pct']}%;background:#f59e0b"></div></div>
  </div>
  <div class="card">
    <div class="kl">단위사업 현황</div>
    <div class="kv" style="color:#22c55e">{len(projects)}개</div>
    <div class="ks">✅ 완료 {done_c}개 · 🔄 진행중 {prog_c}개<br>⏸️ 미착수·신설 {wait_c}개</div>
    <div class="kb"><div style="width:{round(done_c/max(len(projects),1)*100)}%;background:#22c55e"></div></div>
  </div>
</div>

<!-- 이중 진척 바 -->
<div class="dual-bar-wrap">
  <div class="dual-bar-title">📊 사업 진척 현황 비교</div>
  <div class="dual-item">
    <div class="dual-lbl">⏱ 기간 소진율</div>
    <div class="dbar"><div style="width:{dday['pct']}%;background:linear-gradient(90deg,#f59e0b,#ef4444)"></div></div>
    <div class="dual-pct" style="color:#f59e0b">{dday['pct']:.1f}%</div>
  </div>
  <div class="dual-item">
    <div class="dual-lbl">📋 WBS 공정률</div>
    <div class="dbar"><div style="width:{wbs_overall}%;background:linear-gradient(90deg,#7c3aed,#2e80e8)"></div></div>
    <div class="dual-pct" style="color:#7c3aed">{wbs_overall:.1f}%</div>
  </div>
  <div class="dual-item">
    <div class="dual-lbl">💰 예산 집행률</div>
    <div class="dbar"><div style="width:{min(total_rate,100)}%;background:linear-gradient(90deg,#2e80e8,#06b6d4)"></div></div>
    <div class="dual-pct" style="color:#2e80e8">{total_rate:.1f}%</div>
  </div>
</div>

<!-- 단위사업 카드 9개 -->
<div class="card" style="margin-bottom:18px">
  <div class="sec-title">🏗️ 단위사업별 현황 (9개 사업) <span class="sec-sub">예산집행률 / WBS공정률</span></div>
  <div class="proj-grid">{proj_html}</div>
</div>

<!-- 비목별 예산 + WBS 서비스 -->
<div class="g2">
  <div class="card">
    <div class="sec-title">💰 비목별 예산 집행 현황 <span class="sec-sub">8개 비목</span></div>
    {cat_html}
  </div>
  <div class="card">
    <div class="sec-title">⚙️ 서비스별 WBS 공정률 <span class="sec-sub">11개 서비스</span></div>
    {svc_html}
  </div>
</div>

<!-- 이슈 + 타임라인 -->
<div class="g2">
  <div class="card">
    <div class="sec-title">⚠️ 리스크 현황 <span class="sec-sub">🔴 긴급 {urg_c}건 · 🟠 높음 {high_c}건</span></div>
    {issue_html}
  </div>
  <div class="card">
    <div class="sec-title">📅 3월 주요 일정 <span class="sec-sub">2026년 1~2분기</span></div>
    {tl_html}
  </div>
</div>

<!-- 시스템 바로가기 -->
<div class="card" style="margin-bottom:18px">
  <div class="sec-title">🔗 업무 시스템 바로가기 <span class="sec-sub">클릭하여 접속</span></div>
  <div class="sys-section-label">📋 프로젝트 관리 (Notion)</div>
  <div class="sys-grid">
    <a class="sys-card" href="https://www.notion.so/21650aa9577d80dc8278e0187c54677f" target="_blank" style="--sc:#2e80e8">
      <span class="sys-icon">📌</span>
      <div class="sys-info">
        <div class="sys-name">프로젝트 관리</div>
        <div class="sys-desc">사업 총괄 · 단위사업 현황</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.notion.so/559654aed9404d9f88225ea0adc7d746?v=3aa59e73-6641-4463-b157-d7c06c129bfb" target="_blank" style="--sc:#7c3aed">
      <span class="sys-icon">📊</span>
      <div class="sys-info">
        <div class="sys-name">WBS 관리</div>
        <div class="sys-desc">187개 작업 · 공정률 추적</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.notion.so/2aa50aa9577d8128b6d4c5c21d845796" target="_blank" style="--sc:#10b981">
      <span class="sys-icon">💰</span>
      <div class="sys-info">
        <div class="sys-name">예산관리 시스템</div>
        <div class="sys-desc">비목별 · 단위사업별 집행현황</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.notion.so/2b850aa9577d8128ad35d86b79f67d12" target="_blank" style="--sc:#f59e0b">
      <span class="sys-icon">👥</span>
      <div class="sys-info">
        <div class="sys-name">인력 현황 대시보드</div>
        <div class="sys-desc">54명 · 기관별 투입 현황</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.notion.so/2aa50aa9577d817da233c79ce0c441fe" target="_blank" style="--sc:#06b6d4">
      <span class="sys-icon">🖥️</span>
      <div class="sys-info">
        <div class="sys-name">통합 대시보드</div>
        <div class="sys-desc">Notion 통합 현황판</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.notion.so/2a750aa9577d8080af05e5f952d1c8b4" target="_blank" style="--sc:#ec4899">
      <span class="sys-icon">🗺️</span>
      <div class="sys-info">
        <div class="sys-name">프로덕트 로드맵</div>
        <div class="sys-desc">서비스별 개발 로드맵</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
  </div>

  <div class="sys-section-label" style="margin-top:16px">📈 GitHub Pages 대시보드</div>
  <div class="sys-grid">
    <a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/" target="_blank" style="--sc:#22c55e">
      <span class="sys-icon">🌐</span>
      <div class="sys-info">
        <div class="sys-name">통합 포털 (현재)</div>
        <div class="sys-desc">본 페이지 · 30분 자동 갱신</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smartcity-WBS/" target="_blank" style="--sc:#7c3aed">
      <span class="sys-icon">📋</span>
      <div class="sys-info">
        <div class="sys-name">WBS 대시보드</div>
        <div class="sys-desc">Gantt · 공정률 시각화</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/" target="_blank" style="--sc:#10b981">
      <span class="sys-icon">💳</span>
      <div class="sys-info">
        <div class="sys-name">BMS 예산 대시보드</div>
        <div class="sys-desc">예산집행 · 비목별 분석</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
  </div>

  <div class="sys-section-label" style="margin-top:16px">🏛️ 정부 업무 시스템</div>
  <div class="sys-grid">
    <a class="sys-card" href="https://www.g2b.go.kr" target="_blank" style="--sc:#ef4444">
      <span class="sys-icon">🛒</span>
      <div class="sys-info">
        <div class="sys-name">나라장터</div>
        <div class="sys-desc">입찰공고 · 계약관리 · 조달</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.gosims.go.kr" target="_blank" style="--sc:#f97316">
      <span class="sys-icon">💼</span>
      <div class="sys-info">
        <div class="sys-name">e나라도움</div>
        <div class="sys-desc">보조금 집행 · 정산 관리</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.smartcity.go.kr" target="_blank" style="--sc:#2e80e8">
      <span class="sys-icon">🏙️</span>
      <div class="sys-info">
        <div class="sys-name">국토부 스마트시티</div>
        <div class="sys-desc">사업 정보 · 정책 동향</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://www.asan.go.kr" target="_blank" style="--sc:#06b6d4">
      <span class="sys-icon">🌿</span>
      <div class="sys-info">
        <div class="sys-name">아산시청</div>
        <div class="sys-desc">발주처 · 스마트도시팀</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
  </div>

  <div class="sys-section-label" style="margin-top:16px">💬 협업 도구</div>
  <div class="sys-grid">
    <a class="sys-card" href="https://app.slack.com/client/T070J9TK0MY/C07061F0MFG" target="_blank" style="--sc:#4a154b">
      <span class="sys-icon">💬</span>
      <div class="sys-info">
        <div class="sys-name">Slack #wbs</div>
        <div class="sys-desc">WBS 파일 공유 · 동기화</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://app.slack.com/client/T070J9TK0MY/C0836U9HVU1" target="_blank" style="--sc:#4a154b">
      <span class="sys-icon">💬</span>
      <div class="sys-info">
        <div class="sys-name">Slack #플랜예산</div>
        <div class="sys-desc">예산 xlsx · 집행현황 공유</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://docs.google.com/spreadsheets/d/12LVhySV-AkKCOvd2Q2H1qoBclmtpw5894njN_8B2TQI" target="_blank" style="--sc:#34a853">
      <span class="sys-icon">📗</span>
      <div class="sys-info">
        <div class="sys-name">WBS 원본 Sheets</div>
        <div class="sys-desc">Google Sheets · Notion 동기화</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
    <a class="sys-card" href="https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal" target="_blank" style="--sc:#6e7681">
      <span class="sys-icon">⚙️</span>
      <div class="sys-info">
        <div class="sys-name">GitHub 저장소</div>
        <div class="sys-desc">포털 소스코드 · Actions 관리</div>
      </div>
      <span class="sys-arrow">→</span>
    </a>
  </div>
</div>

<!-- 추진 체계 -->
<div class="card" style="margin-bottom:18px">
  <div class="sec-title">👥 사업 추진 체계</div>
  <div class="org-grid">
    <div class="org-card" style="background:rgba(46,128,232,.08)">
      <div style="color:#2e80e8;font-weight:700;margin-bottom:6px">🏛️ 시행기관</div>
      <div style="font-weight:600">아산시</div>
      <div style="color:var(--muted);font-size:.69rem">스마트도시팀 박상국 팀장<br>오세현 시장</div>
    </div>
    <div class="org-card" style="background:rgba(34,197,94,.08)">
      <div style="color:#22c55e;font-weight:700;margin-bottom:6px">🏗️ 직접보조사업자</div>
      <div style="font-weight:600">제일엔지니어링</div>
      <div style="color:var(--muted);font-size:.69rem">PMO · 이성호 이사<br>임혁 이사 (PMO Lead)</div>
    </div>
    <div class="org-card" style="background:rgba(168,85,247,.08)">
      <div style="color:#a78bfa;font-weight:700;margin-bottom:6px">🎓 간접보조사업자</div>
      <div style="font-weight:600">호서대학교</div>
      <div style="color:var(--muted);font-size:.69rem">이노베이션센터 운영<br>KTX캠퍼스 내</div>
    </div>
    <div class="org-card" style="background:rgba(6,182,212,.08)">
      <div style="color:#06b6d4;font-weight:700;margin-bottom:6px">🔬 간접보조사업자</div>
      <div style="font-weight:600">충남연구원 · KAIST</div>
      <div style="color:var(--muted);font-size:.69rem">연구·기술지원<br>성과지표 관리</div>
    </div>
  </div>
</div>

</div>
<footer>
  아산시 강소형 스마트시티 조성사업 통합 포털 &nbsp;·&nbsp;
  제일엔지니어링 PMO팀 &nbsp;·&nbsp;
  데이터 기준: {ts} KST &nbsp;·&nbsp;
  Notion → GitHub Actions 30분 자동 동기화
</footer>
</body></html>"""

# ══════════════════════════════════════════ MAIN
def main():
    print("="*50)
    print(f"🚀 대시보드 v3.0 생성 시작: {NOW_KST.strftime('%Y-%m-%d %H:%M')} KST")
    print("="*50)

    mode = "📡 Notion 실시간" if NOTION_TOKEN else "📋 Fallback 데이터"

    if NOTION_TOKEN:
        print("✅ NOTION_TOKEN → Notion API 호출")
        projects = fetch_projects()
        cats     = fetch_cats()
        wbs_val  = fetch_wbs()
    else:
        print("⚠️  NOTION_TOKEN 없음 → Fallback")
        projects = FALLBACK_PROJECTS
        cats     = FALLBACK_CATS
        wbs_val  = 49.6

    dday = {
        "label":   f"D-{(PROJECT_END-TODAY).days}",
        "remain":  (PROJECT_END-TODAY).days,
        "elapsed": (TODAY-PROJECT_START).days,
        "total":   (PROJECT_END-PROJECT_START).days,
        "pct":     round((TODAY-PROJECT_START).days/(PROJECT_END-PROJECT_START).days*100,1),
    }

    # snapshot.json
    os.makedirs("data", exist_ok=True)
    with open("data/snapshot.json","w",encoding="utf-8") as f:
        json.dump({"meta":{"updated":NOW_KST.strftime("%Y-%m-%d %H:%M KST"),"source":mode},
                   "dday":dday,"projects":projects,"cats":cats,
                   "wbs_overall":wbs_val,"issues":ISSUES,"timeline":TIMELINE},
                  f, ensure_ascii=False, indent=2)
    print("✅ data/snapshot.json 저장")

    # index.html
    html = build_html(projects, cats, wbs_val, dday, mode)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)
    print(f"✅ index.html 생성 ({len(html):,} bytes)")
    print("🎉 완료!")

if __name__ == "__main__":
    main()
