#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아산시 강소형 스마트시티 대시보드 자동 생성기
────────────────────────────────────────────
동작 원리:
  1. GitHub Actions (30분 주기 자동 실행)
  2. Notion API → 최신 데이터 파싱
  3. index.html 완전 재생성 (데이터 내장)
  4. git commit & push → GitHub Pages 자동 반영

CORS 문제 없음 (브라우저가 아닌 서버사이드 Python 실행)
"""

import os, json, re, sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

try:
    import requests
except ImportError:
    os.system("pip install requests --quiet")
    import requests

# ══════════════════════════════════════════
#  설정값
# ══════════════════════════════════════════
NOTION_TOKEN   = os.environ.get("NOTION_TOKEN", "")
BUDGET_PAGE_ID = os.environ.get("NOTION_BUDGET_PAGE_ID",
                                "2e050aa9577d81a8baa0d7decdac9010")

PROJECT_START = date(2023, 12, 1)
PROJECT_END   = date(2026, 12, 31)

KST     = ZoneInfo("Asia/Seoul")
NOW_KST = datetime.now(KST)

HEADERS = {
    "Authorization":  f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type":   "application/json",
}

# ══════════════════════════════════════════
#  기본 데이터 (Notion 2026-03-10 기준 직접 확인값)
#  → Notion API 실패 시 이 값을 사용
# ══════════════════════════════════════════

FALLBACK_SUMMARY = {
    "total": 240.0, "executed": 98.0, "remaining": 142.0,
    "exec_rate": 40.8,
    "national": 49.0, "provincial": 11.8, "municipal": 37.2,
}

FALLBACK_CATS = [
    # name,           budget, executed,  rate,  note
    ("인건비",          19.0,   18.3,    96.1, "정규직+계약직 (2024년)"),
    ("운영비",           7.5,    4.3,    57.0, "부스제작비 초과 184%"),
    ("여비",             0.4,    0.8,   191.4, "⚠️ 초과집행 — 비목 간 전용 필요"),
    ("연구개발비",       10.0,    0.0,     0.0, "DRT 플랫폼 설계 진행중"),
    ("유형자산",          0.2,    0.2,    82.1, "이노베이션센터 PC"),
    ("무형자산(SW)",     90.5,   38.3,    42.3, "6개 플랫폼 개발 진행중"),
    ("건설비",           99.4,   23.2,    23.4, "OASIS SPOT 착공 추진 중"),
    ("사업비배분",       13.0,   13.0,   100.0, "✅ 간접보조 교부완료"),
]

# ★ 서비스 인프라: 예산 45.33억 / 집행 0억(선급금 미집행) / 0%
#   → 한국정보기술 컨소시엄 7~9주차 공정보고 제출완료 (2026-03-09)
FALLBACK_PROJECTS = [
    # num, name,                              budget, executed, rate, status,      note
    (1, "유무선 네트워크 구축",               11.35,   4.15,  36.6, "✅ 완료",   "변경계약·연장 합의서 체결완료 (2/25)"),
    (2, "서비스 인프라 플랫폼",               45.33,   0.00,   0.0, "🔄 진행중", "7~9주차 공정보고 제출완료, 선급금 집행 필요"),
    (3, "이노베이션 센터 구축",               13.00,  11.86,  91.2, "✅ 완료",   "구축완료 (운영중, 음향·조경 마무리)"),
    (4, "디지털 OASIS SPOT",                 35.00,   0.15,   0.4, "🔄 진행중", "부지 확정(도고면 기곡리 296-4), 착공 추진"),
    (5, "SDDC Platform 구축",               27.00,   7.09,  26.2, "🔄 진행중", "서버실 HW·SW 납품 및 설치 진행중"),
    (6, "AI 통합관제 플랫폼",                16.00,   9.29,  58.1, "🔄 진행중", "서비스 인프라 통합 계약, 선급금 집행 필요"),
    (7, "디지털 OASIS 정보관리",             25.00,  10.93,  43.7, "🔄 진행중", "개발 진행중"),
    (8, "DRT 수요응답형 교통",               10.00,   0.00,   0.0, "⏸️ 대기",  "설계 진행중, 1분기 내 발주 목표"),
    (9, "감리용역 (신설)",                    1.60,   0.00,   0.0, "🆕 신설",  "업체선정 준비 중"),
]

FALLBACK_ISSUES = [
    ("🔴 긴급", "#ef4444", "예산 집행률 저조 (40.8%) — 잔여 142억, 1분기 50% 집행 목표",        "142억원"),
    ("🔴 긴급", "#ef4444", "OASIS SPOT 공사 착공 지연 — 부지 확정, 3월 내 착공 필요",           "35억원"),
    ("🟠 높음", "#f59e0b", "서비스 인프라·AI관제 선급금 미집행 — 대형사업 집행 가속화 시급",    "61.33억원"),
    ("🟠 높음", "#f59e0b", "SDDC Platform 서버실 납품·설치 일정 준수 필요 (현 26.2% 집행)",     "27억원"),
    ("🟠 높음", "#f59e0b", "여비 초과집행 (191.4%) — 비목 간 전용 또는 실시계획 변경 필요",     "-"),
    ("🟡 주의", "#eab308", "DRT 1분기 발주 미착수 — 연구개발비 전액 미집행",                    "10억원"),
    ("🟡 주의", "#eab308", "감리용역 업체선정 지연",                                            "1.6억원"),
    ("🟡 주의", "#eab308", "유무선 네트워크 세목별 초과집행 지속 — 정산 필요",                  "-"),
]

FALLBACK_TIMELINE = [
    ("03/02", "동기화", "WBS 동기화 179건 업데이트 완료",                     True),
    ("03/05", "데이터", "예산 파일 재업로드 (Slack #플랜예산 — 김주용)",       True),
    ("03/09", "제출",   "유무선 네트워크 2월 공정보고서 일괄 제출 (싸인텔레콤)", True),
    ("03/09", "제출",   "서비스 인프라 7~9주차 공정보고서 제출 완료",           True),
    ("03/10", "제출",   "2026년 2월 관리카드 제출",                            False),
    ("03/31", "마감",   "1분기 예산 집행 점검 (50% 달성 목표)",                None),
]

# ══════════════════════════════════════════
#  Notion API 헬퍼
# ══════════════════════════════════════════

def notion_get(path, params=None):
    url = f"https://api.notion.com/v1/{path}"
    r = requests.get(url, headers=HEADERS, params=params or {}, timeout=20)
    r.raise_for_status()
    return r.json()

def rich_text(arr):
    return "".join(t.get("plain_text", "") for t in (arr or []))

def page_blocks(pid):
    blocks, cursor = [], None
    pid = pid.replace("-", "")
    while True:
        p = {"page_size": 100}
        if cursor:
            p["start_cursor"] = cursor
        data = notion_get(f"blocks/{pid}/children", p)
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return blocks

def table_rows(block_id):
    data = notion_get(f"blocks/{block_id}/children", {"page_size": 100})
    rows = []
    for rb in data.get("results", []):
        cells = rb.get("table_row", {}).get("cells", [])
        rows.append([rich_text(cell) for cell in cells])
    return rows

# ══════════════════════════════════════════
#  파싱 유틸
# ══════════════════════════════════════════

def to_eok(text):
    """'45.33억', '-', '' → float (억원)"""
    s = str(text or "").strip().replace(",", "")
    if s in ("-", "", "0억", "0"):
        return 0.0
    m = re.search(r"([\d.]+)억", s)
    if m:
        return float(m.group(1))
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else 0.0

def to_pct(text):
    """'40.8%', '0%' → float"""
    try:
        return float(str(text or "0").strip().replace("%", ""))
    except:
        return 0.0

def status_icon(s):
    s = str(s)
    if "✅" in s or "완료" in s: return "✅ 완료"
    if "🔄" in s or "진행" in s: return "🔄 진행중"
    if "⏸️" in s or "대기" in s: return "⏸️ 대기"
    if "🆕" in s or "신설" in s: return "🆕 신설"
    return "🔄 진행중"

# ══════════════════════════════════════════
#  Notion 실데이터 수집
# ══════════════════════════════════════════

def fetch_notion():
    print("🔍 Notion API 호출...")
    blocks = page_blocks(BUDGET_PAGE_ID)
    tbls   = [b for b in blocks if b.get("type") == "table"]
    print(f"   블록 {len(blocks)}개 / 테이블 {len(tbls)}개")

    if len(tbls) < 4:
        print("   ⚠️ 테이블 부족 → fallback 사용")
        return None

    # 테이블 인덱스 (Notion 페이지 순서)
    # 0: 추진체계  1: 재원별  2: 비목별  3: 단위사업별
    # 4: 간접보조  5: 2월일정  6: 최근지출

    rows = {}
    for i, tb in enumerate(tbls):
        try:
            rows[i] = table_rows(tb["id"])
        except Exception as e:
            print(f"   ⚠️ 테이블[{i}] 오류: {e}")
            rows[i] = []

    # ── 재원별 요약 (idx 1)
    summary = dict(FALLBACK_SUMMARY)
    for row in rows.get(1, []):
        if len(row) < 4: continue
        lbl = row[0].replace("*", "").strip()
        if "합" in lbl:
            v = to_eok(row[3]); r = to_pct(row[4])
            if v > 0: summary["executed"]    = v
            if r > 0: summary["exec_rate"]   = r
        elif "국비" in lbl:
            v = to_eok(row[3])
            if v > 0: summary["national"]    = v
        elif "도비" in lbl:
            v = to_eok(row[3])
            if v > 0: summary["provincial"]  = v
        elif "시비" in lbl:
            v = to_eok(row[3])
            if v > 0: summary["municipal"]   = v
    summary["remaining"] = summary["total"] - summary["executed"]

    # ── 비목별 (idx 2)
    cats = []
    for row in rows.get(2, []):
        if len(row) < 5: continue
        name = row[0].replace("*", "").strip()
        if not name or "비목" in name or "합" in name: continue
        cats.append({
            "name": name,
            "budget":   to_eok(row[1]),
            "executed": to_eok(row[2]),
            "rate":     to_pct(row[4]),
            "note":     row[5].strip() if len(row) > 5 else "",
        })

    # ── 단위사업별 (idx 3)
    projects = []
    for row in rows.get(3, []):
        if len(row) < 6: continue
        name = row[1].replace("*", "").strip()
        if not name or "사업명" in name: continue
        try:   num = int(row[0].replace("*", "").strip())
        except: num = len(projects) + 1
        projects.append({
            "num":      num,
            "name":     name,
            "budget":   to_eok(row[2]),
            "executed": to_eok(row[3]),   # "-" → 0.0
            "rate":     to_pct(row[4]),
            "status":   status_icon(row[5]),
            "note":     row[5].strip(),
        })

    # ── 2월 일정 (idx 5)
    timeline = []
    for row in rows.get(5, []):
        if len(row) < 4 or "일자" in row[0]: continue
        s = row[3].strip()
        done = True  if ("✅" in s or "완료" in s) else \
               False if ("🔄" in s or "진행" in s) else None
        timeline.append((row[0], row[1], row[2], done))

    ok_cats  = cats     or None
    ok_proj  = projects or None
    ok_tl    = timeline or None

    if not ok_cats:  print("   ⚠️ 비목 파싱 실패 → fallback")
    if not ok_proj:  print("   ⚠️ 단위사업 파싱 실패 → fallback")
    if not ok_tl:    print("   ⚠️ 일정 파싱 실패 → fallback")

    print(f"   ✅ 비목 {len(ok_cats or FALLBACK_CATS)}개  "
          f"사업 {len(ok_proj or FALLBACK_PROJECTS)}개  "
          f"일정 {len(ok_tl or FALLBACK_TIMELINE)}개")

    return summary, ok_cats, ok_proj, ok_tl

# ══════════════════════════════════════════
#  데이터 조합
# ══════════════════════════════════════════

def collect():
    summary  = FALLBACK_SUMMARY
    cats_raw = FALLBACK_CATS       # list of tuples
    proj_raw = FALLBACK_PROJECTS   # list of tuples
    tl_raw   = FALLBACK_TIMELINE   # list of tuples
    source   = "기본 데이터 (Notion 2026-03-10)"

    if NOTION_TOKEN:
        try:
            result = fetch_notion()
            if result:
                n_sum, n_cats, n_proj, n_tl = result
                summary = n_sum
                source  = "Notion API 실시간"

                # API 파싱 결과를 dict 형태로 변환 (이미 dict)
                cats_raw = [(c["name"], c["budget"], c["executed"],
                             c["rate"], c["note"]) for c in n_cats] \
                           if n_cats else FALLBACK_CATS

                proj_raw = [(p["num"], p["name"], p["budget"],
                             p["executed"], p["rate"],
                             p["status"], p["note"]) for p in n_proj] \
                           if n_proj else FALLBACK_PROJECTS

                tl_raw   = n_tl if n_tl else FALLBACK_TIMELINE
        except Exception as e:
            print(f"⚠️ Notion 오류: {e} → fallback 사용")
    else:
        print("⚠️ NOTION_TOKEN 없음 → fallback 사용")

    today        = date.today()
    total_days   = (PROJECT_END - PROJECT_START).days
    elapsed_days = (today - PROJECT_START).days
    remain_days  = (PROJECT_END - today).days
    elapsed_pct  = round(elapsed_days / total_days * 100, 1)
    dday         = f"D-{remain_days}" if remain_days >= 0 else f"D+{abs(remain_days)}"

    # tuple → dict 통일
    def cat_dict(t):
        return {"name":t[0],"budget":t[1],"executed":t[2],"rate":t[3],"note":t[4]}

    def proj_dict(t):
        return {"num":t[0],"name":t[1],"budget":t[2],
                "executed":t[3],"rate":t[4],"status":t[5],"note":t[6]}

    def tl_dict(t):
        return {"date":t[0],"type":t[1],"content":t[2],"done":t[3]}

    def issue_dict(t):
        return {"level":t[0],"color":t[1],"content":t[2],"amount":t[3]}

    return {
        "meta":    {"updated": NOW_KST.strftime("%Y-%m-%d %H:%M KST"), "source": source},
        "dday":    {"label": dday, "total": total_days, "elapsed": elapsed_days,
                    "remain": remain_days, "pct": elapsed_pct},
        "summary": summary,
        "cats":    [cat_dict(c) if isinstance(c, tuple) else c for c in cats_raw],
        "projects":[proj_dict(p) if isinstance(p, tuple) else p for p in proj_raw],
        "issues":  [issue_dict(i) for i in FALLBACK_ISSUES],
        "timeline":[tl_dict(t)  if isinstance(t, tuple) else t for t in tl_raw],
    }

# ══════════════════════════════════════════
#  HTML 렌더링
# ══════════════════════════════════════════

def rate_color(r):
    r = float(r or 0)
    if r > 100: return "#ef4444"
    if r == 0:  return "#4b5568"
    if r < 30:  return "#f59e0b"
    return "#2e80e8"

def status_cls(s):
    if "완료" in s: return "s-done"
    if "진행" in s: return "s-prog"
    if "대기" in s: return "s-wait"
    if "신설" in s: return "s-new"
    return "s-etc"

def html_cats(cats):
    h = ""
    for c in cats:
        r   = float(c["rate"])
        col = rate_color(r)
        tag = " ⚠️초과" if r > 100 else ""
        h += f"""
      <div class="bi">
        <div class="bih">
          <span class="bin">{c['name']}</span>
          <span class="bir" style="color:{col}">{r:.1f}%{tag}</span>
        </div>
        <div class="bb"><div style="width:{min(r,100):.1f}%;background:{col}"></div></div>
        <div class="bd">{c['executed']:.1f}억 / {c['budget']:.1f}억원 &nbsp;·&nbsp; {c.get('note','')}</div>
      </div>"""
    return h

def html_projects(projs):
    h = ""
    for p in projs:
        r   = float(p["rate"])
        col = rate_color(r)
        h += f"""
      <div class="pi">
        <span class="pn">{p['num']:02d}</span>
        <span class="sbadge {status_cls(p['status'])}">{p['status']}</span>
        <span class="pm" title="{p['note']}">{p['name']}</span>
        <div class="pb"><div style="width:{min(r,100):.1f}%;background:{col}"></div></div>
        <span class="pr" style="color:{col}">{r:.1f}%</span>
      </div>"""
    return h

def html_issues(issues):
    h = ""
    for i in issues:
        h += f"""
        <tr>
          <td style="color:{i['color']};font-weight:700;white-space:nowrap">{i['level']}</td>
          <td>{i['content']}</td>
          <td style="color:#8fa3c0;white-space:nowrap;font-size:.72rem">{i['amount']}</td>
        </tr>"""
    return h

def html_timeline(tl):
    h = ""
    for t in tl[:8]:
        icon = "✅" if t["done"] is True else "🔄" if t["done"] is False else "📅"
        h += f"""
      <div class="tli">
        <span class="tld">{t['date']}</span>
        <span class="tlt">{t['type']}</span>
        <span class="tlc">{t['content']}</span>
        <span>{icon}</span>
      </div>"""
    return h

CSS = """
:root{--bg:#0f1623;--card:#1a2540;--bdr:#2a3a5a;--txt:#e2e8f0;
      --muted:#8fa3c0;--acc:#2e80e8;--ok:#22c55e;--pri:#1a3a6b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Malgun Gothic','맑은 고딕',sans-serif;
     background:var(--bg);color:var(--txt);font-size:14px}
