#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아산시 강소형 스마트시티 - Notion → dashboard.json 자동 동기화
GitHub Actions에서 스케줄 실행 (매 30분)
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────
# 환경변수 (GitHub Secrets에서 주입)
# ─────────────────────────────────────────────
NOTION_TOKEN = os.environ["NOTION_TOKEN"]

# ── Notion DB IDs (각 DB 공유 링크에서 추출) ──
DB_BUDGET    = os.environ.get("DB_BUDGET",    "")   # 예산관리 DB
DB_TASKS     = os.environ.get("DB_TASKS",     "")   # 업무현황 DB
DB_MILESTONES= os.environ.get("DB_MILESTONES","")   # 마일스톤/사업항목 DB

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

KST = timezone(timedelta(hours=9))

# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def query_db(db_id, filter_body=None, page_size=100):
    """Notion DB 전체 페이지 쿼리 (페이지네이션 포함)"""
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    results = []
    has_more = True
    start_cursor = None

    while has_more:
        body = {"page_size": page_size}
        if filter_body:
            body["filter"] = filter_body
        if start_cursor:
            body["start_cursor"] = start_cursor

        resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return results


def get_prop(page, name, prop_type="rich_text"):
    """페이지 속성 안전 추출"""
    props = page.get("properties", {})
    prop = props.get(name, {})
    pt = prop.get("type", "")

    if pt == "title":
        items = prop.get("title", [])
        return items[0]["plain_text"] if items else ""
    if pt == "rich_text":
        items = prop.get("rich_text", [])
        return items[0]["plain_text"] if items else ""
    if pt == "number":
        return prop.get("number") or 0
    if pt == "select":
        sel = prop.get("select")
        return sel["name"] if sel else ""
    if pt == "multi_select":
        return [s["name"] for s in prop.get("multi_select", [])]
    if pt == "date":
        d = prop.get("date")
        return d["start"] if d else ""
    if pt == "checkbox":
        return prop.get("checkbox", False)
    if pt == "formula":
        f = prop.get("formula", {})
        ft = f.get("type", "")
        return f.get(ft, 0)
    if pt == "status":
        s = prop.get("status")
        return s["name"] if s else ""
    if pt == "people":
        people = prop.get("people", [])
        return [p.get("name","") for p in people]
    return ""


# ─────────────────────────────────────────────
# 1) 예산 데이터 파싱
# ─────────────────────────────────────────────
def fetch_budget():
    """예산관리 DB → 요약 구조 반환"""
    if not DB_BUDGET:
        return _default_budget()

    try:
        pages = query_db(DB_BUDGET)
    except Exception as e:
        print(f"[WARN] 예산 DB 조회 실패: {e}")
        return _default_budget()

    total_budget    = 0
    total_executed  = 0
    categories      = []

    for p in pages:
        cat_name    = get_prop(p, "사업항목") or get_prop(p, "Name") or get_prop(p, "항목")
        budget_amt  = get_prop(p, "예산액") or get_prop(p, "계획금액") or 0
        exec_amt    = get_prop(p, "집행액") or get_prop(p, "집행금액") or 0
        status      = get_prop(p, "상태") or get_prop(p, "Status") or ""

        if not cat_name:
            continue

        total_budget   += budget_amt
        total_executed += exec_amt
        rate = round((exec_amt / budget_amt * 100), 1) if budget_amt > 0 else 0

        categories.append({
            "name": cat_name,
            "budget": budget_amt,
            "executed": exec_amt,
            "rate": rate,
            "status": status,
        })

    exec_rate = round((total_executed / total_budget * 100), 1) if total_budget > 0 else 0

    return {
        "total_budget": total_budget,
        "total_executed": total_executed,
        "execution_rate": exec_rate,
        "remaining": total_budget - total_executed,
        "categories": categories,
    }


def _default_budget():
    return {
        "total_budget": 24000000000,
        "total_executed": 9800000000,
        "execution_rate": 40.8,
        "remaining": 14200000000,
        "categories": [],
    }


