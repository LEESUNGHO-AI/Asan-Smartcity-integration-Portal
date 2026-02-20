#!/usr/bin/env python3
"""
아산시 강소형 스마트시티 대시보드 자동 생성기
Notion API → 데이터 파싱 → index.html 직접 생성 (CORS 문제 없음)
"""

import os
import json
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import math

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
NOTION_TOKEN    = os.environ.get("NOTION_TOKEN", "")
BUDGET_PAGE_ID  = os.environ.get("NOTION_BUDGET_PAGE_ID", "2e050aa9577d81a8baa0d7decdac9010")

PROJECT_START   = date(2023, 12, 1)
PROJECT_END     = date(2026, 12, 31)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type":  "application/json",
}

KST_NOW = datetime.utcnow()  # GitHub Actions UTC, 표시 시 +9


# ──────────────────────────────────────────────
# Notion 유틸
# ──────────────────────────────────────────────
def notion_get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def notion_post(url, body=None):
    r = requests.post(url, headers=HEADERS, json=body or {}, timeout=20)
    r.raise_for_status()
    return r.json()


# ──────────────────────────────────────────────
# 데이터 수집
# ──────────────────────────────────────────────
def fetch_budget_page():
    """예산 총괄 현황 페이지의 블록 내용 파싱"""
    blocks = []
    cursor = None
    page_id = BUDGET_PAGE_ID.replace("-", "")
    
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = notion_get(f"https://api.notion.com/v1/blocks/{page_id}/children", params)
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks

def extract_text(rich_text):
    return "".join(t.get("plain_text", "") for t in (rich_text or []))

def parse_table_block(block_id):
    """테이블 블록 → 2D list"""
    data = notion_get(f"https://api.notion.com/v1/blocks/{block_id}/children")
    rows = []
    for row_block in data.get("results", []):
        cells = row_block.get("table_row", {}).get("cells", [])
        rows.append([extract_text(cell) for cell in cells])
    return rows


# ──────────────────────────────────────────────
# 실제 데이터 파싱 (Notion 페이지 기반)
# ──────────────────────────────────────────────
def get_dashboard_data():
    """Notion에서 데이터를 수집해 대시보드 데이터 딕셔너리 반환"""
    
    data = {
        "meta": {},
        "dday": {},
        "budget": {},
        "projects": [],
        "issues": [],
        "timeline": [],
    }

    # ── D-Day 계산
    today = date.today()
    total_days   = (PROJECT_END - PROJECT_START).days
    elapsed_days = (today - PROJECT_START).days
    remain_days  = (PROJECT_END - today).days
    elapsed_pct  = round(elapsed_days / total_days * 100, 1) if total_days else 0

    data["dday"] = {
        "today":        today.strftime("%Y-%m-%d"),
        "start":        PROJECT_START.strftime("%Y-%m-%d"),
        "end":          PROJECT_END.strftime("%Y-%m-%d"),
        "total_days":   total_days,
        "elapsed_days": elapsed_days,
        "remain_days":  remain_days,
        "elapsed_pct":  elapsed_pct,
        "dday_label":   f"D-{remain_days}" if remain_days >= 0 else f"D+{abs(remain_days)}",
    }

    # ── Notion에서 데이터 수집 시도
    if NOTION_TOKEN:
        try:
            _fetch_notion_data(data)
        except Exception as e:
            print(f"⚠️ Notion API 오류: {e} — 기본 데이터 사용")
            _use_default_data(data)
    else:
        print("⚠️ NOTION_TOKEN 없음 — 기본 데이터 사용")
        _use_default_data(data)

    # ── 메타
    kst_str = (KST_NOW).strftime("%Y-%m-%d %H") + f":{KST_NOW.strftime('%M')} UTC"
    data["meta"] = {
        "last_updated": (KST_NOW).strftime("%Y-%m-%d %H:%M") + " KST+9h",
        "source": "Notion API 자동 연동",
    }

    return data


