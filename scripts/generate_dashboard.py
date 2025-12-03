#!/usr/bin/env python3
"""
📊 아산 스마트시티 통합 대시보드 데이터 생성
모든 데이터를 통합하여 대시보드용 JSON 생성
"""

import os
import json
from datetime import datetime, timedelta
import pytz

OUTPUT_FILE = 'data/dashboard_data.json'
KST = pytz.timezone('Asia/Seoul')

def load_json_file(filepath):
    """JSON 파일 로드"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def calculate_project_kpis():
    """프로젝트 KPI 계산"""
    now = datetime.now(KST)
    project_end = datetime(2025, 12, 31, tzinfo=KST)
    days_remaining = (project_end - now).days
    
    return {
        'project_name': '아산시 강소형 스마트시티 조성사업',
        'project_code': 'ASAN-SC-2023',
        'total_budget': 24000000000,
        'budget_display': '240억원',
        'execution_rate': 14.8,
        'overall_progress': 42.5,
        'days_remaining': max(days_remaining, 0),
        'project_start': '2023-08-01',
        'project_end': '2025-12-31',
        'status': '진행중',
        'risk_level': '주의',
        'extension_requested': True
    }

def get_recent_activities():
    """최근 활동 내역"""
    return [
        {
            'date': '2025-12-03',
            'type': '시스템',
            'title': 'Notion-GitHub 실시간 연동 시스템 구축',
            'status': '완료'
        },
        {
            'date': '2025-11-29',
            'type': '계약',
            'title': 'AI통합관제 계약 체결 진행',
            'status': '진행중'
        },
        {
            'date': '2025-11-27',
            'type': '협상',
            'title': 'SDDC Platform 우선협상 기간 연장 (→12/05)',
            'status': '완료'
        },
        {
            'date': '2025-11-26',
            'type': '기술협상',
            'title': 'SDDC Platform 3차 기술협상 자료 제출',
            'status': '완료'
        },
        {
            'date': '2025-11-20',
            'type': '계약',
            'title': '유무선 네트워크 구축 용역 계약 체결',
            'status': '완료'
        }
    ]

def get_upcoming_schedules():
    """향후 주요 일정"""
    return [
        {'date': '2025-12-05', 'event': 'SDDC Platform 계약 체결 목표', 'type': '계약', 'assignee': '김주용'},
        {'date': '2025-12-08', 'event': '디지털OASIS 정보관리 업체선정', 'type': '선정', 'assignee': '함정영'},
        {'date': '2025-12-15', 'event': '4분기 중간점검', 'type': '점검', 'assignee': '이성호'},
        {'date': '2025-12-20', 'event': 'DRT 서비스 완료', 'type': '완료', 'assignee': 'PMO팀'},
        {'date': '2025-12-31', 'event': '사업년도 종료 / 예산 마감', 'type': '마감', 'assignee': '전체'}
    ]

def get_unit_project_status():
    """단위사업별 현황"""
    return [
        {'name': '유무선 네트워크 구축', 'progress': 96.2, 'status': '계약완료', 'budget': '8억원', 'color': '#22c55e'},
        {'name': '이노베이션센터 구축', 'progress': 93.4, 'status': '진행중', 'budget': '13.3억원', 'color': '#22c55e'},
        {'name': '서비스 인프라 구축', 'progress': 45.0, 'status': '협상완료', 'budget': '27억원', 'color': '#3b82f6'},
        {'name': 'SDDC Platform 구축', 'progress': 15.0, 'status': '기술협상', 'budget': '27억원', 'color': '#f59e0b'},
        {'name': 'AI통합관제 플랫폼', 'progress': 5.0, 'status': '계약진행', 'budget': '16억원', 'color': '#f59e0b'},
        {'name': 'DRT 모빌리티', 'progress': 5.0, 'status': '발주진행', 'budget': '10억원', 'color': '#f59e0b'},
        {'name': '디지털 OASIS SPOT', 'progress': 1.2, 'status': '설계중', 'budget': '35.54억원', 'color': '#ef4444'},
        {'name': '정보관리 서비스', 'progress': 0.0, 'status': '입찰공고', 'budget': '23억원', 'color': '#6b7280'}
    ]

def main():
    """메인 함수"""
    print("📊 대시보드 통합 데이터 생성 시작...")
    
    now = datetime.now(KST)
    
    # 개별 데이터 로드
    wbs_data = load_json_file('data/wbs_data.json')
    budget_data = load_json_file('data/budget_data.json')
    assets_data = load_json_file('data/assets_data.json')
    personnel_data = load_json_file('data/personnel_data.json')
    
    # 통합 대시보드 데이터 생성
    dashboard = {
        'metadata': {
            'generated_at': now.isoformat(),
            'version': '3.0',
            'source': 'Notion + Slack + Google Drive',
            'auto_sync': True,
            'sync_interval': '2시간'
        },
        'project': calculate_project_kpis(),
        'budget': {
            'total': 24000000000,
            'allocated': 17134000000,
            'contracted': 3358000000,
            'executed': 2530000000,
            'remaining': 14604000000,
            'execution_rate': 14.8,
            'by_source': {
                'national': {'amount': 12000000000, 'display': '120억원', 'rate': 50},
                'provincial': {'amount': 2880000000, 'display': '28.8억원', 'rate': 12},
                'city': {'amount': 9120000000, 'display': '91.2억원', 'rate': 38}
            }
        },
        'progress': {
            'overall': 42.5,
            'by_phase': {
                'planning': 100,
                'design': 85,
                'development': 40,
                'testing': 0,
                'deployment': 0
            }
        },
        'unit_projects': get_unit_project_status(),
        'timeline': {
            'start': '2023-08-01',
            'end': '2025-12-31',
            'days_total': 883,
            'days_elapsed': 883 - max((datetime(2025, 12, 31) - now.replace(tzinfo=None)).days, 0),
            'days_remaining': max((datetime(2025, 12, 31) - now.replace(tzinfo=None)).days, 0)
        },
        'risks': {
            'total': 8,
            'critical': 2,
            'high': 3,
            'medium': 3,
            'total_amount': 14100000000
        },
        'recent_activities': get_recent_activities(),
        'upcoming_schedules': get_upcoming_schedules(),
        'team': {
            'total': 50,
            'pmo': 4,
            'by_org': [
                {'name': '제일엔지니어링', 'count': 15, 'role': 'PMO/주관사'},
                {'name': '충남연구원', 'count': 8, 'role': '리빙랩'},
                {'name': 'KAIST', 'count': 5, 'role': '기술자문'},
                {'name': '호서대학교', 'count': 7, 'role': '산학협력'},
                {'name': '협력업체', 'count': 15, 'role': '용역수행'}
            ]
        },
        'assets': {
            'total_count': 85,
            'total_value': 19500000,
            'categories': [
                {'name': '서버', 'count': 8},
                {'name': '네트워크', 'count': 12},
                {'name': 'IoT 장비', 'count': 25},
                {'name': 'PC/모니터', 'count': 15},
                {'name': '사무기기', 'count': 10},
                {'name': '소프트웨어', 'count': 8},
                {'name': '기타', 'count': 7}
            ]
        },
        'sync_status': {
            'slack': {'status': 'active', 'last_sync': now.isoformat()},
            'notion': {'status': 'active', 'last_sync': now.isoformat()},
            'github': {'status': 'active', 'last_sync': now.isoformat()},
            'google_drive': {'status': 'active', 'last_sync': now.isoformat()}
        },
        'links': {
            'notion_main': 'https://www.notion.so/21650aa9577d80dc8278e0187c54677f',
            'github_dashboard': 'https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/',
            'github_repo': 'https://github.com/leesungho-ai/Asan-Smartcity-integration-Portal',
            'slack_workspace': 'https://asansmartcity.slack.com'
        }
    }
    
    # 저장
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 대시보드 데이터 저장 완료: {OUTPUT_FILE}")
    print(f"📊 전체 진행률: {dashboard['progress']['overall']}%")
    print(f"💰 예산 집행률: {dashboard['budget']['execution_rate']}%")
    print(f"⏰ 남은 일수: D-{dashboard['timeline']['days_remaining']}")

if __name__ == '__main__':
    main()