# ─────────────────────────────────────────────
# 2) 사업현황(마일스톤) 파싱
# ─────────────────────────────────────────────
def fetch_projects():
    """마일스톤/사업항목 DB → 사업 목록"""
    if not DB_MILESTONES:
        return _default_projects()

    try:
        pages = query_db(DB_MILESTONES)
    except Exception as e:
        print(f"[WARN] 사업현황 DB 조회 실패: {e}")
        return _default_projects()

    projects = []
    total_progress = 0

    for p in pages:
        name     = get_prop(p, "Name") or get_prop(p, "사업명") or get_prop(p, "항목명")
        status   = get_prop(p, "Status") or get_prop(p, "상태") or get_prop(p, "진행상태")
        progress = get_prop(p, "진도율") or get_prop(p, "Progress") or 0
        zone     = get_prop(p, "구역") or get_prop(p, "Zone") or ""
        manager  = get_prop(p, "담당자") or ""
        due_date = get_prop(p, "완료예정일") or get_prop(p, "Due Date") or ""

        if not name:
            continue

        # progress가 0~1 사이 소수점이면 100 곱하기
        if isinstance(progress, float) and progress <= 1.0 and progress > 0:
            progress = round(progress * 100, 1)

        total_progress += float(progress)
        projects.append({
            "name": name,
            "status": status,
            "progress": float(progress),
            "zone": zone,
            "manager": manager if isinstance(manager, str) else (manager[0] if manager else ""),
            "due_date": due_date,
        })

    avg_progress = round(total_progress / len(projects), 1) if projects else 0

    # 상태별 카운트
    status_count = {}
    for prj in projects:
        s = prj["status"]
        status_count[s] = status_count.get(s, 0) + 1

    return {
        "overall_progress": avg_progress,
        "total_count": len(projects),
        "status_count": status_count,
        "items": projects,
    }


def _default_projects():
    return {
        "overall_progress": 42.5,
        "total_count": 9,
        "status_count": {"완료": 2, "진행중": 4, "대기": 3},
        "items": [],
    }


# ─────────────────────────────────────────────
# 3) 업무 현황 파싱
# ─────────────────────────────────────────────
def fetch_tasks():
    """업무현황 DB → 최근 업무 목록"""
    if not DB_TASKS:
        return {"total": 0, "done": 0, "in_progress": 0, "pending": 0, "recent": []}

    try:
        pages = query_db(DB_TASKS)
    except Exception as e:
        print(f"[WARN] 업무 DB 조회 실패: {e}")
        return {"total": 0, "done": 0, "in_progress": 0, "pending": 0, "recent": []}

    tasks = []
    done = in_progress = pending = 0

    for p in pages:
        name     = get_prop(p, "Name") or get_prop(p, "업무명") or get_prop(p, "제목")
        status   = get_prop(p, "Status") or get_prop(p, "상태") or ""
        assignee = get_prop(p, "담당자") or ""
        due      = get_prop(p, "기한") or get_prop(p, "Due Date") or ""
        priority = get_prop(p, "우선순위") or get_prop(p, "Priority") or ""

        if not name:
            continue

        s_lower = status.lower()
        if "완료" in s_lower or "done" in s_lower or "complete" in s_lower:
            done += 1
        elif "진행" in s_lower or "progress" in s_lower or "in" in s_lower:
            in_progress += 1
        else:
            pending += 1

        tasks.append({
            "name": name,
            "status": status,
            "assignee": assignee if isinstance(assignee, str) else (assignee[0] if assignee else ""),
            "due": due,
            "priority": priority,
        })

    # 최근 10건만
    recent = tasks[:10]

    return {
        "total": len(tasks),
        "done": done,
        "in_progress": in_progress,
        "pending": pending,
        "recent": recent,
    }


# ─────────────────────────────────────────────
# 4) D-Day 계산
# ─────────────────────────────────────────────
def calc_dday():
    now = datetime.now(KST)
    end = datetime(2025, 12, 31, 23, 59, 59, tzinfo=KST)
    delta = (end - now).days
    start = datetime(2023, 12, 1, tzinfo=KST)
    total_days = (end - start).days
    elapsed = (now - start).days
    elapsed_rate = round(elapsed / total_days * 100, 1)
    return {
        "end_date": "2025-12-31",
        "dday": delta,
        "elapsed_days": elapsed,
        "total_days": total_days,
        "elapsed_rate": elapsed_rate,
    }


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    print(f"[{now_kst}] Notion 동기화 시작...")

    budget   = fetch_budget()
    projects = fetch_projects()
    tasks    = fetch_tasks()
    dday     = calc_dday()

    dashboard = {
        "meta": {
            "project_name": "아산시 강소형 스마트시티 조성사업",
            "last_updated": now_kst,
            "data_source": "Notion API (자동 동기화)",
            "version": "3.0",
        },
        "dday": dday,
        "budget": budget,
        "projects": projects,
        "tasks": tasks,
    }

    # 저장
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "dashboard.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"✅ dashboard.json 생성 완료 ({now_kst})")
    print(f"   예산: {budget['execution_rate']}% 집행")
    print(f"   사업진도: {projects['overall_progress']}%")
    print(f"   업무: 전체 {tasks['total']}건 / 완료 {tasks['done']}건")


if __name__ == "__main__":
    main()