header{background:linear-gradient(135deg,var(--pri),#0d2444);
  padding:14px 26px;display:flex;align-items:center;
  justify-content:space-between;border-bottom:2px solid var(--acc);
  flex-wrap:wrap;gap:8px}
.ht{font-size:1.25rem;font-weight:700}
.hs{font-size:.74rem;color:var(--muted);margin-top:3px}
.hr{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.badge{background:rgba(46,128,232,.18);border:1px solid var(--acc);
  border-radius:20px;padding:3px 12px;font-size:.71rem;color:var(--acc)}
.upd{font-size:.70rem;color:var(--muted)}
.src{font-size:.68rem;color:#22c55e;border:1px solid #22c55e55;
  border-radius:10px;padding:2px 8px}
.wrap{max-width:1400px;margin:0 auto;padding:18px 14px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-bottom:18px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:16px}
.gcol{display:flex;flex-direction:column;gap:15px}
@media(max-width:1000px){.g4{grid-template-columns:repeat(2,1fr)}.g2{grid-template-columns:1fr}}
@media(max-width:580px){.g4{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:17px}
.ct{font-size:.85rem;font-weight:600;color:var(--acc);margin-bottom:13px;
  display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.cs{font-size:.69rem;color:var(--muted);margin-left:auto;font-weight:400}
.kl{font-size:.70rem;color:var(--muted);text-transform:uppercase;
  letter-spacing:.05em;margin-bottom:5px}
.kv{font-size:1.9rem;font-weight:700;margin-bottom:3px}
.ks{font-size:.72rem;color:var(--muted);line-height:1.5}
.kb{height:5px;background:var(--bdr);border-radius:3px;overflow:hidden;margin-top:9px}
.kb div{height:100%;border-radius:3px}
.fg{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-bottom:15px}
.fi{background:rgba(46,128,232,.07);border:1px solid var(--bdr);
  border-radius:8px;padding:9px 11px;text-align:center}
.fil{font-size:.69rem;color:var(--muted);margin-bottom:3px}
.fiv{font-size:1.05rem;font-weight:700;color:var(--acc)}
.fis{font-size:.67rem;color:var(--muted)}
.bi{margin-bottom:12px}
.bih{display:flex;justify-content:space-between;align-items:baseline;
  margin-bottom:4px;gap:8px}
.bin{font-size:.80rem;font-weight:500;flex:1;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.bir{font-size:.78rem;font-weight:700;white-space:nowrap}
.bb{height:7px;background:var(--bdr);border-radius:4px;overflow:hidden}
.bb div{height:100%;border-radius:4px}
.bd{font-size:.68rem;color:var(--muted);margin-top:3px}
.pi{display:flex;align-items:center;gap:8px;padding:7px 0;
  border-bottom:1px solid var(--bdr);font-size:.79rem}
.pi:last-child{border-bottom:none}
.pn{font-size:.68rem;color:var(--muted);width:18px;flex-shrink:0}
.sbadge{padding:2px 8px;border-radius:10px;font-size:.68rem;
  font-weight:600;white-space:nowrap;flex-shrink:0}
.s-done{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid #22c55e44}
.s-prog{background:rgba(46,128,232,.15);color:#2e80e8;border:1px solid #2e80e844}
.s-wait{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid #f59e0b44}
.s-new{background:rgba(168,85,247,.15);color:#c084fc;border:1px solid #c084fc44}
.s-etc{background:rgba(143,163,192,.1);color:var(--muted);border:1px solid #8fa3c044}
.pm{flex:2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.pb{flex:1;height:6px;background:var(--bdr);border-radius:3px;
  overflow:hidden;min-width:45px}
.pb div{height:100%;border-radius:3px}
.pr{font-size:.72rem;font-weight:600;width:38px;text-align:right;flex-shrink:0}
.itbl{width:100%;border-collapse:collapse;font-size:.78rem}
.itbl th{text-align:left;color:var(--muted);font-size:.69rem;font-weight:500;
  padding:5px 7px;border-bottom:1px solid var(--bdr)}
.itbl td{padding:7px 7px;border-bottom:1px solid var(--bdr);
  vertical-align:top;line-height:1.45}
.itbl tr:last-child td{border-bottom:none}
.tlbar{background:var(--bdr);height:19px;border-radius:10px;
  overflow:hidden;margin:9px 0 4px}
.tlf{height:100%;background:linear-gradient(90deg,#2e80e8,#7c3aed);
  border-radius:10px;display:flex;align-items:center;justify-content:center;
  font-size:.69rem;font-weight:700;color:#fff;min-width:52px}
.tls{display:flex;justify-content:space-between;font-size:.70rem;
  color:var(--muted);margin-bottom:14px}
.tli{display:flex;align-items:flex-start;gap:7px;padding:6px 0;
  border-bottom:1px solid var(--bdr);font-size:.77rem}
.tli:last-child{border-bottom:none}
.tld{color:#2e80e8;font-weight:700;width:32px;flex-shrink:0}
.tlt{background:rgba(46,128,232,.12);color:#90cdf4;border-radius:8px;
  padding:1px 6px;font-size:.67rem;flex-shrink:0;margin-top:1px}
.tlc{flex:1;line-height:1.4}
.lg{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:7px}
.lb{background:rgba(46,128,232,.07);border:1px solid var(--bdr);
  border-radius:8px;padding:9px 10px;text-decoration:none;color:var(--txt);
  font-size:.77rem;display:flex;align-items:center;gap:6px;transition:all .2s}
.lb:hover{background:rgba(46,128,232,.22);border-color:var(--acc)}
footer{text-align:center;padding:16px;color:var(--muted);font-size:.70rem;
  border-top:1px solid var(--bdr);margin-top:4px}
"""

def build_html(d):
    m  = d["meta"];  dd = d["dday"];  s = d["summary"]
    c  = d["cats"];  pj = d["projects"]
    iss= d["issues"]; tl = d["timeline"]

    done_c = sum(1 for p in pj if "완료" in p["status"])
    prog_c = sum(1 for p in pj if "진행" in p["status"])
    wait_c = sum(1 for p in pj if "대기" in p["status"])
    new_c  = sum(1 for p in pj if "신설" in p["status"])
    ov     = round(sum(p["rate"] for p in pj)/len(pj), 1) if pj else 0
    urg    = sum(1 for i in iss if "긴급" in i["level"])
    hi     = sum(1 for i in iss if "높음" in i["level"])

    ep = min(dd["pct"], 100)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>아산시 강소형 스마트시티 통합 포털</title>
<style>{CSS}</style>
</head>
<body>

<header>
  <div>
    <div class="ht">🏙️ 아산시 강소형 스마트시티 통합 포털</div>
    <div class="hs">아산시 시행 &nbsp;|&nbsp; (주)제일엔지니어링 PMO &nbsp;|&nbsp; 호서대 · 충남연구원 · KAIST</div>
  </div>
  <div class="hr">
    <span class="badge">2023.12 ~ 2026.12.31</span>
    <span class="badge">총 240억원</span>
    <span class="upd">🕐 {m['updated']}</span>
    <span class="src">📡 {m['source']}</span>
  </div>
</header>

<div class="wrap">

<!-- ── KPI 4개 ── -->
<div class="g4">
  <div class="card">
    <div class="kl">⏳ D-DAY</div>
    <div class="kv" style="color:#f59e0b">{dd['label']}</div>
    <div class="ks">경과 {dd['elapsed']}일 / 전체 {dd['total']}일<br>종료: 2026.12.31</div>
    <div class="kb"><div style="width:{ep:.1f}%;background:#7c3aed"></div></div>
  </div>
  <div class="card">
    <div class="kl">💰 예산 집행률</div>
    <div class="kv" style="color:#2e80e8">{s['exec_rate']}%</div>
    <div class="ks">{s['executed']:.1f}억원 / {s['total']:.0f}억원<br>잔액: {s['remaining']:.1f}억원</div>
    <div class="kb"><div style="width:{s['exec_rate']:.1f}%;background:#2e80e8"></div></div>
  </div>
  <div class="card">
    <div class="kl">📊 사업 진도율</div>
    <div class="kv" style="color:#22c55e">{ov}%</div>
    <div class="ks">완료 {done_c} · 진행 {prog_c} · 대기 {wait_c} · 신설 {new_c}<br>전체 {len(pj)}개 사업</div>
    <div class="kb"><div style="width:{min(ov,100):.1f}%;background:#22c55e"></div></div>
  </div>
  <div class="card">
    <div class="kl">⚠️ 이슈 현황</div>
    <div class="kv" style="color:#e879f9">{len(iss)}건</div>
    <div class="ks">긴급 {urg}건 · 높음 {hi}건 · 주의 {len(iss)-urg-hi}건</div>
    <div class="kb"><div style="width:{round(urg/len(iss)*100) if iss else 0}%;background:#e879f9"></div></div>
  </div>
</div>

<!-- ── 비목별 + 단위사업 ── -->
<div class="g2">
  <div class="card">
    <div class="ct">💰 비목별 예산 집행 현황
      <span class="cs">집행률 {s['exec_rate']}% | {s['executed']:.1f}억 / {s['total']:.0f}억원</span>
    </div>
    <!-- 재원 요약 -->
    <div class="fg">
      <div class="fi">
        <div class="fil">🏛️ 국비 (50%)</div>
        <div class="fiv">{s['national']:.1f}억</div>
        <div class="fis">120억원 중</div>
      </div>
      <div class="fi">
        <div class="fil">🏘️ 도비 (12%)</div>
        <div class="fiv">{s['provincial']:.1f}억</div>
        <div class="fis">28.8억원 중</div>
      </div>
      <div class="fi">
        <div class="fil">🏙️ 시비 (38%)</div>
        <div class="fiv">{s['municipal']:.1f}억</div>
        <div class="fis">91.2억원 중</div>
      </div>
    </div>
    <!-- 비목 막대 -->
    {html_cats(c)}
  </div>

  <div class="card">
    <div class="ct">📋 단위사업별 진행 현황
      <span class="cs">총 {len(pj)}개 사업</span>
    </div>
    {html_projects(pj)}
  </div>
</div>

<!-- ── 이슈 + 일정/링크 ── -->
<div class="g2">
  <div class="card">
    <div class="ct">⚠️ 주요 리스크 및 이슈
      <span class="cs">전체 {len(iss)}건</span>
    </div>
    <table class="itbl">
      <thead><tr><th>우선순위</th><th>내용</th><th>금액</th></tr></thead>
      <tbody>{html_issues(iss)}</tbody>
    </table>
  </div>

  <div class="gcol">
    <div class="card">
      <div class="ct">📅 3월 주요 일정</div>
      {html_timeline(tl)}
    </div>

    <div class="card">
      <div class="ct">📊 사업기간 진행률</div>
      <div style="display:flex;justify-content:space-between;font-size:.71rem;color:var(--muted)">
        <span>▶ 2023.12.01</span><span>2026.12.31 ◀</span>
      </div>
      <div class="tlbar">
        <div class="tlf" style="width:{ep:.1f}%">{dd['pct']}% 경과</div>
      </div>
      <div class="tls">
        <span>경과 {dd['elapsed']}일</span>
        <span>잔여 {dd['remain']}일</span>
      </div>

      <div class="ct" style="margin-bottom:9px">🔗 관련 시스템 바로가기</div>
      <div class="lg">
        <a class="lb" href="https://www.notion.so/21650aa9577d80dc8278e0187c54677f" target="_blank">📝 Notion DB</a>
        <a class="lb" href="https://leesungho-ai.github.io/Asan-Smart-City-Budget-Management-System-BMS-/" target="_blank">💰 예산관리</a>
        <a class="lb" href="https://leesungho-ai.github.io/Asan-asset-management/" target="_blank">🏗️ 자산관리</a>
        <a class="lb" href="https://leesungho-ai.github.io/Asan-HR-Management-Portal/" target="_blank">👤 인력관리</a>
        <a class="lb" href="https://leesungho-ai.github.io/Asan-Smartcity-WBS/" target="_blank">📊 WBS</a>
        <a class="lb" href="https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal/actions" target="_blank">⚙️ Actions</a>
      </div>
    </div>
  </div>
</div>

</div><!-- /wrap -->

<footer>
  © 2026 아산시 강소형 스마트시티 PMO &nbsp;|&nbsp; (주)제일엔지니어링
  &nbsp;|&nbsp; {m['updated']} &nbsp;|&nbsp; GitHub Actions 30분 자동 갱신
</footer>
</body>
</html>"""

# ══════════════════════════════════════════
#  main
# ══════════════════════════════════════════

def main():
    print("=" * 52)
    print("🚀 아산시 스마트시티 대시보드 생성 시작")
    print("=" * 52)

    data = collect()

    # 스냅샷 저장
    os.makedirs("data", exist_ok=True)
    with open("data/snapshot.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print("✅ data/snapshot.json 저장")

    # index.html 생성
    html = build_html(data)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ index.html 생성 ({len(html.encode()):,} bytes)")
    print()
    print(f"   출처    : {data['meta']['source']}")
    print(f"   갱신    : {data['meta']['updated']}")
    print(f"   D-Day   : {data['dday']['label']}")
    print(f"   집행률  : {data['summary']['exec_rate']}%")
    print(f"   비목    : {len(data['cats'])}개")
    print(f"   단위사업: {len(data['projects'])}개")
    print("=" * 52)

if __name__ == "__main__":
    main()