def _fetch_notion_data(data):
    """Notion API로 실제 데이터 파싱"""
    page_id = BUDGET_PAGE_ID.replace("-", "")
    blocks_data = notion_get(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        {"page_size": 100}
    )
    blocks = blocks_data.get("results", [])

    # 테이블 블록 순서대로 파싱
    tables = []
    for b in blocks:
        if b.get("type") == "table":
            table_rows = parse_table_block(b["id"])
            tables.append(table_rows)

    # 테이블 인덱스 (Notion 페이지 구조 기반):
    # 0: 재원별 집행 (4행 헤더 포함)
    # 1: 비목별 집행 (9행)
    # 2: 단위사업별 (9행)
    # 3: 간접보조 (4행)
    # 4: 2월 일정
    # 5: 최근 지출

    # 예산 요약 (비목별 테이블)
    budget_cats = []
    if len(tables) > 1:
        cat_table = tables[1]  # 비목별
        for row in cat_table[1:]:  # 헤더 제외
            if len(row) >= 5 and row[0] not in ("", "비목", "합 계", "합계"):
                try:
                    budget_val  = float(row[1].replace("억", "").strip()) * 1e8 if "억" in row[1] else 0
                    exec_val    = float(row[2].replace("억", "").strip()) * 1e8 if "억" in row[2] else 0
                    rate_str    = row[4].replace("%", "").strip()
                    rate        = float(rate_str) if rate_str else 0
                    budget_cats.append({
                        "name":     row[0],
                        "budget":   budget_val,
                        "executed": exec_val,
                        "rate":     rate,
                        "note":     row[5] if len(row) > 5 else "",
                    })
                except:
                    pass

    # 단위사업별 (projects)
    projects = []
    if len(tables) > 2:
        proj_table = tables[2]
        status_map = {
            "✅": "✅ 완료",
            "🔄": "🔄 진행중",
            "⏸️": "⏸️ 대기",
            "🆕": "🆕 신설",
        }
        for row in proj_table[1:]:
            if len(row) >= 6:
                name = row[1].strip()
                if not name:
                    continue
                try:
                    budget_val = float(row[2].replace("억", "").strip()) * 1e8 if "억" in row[2] else 0
                    exec_val   = float(row[3].replace("억", "").replace("-", "0").strip()) * 1e8 if "억" in row[3] else 0
                    rate_str   = row[4].replace("%", "").strip()
                    rate       = float(rate_str) if rate_str else 0
                    status_raw = row[5].strip()
                    status = "🔄 진행중"
                    for emoji, mapped in status_map.items():
                        if emoji in status_raw:
                            status = mapped
                            break
                    projects.append({
                        "name":     name,
                        "budget":   budget_val,
                        "executed": exec_val,
                        "rate":     rate,
                        "status":   status,
                        "note":     status_raw,
                    })
                except:
                    pass

    # 예산 합계
    total_budget   = 240e8  # 240억 (고정)
    total_executed = 98e8   # 기본값
    exec_rate      = 40.8

    if budget_cats:
        # 비목별 합계에서 추출
        for row in (tables[1] if len(tables) > 1 else []):
            if "합" in (row[0] if row else ""):
                try:
                    total_executed = float(row[2].replace("억", "").strip()) * 1e8
                    exec_rate = float(row[4].replace("%", "").strip())
                except:
                    pass

    data["budget"] = {
        "total":       total_budget,
        "executed":    total_executed,
        "remaining":   total_budget - total_executed,
        "exec_rate":   exec_rate,
        "categories":  budget_cats,
    }
    data["projects"] = projects if projects else _default_projects()

    # 일정/이슈 (2월 일정 테이블)
    timeline = []
    if len(tables) > 4:
        for row in tables[4][1:]:
            if len(row) >= 4:
                timeline.append({
                    "date":    row[0],
                    "type":    row[1],
                    "content": row[2],
                    "status":  row[3],
                })
    data["timeline"] = timeline

    # 이슈 (리스크)
    data["issues"] = _default_issues()  # callout 파싱 복잡 → 기본값 사용


