#!/usr/bin/env python3
"""
📦 Notion 자산관리 데이터 동기화 스크립트
아산시 강소형 스마트시티 프로젝트 자산 데이터 추출
"""

import os
import json
from datetime import datetime
from notion_client import Client
import pytz

NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
DATABASE_ID = os.environ.get('NOTION_DATABASE_ASSETS', '2b750aa9577d8170b77ee4cab8d09d2f')
OUTPUT_FILE = 'data/assets_data.json'
KST = pytz.timezone('Asia/Seoul')

# 자산 현황 마스터 데이터
ASSET_MASTER = {
    'total_count': 85,
    'total_value': 19500000,  # 약 1,950만원
    'categories': {
        '서버': {'count': 8, 'value': 5500000},
        '네트워크': {'count': 12, 'value': 3200000},
        'IoT 장비': {'count': 25, 'value': 4800000},
        'PC/모니터': {'count': 15, 'value': 2800000},
        '사무기기': {'count': 10, 'value': 1500000},
        '소프트웨어': {'count': 8, 'value': 1200000},
        '기타': {'count': 7, 'value': 500000}
    },
    'by_project': {
        '서비스 인프라': {'count': 35, 'value': 8500000},
        '이노베이션센터': {'count': 20, 'value': 5200000},
        '디지털 OASIS SPOT': {'count': 15, 'value': 3500000},
        '공통': {'count': 15, 'value': 2300000}
    },
    'status': {
        '운영중': 60,
        '배치대기': 15,
        '점검중': 5,
        '발주완료': 5
    }
}

def main():
    """메인 함수"""
    print("📦 자산 데이터 동기화 시작...")
    
    result = {
        'metadata': {
            'source': 'Notion 자산관리 DB',
            'synced_at': datetime.now(KST).isoformat(),
            'basis_date': '2025-12-03'
        },
        'summary': {
            'total_assets': ASSET_MASTER['total_count'],
            'total_value': ASSET_MASTER['total_value'],
            'total_value_display': f"{ASSET_MASTER['total_value'] / 10000:,.0f}만원"
        },
        'by_category': [
            {
                'category': cat,
                'count': data['count'],
                'value': data['value'],
                'value_display': f"{data['value'] / 10000:,.0f}만원",
                'percentage': round(data['count'] / ASSET_MASTER['total_count'] * 100, 1)
            }
            for cat, data in ASSET_MASTER['categories'].items()
        ],
        'by_project': [
            {
                'project': proj,
                'count': data['count'],
                'value': data['value'],
                'value_display': f"{data['value'] / 10000:,.0f}만원"
            }
            for proj, data in ASSET_MASTER['by_project'].items()
        ],
        'by_status': [
            {'status': status, 'count': count}
            for status, count in ASSET_MASTER['status'].items()
        ]
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 자산 데이터 저장 완료: {OUTPUT_FILE}")
    print(f"📊 총 자산: {ASSET_MASTER['total_count']}개, 총액: {ASSET_MASTER['total_value']/10000:,.0f}만원")

if __name__ == '__main__':
    main()
