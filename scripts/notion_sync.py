#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
아산시 강소형 스마트시티 - Notion → dashboard.json 자동 동기화
GitHub Actions 매 30분 스케줄 실행

[DB 연결 정보]
- DB_BUDGET    : efc3526e6e7845d6a48e4ea61021340e  (📊 단위사업별 예산관리)
- DB_MILESTONES: efc3526e6e7845d6a48e4ea61021340e  (동일 DB - 진도율/상태 활용)
- DB_TASKS     : 8e565ba155484d90af86333a1857530b  (📝 회의 및 이슈 관리)
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────
# 환경변수 (GitHub Secrets)
# ─────────────────────────────────────────────
NOTION_TOKEN    = os.environ["NOTION_TOKEN"]
DB_BUDGET       = os.environ.get("DB_BUDGET",     "efc3526e6e7845d6a48e4ea61021340e")
DB_MILESTONES   = os.environ.get("DB_MILESTONES", "efc3526e6e7845d6a48e4ea61021340e")
DB_TASKS        = os.environ.get("DB_TASKS",      "8e565ba155484d90af86333a1857530b")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
KST = timezone(timedelta(hours=9))


# ─────────────────────────────────────────────
# Notion DB 쿼리 (페이지네이션 포함)
# ─────────────────────────────────────────────
def query_db(db_id):
    url     = f"https://api.notion.com/v1/databases/{db_id}/query"
    results = []
    cursor  = None

    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor

        resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return results


# ─────────────────────────────────────────────
# 속성 추출 헬퍼
# ─────────────────────────────────────────────
def prop(page, name):
    """Notion 페이지 속성을 타입에 맞게 안전하게 반환"""
    p = page.get("properties", {}).get(name, {})
    t = p.get("type", "")

    if t == "title":
        items = p.get("title", [])
        return items[0]["plain_text"] if items else ""

    if t == "rich_text":
        items = p.get("rich_text", [])
        return items[0]["plain_text"] if items else ""

    if t == "number":
        return p.get("number") or 0

    if t == "select":
        s = p.get("select")
        return s["name"] if s else ""

    if t == "multi_select":
        return [x["name"] for x in p.get("multi_select", [])]

    if t == "date":
        d = p.get("date")
        return d["start"] if d else ""

    if t == "people":
        people = p.get("people", [])
        return people[0].get("name", "") if people else ""

    if t == "formula":
        f = p.get("formula", {})
        ft = f.get("type", "")
        val = f.get(ft, 0)
        return val if val is not None else 0

    if t == "checkbox":
        return p.get("checkbox", False)

    return ""


# ─────────────────────────────────────────────
# 1) 예산 현황
#    DB: 📊 단위사업별 예산관리
#    컬럼: 사업명(title), 예산금액(number), 집행금액(number),
#           진도율(number/percent), 상태(select), 사업구분(select)
# ─────────────────────────────────────────────
def fetch_budget():
    try:
        pages = query_db(DB_BUDGET)
    except Exception as e:
        print(f"[WARN] 예산 DB 조회 실패: {e}")
        return _default_budget()

    if not pages:
        return _default_budget()

    total_budget   = 0
    total_executed = 0
    categories     = []

    for p in pages:
        name     = prop(p, "사업명")
        budget   = prop(p, "예산금액")
        executed = prop(p, "집행금액")
        progress = prop(p, "진도율")
        status   = prop(p, "상태")
        category = prop(p, "사업구분")

        if not name:
            continue

        # 진도율이 0~1 소수점 형태면 100 곱하기
        if isinstance(progress, float) and 0 < progress <= 1:
            progress = round(progress * 100, 1)

        total_budget   += float(budget)
        total_executed += float(executed)

        rate = round(float(executed) / float(budget) * 100, 1) if budget > 0 else 0

        categories.append({
            "name"    : name,
            "budget"  : float(budget),
            "executed": float(executed),
            "rate"    : rate,
            "progress": float(progress),
            "status"  : status,
            "category": category,
        })

    exec_rate = round(total_executed / total_budget * 100, 1) if total_budget > 0 else 0

    return {
        "total_budget"   : total_budget,
        "total_executed" : total_executed,
        "execution_rate" : exec_rate,
        "remaining"      : total_budget - total_executed,
        "categories"     : categories,
    }


def _default_budget():
    return {
        "total_budget"   : 24000000000,
        "total_executed" : 9080000000,
        "execution_rate" : 37.8,
        "remaining"      : 14920000000,
        "categories"     : [],
    }