def _default_projects():
    return [
        {"name": "유무선 네트워크 구축",           "budget": 11.35e8, "executed": 4.15e8, "rate": 36.6, "status": "✅ 완료",   "note": "계약완료 (연장 협의 중)"},
        {"name": "서비스 인프라 플랫폼",       "budget": 45.33e8, "executed": 0,       "rate":  0.0, "status": "🔄 진행중", "note": "계약체결 진행중"},
        {"name": "이노베이션 센터 구축",             "budget": 13.0e8,  "executed": 11.86e8,"rate": 91.2, "status": "✅ 완료",   "note": "구축완료 (운영중)"},
        {"name": "디지털 OASIS SPOT",              "budget": 35.0e8,  "executed": 0.15e8,  "rate":  0.4, "status": "🔄 진행중", "note": "부지승인 완료, 설계용역 진행"},
        {"name": "SDDC Platform 구축",             "budget": 27.0e8,  "executed": 7.09e8,  "rate": 26.2, "status": "🔄 진행중", "note": "서버실 구축 진행중"},
        {"name": "AI 통합관제 플랫폼",              "budget": 16.0e8,  "executed": 9.29e8,  "rate": 58.1, "status": "🔄 진행중", "note": "서비스 인프라에 통합 계약"},
        {"name": "디지털 OASIS 정보관리",           "budget": 25.0e8,  "executed": 10.93e8, "rate": 43.7, "status": "🔄 진행중", "note": "개발 진행중"},
        {"name": "DRT 수요응답형 교통",             "budget": 10.0e8,  "executed": 0,        "rate":  0.0, "status": "⏸️ 대기",  "note": "설계 진행중"},
        {"name": "감리용역 (신설)",                 "budget":  1.6e8,  "executed": 0,        "rate":  0.0, "status": "🆕 신설",  "note": "업체선정 준비"},
    ]

def _default_issues():
    return [
        {"priority": "🔴 긴급", "content": "예산 집행률 저조 (40.8%) - 잔여 142억원 10개월 내 집행 필요", "amount": "월평균 14.2억원"},
        {"priority": "🔴 긴급", "content": "OASIS SPOT 공사 착공 지연 (집행률 0.4%)",             "amount": "35억원"},
        {"priority": "🟠 높음", "content": "서비스 인프라 계약 체결  - 선급금 지급",     "amount": "45.33억원"},
        {"priority": "🟠 높음", "content": "SDDC Platform 서버실 일정 조정 필요 (현 26.2% 집행)",  "amount": "27억원"},
        {"priority": "🟠 높음", "content": "여비 초과집행 (191.4%) - 비목 간 전용 또는 실시계획 변경 필요", "amount": "-"},
        {"priority": "🟡 주의", "content": "DRT 차량 발주 설계 지연 (연구개발비 미집행)",            "amount": "10억원"},
        {"priority": "🟡 주의", "content": "감리용역 업체선정 지연",                                "amount": "1.6억원"},
        {"priority": "🟡 주의", "content": "부스제작비 초과집행 (184.1%) 정리 필요",                "amount": "-"},
    ]

def _use_default_data(data):
    data["budget"] = {
        "total":     240e8,
        "executed":   98e8,
        "remaining": 142e8,
        "exec_rate":  40.8,
        "categories": [
            {"name": "인건비",      "budget": 19.0e8, "executed": 18.3e8, "rate":  96.1, "note": "정규직+계약직"},
            {"name": "운영비",      "budget":  7.5e8, "executed":  4.3e8, "rate":  57.0, "note": "부스제작비 초과"},
            {"name": "여비",        "budget":  0.4e8, "executed":  0.8e8, "rate": 191.4, "note": "⚠️ 초과집행"},
            {"name": "연구개발비",  "budget": 10.0e8, "executed":  0,     "rate":   0.0, "note": "DRT 미착수"},
            {"name": "유형자산",    "budget":  0.2e8, "executed":  0.2e8, "rate":  82.1, "note": "이노베이션센터"},
            {"name": "무형자산(SW)","budget": 90.5e8, "executed": 38.3e8, "rate":  42.3, "note": "6개 플랫폼"},
            {"name": "건설비",      "budget": 99.4e8, "executed": 23.2e8, "rate":  23.4, "note": "7개 시설"},
            {"name": "사업비배분",  "budget": 13.0e8, "executed": 13.0e8, "rate": 100.0, "note": "✅ 교부완료"},
        ],
    }
    data["projects"] = _default_projects()
    data["issues"]   = _default_issues()
    data["timeline"] = [
        {"date": "02/10", "type": "제출",   "content": "25년 4분기보고서 및 연간보고서 제출",     "status": "✅ 완료"},
        {"date": "02/10", "type": "공문",   "content": "실시계획 변경 승인 요청 공문 제출",       "status": "✅ 완료"},
        {"date": "02/11", "type": "회의",   "content": "아산시 스마트시티 사업 운영방안 회의",    "status": "✅ 완료"},
        {"date": "02/11", "type": "협의",   "content": "유무선인프라 구축 계약 연장 협의",        "status": "🔄 진행중"},
        {"date": "02/12", "type": "동기화", "content": "Slack → Notion 전체 동기화",             "status": "✅ 완료"},
        {"date": "02/28", "type": "마감",   "content": "2월 월간 추진실적 보고",                 "status": "📅 예정"},
    ]


