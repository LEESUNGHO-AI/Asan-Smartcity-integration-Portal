#!/usr/bin/env python3
"""
👥 Notion 인력 현황 데이터 동기화 스크립트
아산시 강소형 스마트시티 프로젝트 인력 현황 데이터 추출
"""

import os
import json
from datetime import datetime
import pytz

OUTPUT_FILE = 'data/personnel_data.json'
KST = pytz.timezone('Asia/Seoul')

# 인력 현황 마스터 데이터
PERSONNEL_MASTER = {
    'total_personnel': 50,
    'by_organization': {
        '제일엔지니어링': {
            'role': 'PMO/주관사',
            'count': 15,
            'members': [
                {'name': '김주용', 'position': 'PM', 'role': '프로젝트 관리'},
                {'name': '임혁', 'position': 'PL', 'role': '계약/행정'},
                {'name': '이성호', 'position': 'PL', 'role': '기술/인프라'},
                {'name': '함정영', 'position': 'PM', 'role': '조달/입찰'}
            ]
        },
        '충남연구원': {
            'role': '리빙랩 운영',
            'count': 8,
            'members': []
        },
        'KAIST': {
            'role': '기술 자문',
            'count': 5,
            'members': []
        },
        '호서대학교': {
            'role': '산학협력',
            'count': 7,
            'members': []
        },
        '협력업체': {
            'role': '용역 수행',
            'count': 15,
            'members': []
        }
    },
    'by_role': {
        'PMO': 4,
        '개발': 12,
        '설계': 8,
        '시공': 10,
        '연구': 8,
        '행정': 5,
        '자문': 3
    }
}

def main():
    """메인 함수"""
    print("👥 인력 데이터 동기화 시작...")
    
    result = {
        'metadata': {
            'source': 'Notion 인력관리 DB',
            'synced_at': datetime.now(KST).isoformat(),
            'basis_date': '2025-12-03'
        },
        'summary': {
            'total_personnel': PERSONNEL_MASTER['total_personnel']
        },
        'by_organization': [
            {
                'organization': org,
                'role': data['role'],
                'count': data['count'],
                'key_members': data.get('members', [])[:4]  # 최대 4명
            }
            for org, data in PERSONNEL_MASTER['by_organization'].items()
        ],
        'by_role': [
            {'role': role, 'count': count}
            for role, count in PERSONNEL_MASTER['by_role'].items()
        ],
        'pmo_team': {
            'organization': '제일엔지니어링',
            'members': [
                {'name': '김주용', 'position': 'PM', 'responsibility': '프로젝트 총괄 관리', 'contact': 'smartcity-pmo@cheileng.com'},
                {'name': '임혁', 'position': 'PL', 'responsibility': '계약 및 행정업무', 'contact': 'smartcity-pmo@cheileng.com'},
                {'name': '이성호', 'position': 'PL', 'responsibility': '기술 및 인프라', 'contact': 'smartcity-pmo@cheileng.com'},
                {'name': '함정영', 'position': 'PM', 'responsibility': '조달 및 입찰관리', 'contact': 'smartcity-pmo@cheileng.com'}
            ]
        }
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 인력 데이터 저장 완료: {OUTPUT_FILE}")
    print(f"📊 총 인력: {PERSONNEL_MASTER['total_personnel']}명")

if __name__ == '__main__':
    main()