# ─────────────────────────────────────────────
# 2) 사업현황 (Milestones)
#    DB: 📊 단위사업별 예산관리 (동일 DB)
#    컬럼: 사업명(title), 진도율, 상태, 사업구분
# ─────────────────────────────────────────────
def fetch_projects():
    try:
        pages = query_db(DB_MILESTONES)
    except Exception as e:
        print(f"[WARN] 사업현황 DB 조회 실패: {e}")
        return _default_projects()

    if not pages:
        return _default_projects()

    items       = []
    status_count = {}
    total_prog  = 0

    for p in pages:
        name     = prop(p, "사업명")
        status   = prop(p, "상태")
        progress = prop(p, "진도율")
        category = prop(p, "사업구분")

        if not name:
            continue

        if isinstance(progress, float) and 0 < progress <= 1:
            progress = round(progress * 100, 1)

        status_count[status] = status_count.get(status, 0) + 1
        total_prog += float(progress)

        items.append({
            "name"    : name,
            "status"  : status,
            "progress": float(progress),
            "category": category,
        })

    avg_prog = round(total_prog / len(items), 1) if items else 0

    return {
        "overall_progress": avg_prog,
        "total_count"     : len(items),
        "status_count"    : status_count,
        "items"           : items,
    }


def _default_projects():
    return {
        "overall_progress": 42.5,
        "total_count"     : 9,
        "status_count"    : {"✅ 완료": 2, "🔄 진행중": 4, "⏸️ 대기": 3},
        "items"           : [],
    }


# ─────────────────────────────────────────────
# 3) 업무/이슈 현황
#    DB: 📝 회의 및 이슈 관리
#    컬럼: 제목(title), 유형(select), 우선순위(select),
#           주최자(people), 회의일시(date), 관련 프로젝트(multi_select)
# ─────────────────────────────────────────────
def fetch_tasks():
    try:
        pages = query_db(DB_TASKS)
    except Exception as e:
        print(f"[WARN] 이슈 DB 조회 실패: {e}")
        return _default_tasks()

    if not pages:
        return _default_tasks()

    items    = []
    type_count = {}

    for p in pages:
        title    = prop(p, "제목")
        kind     = prop(p, "유형")           # 주간회의, 긴급회의, 기술이슈 등
        priority = prop(p, "우선순위")        # 긴급, 높음, 보통, 낮음
        host     = prop(p, "주최자")          # person
        date_val = prop(p, "회의일시")        # date
        projects = prop(p, "관련 프로젝트")   # multi_select (list)

        if not title:
            continue

        type_count[kind] = type_count.get(kind, 0) + 1

        items.append({
            "name"    : title,
            "type"    : kind,
            "priority": priority,
            "host"    : host,
            "date"    : date_val,
            "projects": projects if isinstance(projects, list) else [],
        })

    # 우선순위 기준 정렬 (긴급 → 높음 → 보통 → 낮음)
    priority_order = {"긴급": 0, "높음": 1, "보통": 2, "낮음": 3}
    items.sort(key=lambda x: priority_order.get(x["priority"], 9))

    # 우선순위별 카운트
    urgent = sum(1 for x in items if x["priority"] == "긴급")
    high   = sum(1 for x in items if x["priority"] == "높음")
    normal = sum(1 for x in items if x["priority"] in ("보통", "낮음", ""))

    return {
        "total"      : len(items),
        "urgent"     : urgent,
        "high"       : high,
        "normal"     : normal,
        "type_count" : type_count,
        "recent"     : items[:15],  # 최근 15건
    }


def _default_tasks():
    return {
        "total"     : 0,
        "urgent"    : 0,
        "high"      : 0,
        "normal"    : 0,
        "type_count": {},
        "recent"    : [],
    }


# ─────────────────────────────────────────────
# 4) D-Day 계산
# ─────────────────────────────────────────────
def calc_dday():
    now   = datetime.now(KST)
    end   = datetime(2025, 12, 31, 23, 59, 59, tzinfo=KST)
    start = datetime(2023, 12,  1,  0,  0,  0, tzinfo=KST)

    dday        = (end - now).days
    total_days  = (end - start).days
    elapsed     = (now - start).days
    elapsed_rate = round(elapsed / total_days * 100, 1) if total_days > 0 else 0

    return {
        "end_date"    : "2025-12-31",
        "dday"        : dday,
        "elapsed_days": elapsed,
        "total_days"  : total_days,
        "elapsed_rate": elapsed_rate,
    }


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    print(f"\n[{now_kst}] ===== Notion 동기화 시작 =====")

    budget   = fetch_budget()
    projects = fetch_projects()
    tasks    = fetch_tasks()
    dday     = calc_dday()

    dashboard = {
        "meta": {
            "project_name": "아산시 강소형 스마트시티 조성사업",
            "last_updated": now_kst,
            "data_source" : "Notion API 자동 동기화 (매 30분)",
            "version"     : "3.1",
        },
        "dday"    : dday,
        "budget"  : budget,
        "projects": projects,
        "tasks"   : tasks,
    }

    # data/ 폴더에 저장
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "dashboard.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    print(f"✅ dashboard.json 저장 완료")
    print(f"   예산 집행률 : {budget['execution_rate']}%  ({budget['total_budget']/1e8:.1f}억 중 {budget['total_executed']/1e8:.1f}억)")
    print(f"   사업 진도율 : {projects['overall_progress']}%  ({projects['total_count']}개 사업)")
    print(f"   회의/이슈   : 전체 {tasks['total']}건  긴급 {tasks['urgent']}건  높음 {tasks['high']}건")
    print(f"==============================================\n")


if __name__ == "__main__":
    main()