# ──────────────────────────────────────────────
# HTML 생성
# ──────────────────────────────────────────────
def fmt_uk(val):
    """억원 단위 표시"""
    val = float(val or 0)
    if val >= 1e8:
        return f"{val/1e8:.1f}억원"
    if val >= 1e4:
        return f"{val/1e4:.0f}만원"
    return f"{int(val):,}원"

def rate_color(rate):
    r = float(rate or 0)
    if r > 100:  return "#ef4444"
    if r == 0:   return "#4a5568"
    if r < 30:   return "#f59e0b"
    return "#2e80e8"

def status_class(status):
    s = str(status)
    if "완료" in s:  return "s-done"
    if "진행" in s:  return "s-progress"
    if "대기" in s:  return "s-wait"
    if "신설" in s:  return "s-new"
    return "s-default"

def issue_class(priority):
    p = str(priority)
    if "긴급" in p: return "pri-urgent"
    if "높음" in p: return "pri-high"
    return "pri-normal"

def safe_min(v, mx=100):
    return min(float(v or 0), mx)


def generate_html(d):
    meta = d["meta"]
    dday = d["dday"]
    budget = d["budget"]
    projects = d["projects"]
    issues = d["issues"]
    timeline = d["timeline"]

    # KPI 값
    total_proj = len(projects)
    done_count = sum(1 for p in projects if "완료" in p.get("status",""))
    prog_count = sum(1 for p in projects if "진행" in p.get("status",""))
    wait_count = sum(1 for p in projects if "대기" in p.get("status",""))
    new_count  = sum(1 for p in projects if "신설" in p.get("status",""))

    overall_progress = round(sum(p.get("rate",0) for p in projects) / len(projects), 1) if projects else 0

    urgent = sum(1 for i in issues if "긴급" in i.get("priority",""))
    high   = sum(1 for i in issues if "높음" in i.get("priority",""))

    # 예산 카테고리 행
    budget_rows = ""
    for c in budget.get("categories", []):
        r = float(c.get("rate", 0))
        w = min(r, 100)
        col = rate_color(r)
        over = " ⚠️ 초과" if r > 100 else ""
        budget_rows += f"""
        <div class="budget-item">
          <div class="bh">
            <span class="bn">{c['name']}</span>
            <span class="bv" style="color:{col}">{fmt_uk(c['executed'])} / {fmt_uk(c['budget'])}
              &nbsp;<b>{r:.1f}%{over}</b>
            </span>
          </div>
          <div class="bbar"><div style="width:{w}%;background:{col}"></div></div>
          <div class="bnote">{c.get('note','')}</div>
        </div>"""

    # 단위사업 행
    proj_rows = ""
    for p in projects:
        r = float(p.get("rate",0))
        sc = status_class(p.get("status",""))
        proj_rows += f"""
        <div class="proj-item">
          <span class="sbadge {sc}">{p['status']}</span>
          <span class="pname">{p['name']}</span>
          <div class="pmini"><div style="width:{min(r,100)}%"></div></div>
          <span class="prate">{r:.1f}%</span>
        </div>"""

    # 이슈 행
    issue_rows = ""
    for i in issues:
        pc = issue_class(i.get("priority",""))
        amt = i.get("amount","")
        issue_rows += f"""
        <tr>
          <td class="ic {pc}">{i.get('priority','')}</td>
          <td class="itxt">{i.get('content','')}</td>
          <td class="iamt">{amt}</td>
        </tr>"""

    # 일정 행
    tl_rows = ""
    for t in timeline[:8]:
        status = t.get("status","")
        sc = "✅" if "완료" in status else ("🔄" if "진행" in status else "📅")
        tl_rows += f"""
        <div class="tl-item">
          <span class="tldate">{t.get('date','')}</span>
          <span class="tltype">{t.get('type','')}</span>
          <span class="tlcontent">{t.get('content','')}</span>
          <span class="tlstatus">{sc}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>아산시 강소형 스마트시티 통합 포털</title>
<style>
:root{{
  --bg:#0f1623;--card:#1a2540;--border:#2a3a5a;
  --text:#e2e8f0;--muted:#8fa3c0;
  --accent:#2e80e8;--success:#22c55e;--warn:#f59e0b;--danger:#ef4444;
  --primary:#1a3a6b;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Malgun Gothic','맑은 고딕',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;font-size:14px}}

/* 헤더 */
header{{background:linear-gradient(135deg,var(--primary),#0d2444);padding:16px 28px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--accent);flex-wrap:wrap;gap:10px}}
.htitle{{font-size:1.28rem;font-weight:700}}
.hsub{{font-size:.76rem;color:var(--muted);margin-top:3px}}
.hright{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.badge{{background:rgba(46,128,232,.18);border:1px solid var(--accent);border-radius:20px;padding:3px 12px;font-size:.72rem;color:var(--accent)}}
.updated{{font-size:.71rem;color:var(--muted)}}
.rbtn{{background:var(--accent);color:#fff;border:none;border-radius:6px;padding:5px 14px;font-size:.76rem;cursor:pointer;font-family:inherit}}
.rbtn:hover{{background:#1a60c0}}

/* 레이아웃 */
.container{{max-width:1400px;margin:0 auto;padding:20px 16px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px}}
@media(max-width:1000px){{.grid4{{grid-template-columns:repeat(2,1fr)}}.grid2{{grid-template-columns:1fr}}}}
@media(max-width:600px){{.grid4{{grid-template-columns:1fr}}}}

/* 카드 */
.card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px}}
.ctitle{{font-size:.86rem;font-weight:600;color:var(--accent);margin-bottom:14px;display:flex;align-items:center;gap:7px}}
.csub{{font-size:.70rem;color:var(--muted);margin-left:auto;font-weight:400}}

/* KPI 카드 */
.kpi-val{{font-size:2rem;font-weight:700;margin:8px 0 4px}}
.kpi-sub{{font-size:.73rem;color:var(--muted);line-height:1.4}}
.kbar{{height:5px;background:var(--border);border-radius:3px;overflow:hidden;margin-top:10px}}
.kbar div{{height:100%;border-radius:3px;transition:width 1s ease}}

/* 예산 */
.budget-item{{margin-bottom:13px}}
.bh{{display:flex;justify-content:space-between;align-items:baseline;font-size:.79rem;margin-bottom:5px;gap:8px}}
.bn{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bv{{white-space:nowrap;font-size:.75rem}}
.bbar{{height:6px;background:var(--border);border-radius:3px;overflow:hidden}}
.bbar div{{height:100%;border-radius:3px}}
.bnote{{font-size:.68rem;color:var(--muted);margin-top:2px}}

/* 프로젝트 */
.proj-item{{display:flex;align-items:center;gap:9px;padding:7px 0;border-bottom:1px solid var(--border);font-size:.79rem}}
.proj-item:last-child{{border-bottom:none}}
.sbadge{{padding:2px 9px;border-radius:10px;font-size:.69rem;font-weight:600;white-space:nowrap}}
.s-done{{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid #22c55e44}}
.s-progress{{background:rgba(46,128,232,.15);color:#2e80e8;border:1px solid #2e80e844}}
.s-wait{{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b44}}
.s-new{{background:rgba(168,85,247,.15);color:#c084fc;border:1px solid #c084fc44}}
.s-default{{background:rgba(143,163,192,.1);color:var(--muted);border:1px solid #8fa3c044}}
.pname{{flex:2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}}
.pmini{{flex:1;height:5px;background:var(--border);border-radius:3px;overflow:hidden;min-width:40px}}
.pmini div{{height:100%;background:var(--accent);border-radius:3px}}
.prate{{font-size:.72rem;color:var(--muted);width:38px;text-align:right}}

/* 이슈 */
.issue-tbl{{width:100%;border-collapse:collapse;font-size:.79rem}}
.issue-tbl th{{text-align:left;color:var(--muted);font-size:.70rem;font-weight:500;padding:5px 7px;border-bottom:1px solid var(--border)}}
.issue-tbl td{{padding:7px 7px;border-bottom:1px solid var(--border);vertical-align:top}}
.issue-tbl tr:last-child td{{border-bottom:none}}
.ic{{white-space:nowrap;font-weight:600;width:70px}}
.pri-urgent{{color:#ef4444}}
.pri-high{{color:#f59e0b}}
.pri-normal{{color:var(--muted)}}
.itxt{{line-height:1.45}}
.iamt{{white-space:nowrap;color:var(--muted);font-size:.72rem}}

/* 타임라인 */
.tl-bar-wrap{{background:var(--border);height:18px;border-radius:9px;overflow:hidden;margin:11px 0 5px}}
.tl-bar-fill{{height:100%;background:linear-gradient(90deg,var(--accent),#7c3aed);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:.69rem;font-weight:600;color:#fff;transition:width 1.2s ease;min-width:50px}}
.tl-label{{display:flex;justify-content:space-between;font-size:.71rem;color:var(--muted);margin-bottom:16px}}

/* 일정 */
.tl-item{{display:flex;align-items:flex-start;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:.78rem}}
.tl-item:last-child{{border-bottom:none}}
.tldate{{color:var(--accent);width:32px;flex-shrink:0;font-weight:600}}
.tltype{{background:rgba(46,128,232,.1);color:#90cdf4;border-radius:8px;padding:1px 7px;font-size:.68rem;flex-shrink:0}}
.tlcontent{{flex:1;color:var(--text);line-height:1.4}}
.tlstatus{{flex-shrink:0}}

/* 링크 */
.link-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}}
.link-btn{{background:rgba(46,128,232,.07);border:1px solid var(--border);border-radius:8px;padding:9px 11px;text-decoration:none;color:var(--text);font-size:.78rem;display:flex;align-items:center;gap:7px;transition:all .2s}}
.link-btn:hover{{background:rgba(46,128,232,.2);border-color:var(--accent)}}

footer{{text-align:center;padding:18px;color:var(--muted);font-size:.71rem;border-top:1px solid var(--border);margin-top:6px}}
</style>
</head>
<body>
<header>
  <div>
    <div class="htitle">🏙️ 아산시 강소형 스마트시티 통합 포털</div>
    <div class="hsub">아산시 | (주)제일엔지니어링 PMO | 호서대 · 충남연구원 · KAIST</div>
  </div>
  <div class="hright">
    <span class="badge">2023.12 ~ 2026.12.31</span>
    <span class="badge">총 240억원</span>
    <span class="updated">🕐 {meta.get('last_updated','')}</span>
    <button class="rbtn" onclick="location.reload()">🔄 새로고침</button>
  </div>
</header>

<div class="container">

<!-- KPI 4개 -->
<div class="grid4">
  <div class="card">
    <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">⏳ D-Day</div>
    <div class="kpi-val" style="color:#f59e0b">{dday['dday_label']}</div>
    <div class="kpi-sub">경과 {dday['elapsed_days']}일 / 전체 {dday['total_days']}일<br>종료: 2026.12.31</div>
    <div class="kbar"><div style="width:{safe_min(dday['elapsed_pct'])}%;background:#7c3aed"></div></div>
  </div>
  <div class="card">
    <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">💰 예산 집행률</div>
    <div class="kpi-val" style="color:#2e80e8">{budget['exec_rate']}%</div>
    <div class="kpi-sub">{fmt_uk(budget['executed'])} / {fmt_uk(budget['total'])}<br>잔액: {fmt_uk(budget['remaining'])}</div>
    <div class="kbar"><div style="width:{safe_min(budget['exec_rate'])}%;background:#2e80e8"></div></div>
  </div>
  <div class="card">
    <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">📊 사업 진도율</div>
    <div class="kpi-val" style="color:#22c55e">{overall_progress}%</div>
    <div class="kpi-sub">완료 {done_count} · 진행 {prog_count} · 대기 {wait_count} · 신설 {new_count}<br>전체 {total_proj}개 사업</div>
    <div class="kbar"><div style="width:{safe_min(overall_progress)}%;background:#22c55e"></div></div>
  </div>
  <div class="card">
    <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">⚠️ 이슈 현황</div>
    <div class="kpi-val" style="color:#e879f9">{len(issues)}건</div>
    <div class="kpi-sub">긴급 {urgent}건 · 높음 {high}건<br>주의 {len(issues)-urgent-high}건</div>
    <div class="kbar"><div style="width:{round(urgent/len(issues)*100) if issues else 0}%;background:#e879f9"></div></div>
  </div>
</div>

<!-- 예산 + 사업현황 -->
<div class="grid2">
  <div class="card">
    <div class="ctitle">💰 비목별 예산 집행 현황 <span class="csub">집행률 {budget['exec_rate']}% | {fmt_uk(budget['executed'])} / {fmt_uk(budget['total'])}</span></div>
    {budget_rows}
  </div>
  <div class="card">
    <div class="ctitle">📋 단위사업별 진행 현황 <span class="csub">총 {total_proj}개 사업</span></div>
    {proj_rows}
  </div>
</div>

<!-- 이슈 + 타임라인/링크 -->
<div class="grid2">
  <div class="card">
    <div class="ctitle">⚠️ 주요 리스크 및 이슈 <span class="csub">전체 {len(issues)}건</span></div>
    <table class="issue-tbl">
      <thead><tr><th>우선순위</th><th>내용</th><th>금액</th></tr></thead>
      <tbody>{issue_rows}</tbody>
    </table>
  </div>

  <div style="display:flex;flex-direction:column;gap:16px">
    <div class="card">
      <div class="ctitle">📅 최근 일정 현황</div>
      {tl_rows}
    </div>
    <div class="card">
      <div class="ctitle">📊 사업기간 진행률</div>
      <div style="display:flex;justify-content:space-between;font-size:.73rem;color:var(--muted)">
        <span>▶ 2023.12.01</span><span>2026.12.31 ◀</span>
      </div>
      <div class="tl-bar-wrap">
        <div class="tl-bar-fill" style="width:{safe_min(dday['elapsed_pct'])}%">{dday['elapsed_pct']}%</div>
      </div>
      <div class="tl-label">
        <span>경과 {dday['elapsed_days']}일</span>
        <span>잔여 {dday['remain_days']}일</span>
      </div>
      <div class="ctitle">🔗 관련 시스템 바로가기</div>
      <div class="link-grid">
        <a class="link-btn" href="https://www.notion.so/21650aa9577d80dc8278e0187c54677f" target="_blank">📝 Notion DB</a>
        <a class="link-btn" href="https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/" target="_blank">💰 예산관리</a>
        <a class="link-btn" href="https://leesungho-ai.github.io/Asan-asset-management/" target="_blank">🏗️ 자산관리</a>
        <a class="link-btn" href="https://leesungho-ai.github.io/Asan-HR-Management-Portal/" target="_blank">👤 인력관리</a>
        <a class="link-btn" href="https://leesungho-ai.github.io/Asan-Smartcity-WBS/" target="_blank">📊 WBS</a>
        <a class="link-btn" href="https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal/actions" target="_blank">⚙️ 동기화 로그</a>
      </div>
    </div>
  </div>
</div>

</div><!-- /container -->

<footer>
  © 2026 아산시 강소형 스마트시티 구축사업 PMO | (주)제일엔지니어링 | Notion API 자동 연동 (매 30분 갱신)
</footer>
</body>
</html>"""
    return html


# ──────────────────────────────────────────────
# 실행
# ──────────────────────────────────────────────
def main():
    print("🚀 대시보드 생성 시작")
    data = get_dashboard_data()
    
    # 스냅샷 저장
    os.makedirs("data", exist_ok=True)
    with open("data/snapshot.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print("✅ data/snapshot.json 저장 완료")

    # HTML 생성
    html = generate_html(data)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ index.html 생성 완료")
    
    # 요약 출력
    print(f"\n📊 대시보드 요약:")
    print(f"   D-Day: {data['dday']['dday_label']}")
    print(f"   예산 집행률: {data['budget']['exec_rate']}%")
    print(f"   단위사업: {len(data['projects'])}개")
    print(f"   이슈: {len(data['issues'])}건")
    print(f"   업데이트: {data['meta']['last_updated']}")

if __name__ == "__main__":
    main()
