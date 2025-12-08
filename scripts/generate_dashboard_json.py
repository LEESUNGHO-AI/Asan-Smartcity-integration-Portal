#!/usr/bin/env python3
"""
대시보드 JSON 생성 스크립트
Notion 데이터를 기반으로 GitHub Pages 대시보드용 JSON을 생성합니다.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

def load_notion_data() -> Dict[str, Any]:
    """Notion 데이터 로드"""
    data_path = 'data/notion_data.json'
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def generate_dashboard_json() -> Dict[str, Any]:
    """대시보드 JSON 생성"""
    notion_data = load_notion_data()
    now = datetime.now()
    
    # 잔여일수 계산
    end_date = datetime(2025, 12, 31)
    remaining_days = max(0, (end_date - now).days)
    
    # 예산 데이터
    budget = notion_data.get('budget', {})
    wbs = notion_data.get('wbs', {})
    risks = notion_data.get('risks', {})
    schedule = notion_data.get('schedule', {})
    
    dashboard = {
        # 프로젝트 기본 정보
        "project": {
            "name": "아산시 강소형 스마트시티 구축사업",
            "subtitle": "디지털 OASIS 구현을 통한 지역경제 활성화",
            "code": "ASAN-SMARTCITY-2025",
            "period": "2023.08 ~ 2025.12",
            "location": "충청남도 아산시 도고면·배방읍 일원",
            "total_budget": 24000000000,
            "status": "진행중"
        },
        
        # 핵심 요약 (대시보드 상단)
        "summary": {
            "remaining_days": remaining_days,
            "overall_progress": wbs.get('overall_progress', 42.5),
            "budget_execution_rate": budget.get('execution_rate', 14.8),
            "risk_count": risks.get('summary', {}).get('critical', 2),
            "status_message": f"D-{remaining_days} | 실시계획 변경 국토부 제출 완료"
        },
        
        # 예산 현황
        "budget": {
            "total": budget.get('total', 24000000000),
            "national": budget.get('national', 12000000000),
            "local": budget.get('local', 12000000000),
            "allocated": budget.get('allocated', 17134000000),
            "contracted": budget.get('contracted', 3358000000),
            "executed": budget.get('executed', 2530000000),
            "execution_rate": budget.get('execution_rate', 14.8),
            "remaining": budget.get('remaining', 14604000000),
            "by_source": budget.get('by_source', {
                "national": {"total": 12000000000, "executed": 1270000000, "rate": 10.6},
                "provincial": {"total": 2880000000, "executed": 300000000, "rate": 10.4},
                "municipal": {"total": 9120000000, "executed": 960000000, "rate": 10.5}
            })
        },
        
        # 단위사업별 현황
        "projects": [
            {"id": "network", "name": "유무선 네트워크 구축", "budget": 800000000, "progress": 96.2, "status": "계약완료", "color": "#22c55e"},
            {"id": "service_infra", "name": "서비스 인프라 플랫폼", "budget": 2700000000, "progress": 85.0, "status": "협상완료", "color": "#22c55e"},
            {"id": "innovation", "name": "이노베이션센터", "budget": 1330000000, "progress": 93.4, "status": "구축완료", "color": "#22c55e"},
            {"id": "oasis_spot", "name": "디지털 OASIS SPOT", "budget": 3554000000, "progress": 1.2, "status": "시유지변경", "color": "#f59e0b"},
            {"id": "sddc", "name": "SDDC Platform", "budget": 2700000000, "progress": 40.0, "status": "기술협상완료", "color": "#3b82f6"},
            {"id": "ai_control", "name": "AI통합관제", "budget": 1600000000, "progress": 30.0, "status": "개발중", "color": "#3b82f6"},
            {"id": "data_hub", "name": "정보관리서비스", "budget": 2300000000, "progress": 15.0, "status": "업체선정중", "color": "#f59e0b"},
            {"id": "drt", "name": "DRT 모빌리티", "budget": 1000000000, "progress": 5.0, "status": "개발중", "color": "#3b82f6"},
            {"id": "supervision", "name": "감리용역", "budget": 160000000, "progress": 0, "status": "신설(1.6억)", "color": "#ef4444"}
        ],
        
        # 리스크 현황
        "risks": {
            "summary": risks.get('summary', {"critical": 2, "high": 3, "medium": 3, "low": 0}),
            "total_exposure": risks.get('total_exposure', 14100000000),
            "top_items": [
                {"title": "OASIS SPOT 시유지 변경", "level": "critical", "status": "진행중"},
                {"title": "사업기간 연장 승인", "level": "critical", "status": "국토부 제출완료"}
            ]
        },
        
        # 일정
        "timeline": schedule.get('upcoming', [
            {"date": "2025-12-05", "event": "SDDC Platform 계약 체결", "status": "upcoming"},
            {"date": "2025-12-08", "event": "정보관리서비스 업체선정", "status": "upcoming"},
            {"date": "2025-12-10", "event": "국토부 승인 예상", "status": "upcoming"},
            {"date": "2025-12-15", "event": "4분기 중간점검", "status": "upcoming"},
            {"date": "2025-12-20", "event": "DRT 서비스 완료", "status": "upcoming"},
            {"date": "2025-12-31", "event": "사업년도 종료", "status": "upcoming"}
        ]),
        
        # 최근 변경사항
        "changes": {
            "latest": {
                "date": "2025-12-04",
                "title": "7차 실시계획 변경",
                "items": [
                    "사업기간 연장: 단위사업별 5~8개월",
                    "감리용역비 신설: 1.6억원",
                    "시유지 변경: OASIS SPOT 부지",
                    "예산 재편성: 총액 240억 유지"
                ],
                "status": "국토부 제출완료",
                "approval_expected": "2025-12-10"
            }
        },
        
        # 메타데이터
        "metadata": {
            "generated_at": now.isoformat(),
            "updated_at": now.strftime('%Y-%m-%d %H:%M:%S KST'),
            "next_update": "매일 09:00 KST",
            "source": "Notion API",
            "version": "2.0"
        },
        
        # 링크
        "links": {
            "notion": "https://www.notion.so/21650aa9577d80dc8278e0187c54677f",
            "github": "https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal",
            "dashboard": "https://leesungho-ai.github.io/Asan-smartcity-budget/"
        }
    }
    
    return dashboard

def save_dashboard_json():
    """대시보드 JSON 저장"""
    dashboard = generate_dashboard_json()
    
    # 루트의 data 폴더에 저장 (GitHub Pages용)
    os.makedirs('data', exist_ok=True)
    with open('data/dashboard.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 대시보드 JSON 생성 완료")
    print(f"   - data/dashboard.json")
    
    return dashboard

def main():
    dashboard = save_dashboard_json()
    print(json.dumps({"success": True, "updated_at": dashboard["metadata"]["updated_at"]}, indent=2))

if __name__ == "__main__":
    main()
