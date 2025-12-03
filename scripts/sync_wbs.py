#!/usr/bin/env python3
"""
🔄 Notion WBS 데이터 동기화 스크립트
아산시 강소형 스마트시티 프로젝트 WBS 데이터를 Notion에서 추출하여 JSON으로 저장
"""

import os
import json
from datetime import datetime
from notion_client import Client
import pytz

# 설정
NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
DATABASE_ID = os.environ.get('NOTION_DATABASE_WBS', '7d94e975-ed67-475b-8ac5-48b4fa36b755')
OUTPUT_FILE = 'data/wbs_data.json'
KST = pytz.timezone('Asia/Seoul')

def init_notion_client():
    """Notion 클라이언트 초기화"""
    if not NOTION_API_KEY:
        raise ValueError("NOTION_API_KEY 환경변수가 설정되지 않았습니다.")
    return Client(auth=NOTION_API_KEY)

def get_property_value(prop):
    """Notion 속성에서 값 추출"""
    if not prop:
        return None
    
    prop_type = prop.get('type')
    
    if prop_type == 'title':
        return ''.join([t.get('plain_text', '') for t in prop.get('title', [])])
    elif prop_type == 'rich_text':
        return ''.join([t.get('plain_text', '') for t in prop.get('rich_text', [])])
    elif prop_type == 'select':
        select = prop.get('select')
        return select.get('name') if select else None
    elif prop_type == 'multi_select':
        return [s.get('name') for s in prop.get('multi_select', [])]
    elif prop_type == 'status':
        status = prop.get('status')
        return status.get('name') if status else None
    elif prop_type == 'number':
        return prop.get('number')
    elif prop_type == 'date':
        date = prop.get('date')
        if date:
            return {
                'start': date.get('start'),
                'end': date.get('end')
            }
        return None
    elif prop_type == 'people':
        return [p.get('name', p.get('id')) for p in prop.get('people', [])]
    elif prop_type == 'url':
        return prop.get('url')
    elif prop_type == 'formula':
        formula = prop.get('formula', {})
        return formula.get(formula.get('type'))
    elif prop_type == 'created_time':
        return prop.get('created_time')
    elif prop_type == 'last_edited_time':
        return prop.get('last_edited_time')
    else:
        return None

def fetch_wbs_data(notion):
    """Notion에서 WBS 데이터 가져오기"""
    results = []
    has_more = True
    start_cursor = None
    
    while has_more:
        query_params = {
            "database_id": DATABASE_ID,
            "page_size": 100
        }
        if start_cursor:
            query_params["start_cursor"] = start_cursor
            
        response = notion.databases.query(**query_params)
        
        for page in response.get('results', []):
            props = page.get('properties', {})
            
            item = {
                'id': page.get('id'),
                'url': page.get('url'),
                '작업_ID': get_property_value(props.get('작업 ID')),
                '작업명': get_property_value(props.get('작업명')),
                '업무_영역': get_property_value(props.get('업무 영역')),
                '진행현황': get_property_value(props.get('진행현황')),
                '우선순위': get_property_value(props.get('우선순위')),
                '담당자': get_property_value(props.get('담당자')),
                '시작일': get_property_value(props.get('시작일')),
                '종료일': get_property_value(props.get('종료일')),
                '실제_시작일': get_property_value(props.get('실제 시작일')),
                '실제_종료일': get_property_value(props.get('실제 종료일')),
                '진척율': get_property_value(props.get('진척율')),
                '작업_유형': get_property_value(props.get('작업 유형')),
                '리스크레벨': get_property_value(props.get('리스크레벨')),
                '산출물': get_property_value(props.get('산출물')),
                '비고': get_property_value(props.get('비고')),
                '생성일': get_property_value(props.get('생성일')),
                '최종_수정일': get_property_value(props.get('최종 수정일'))
            }
            results.append(item)
        
        has_more = response.get('has_more', False)
        start_cursor = response.get('next_cursor')
    
    return results

def calculate_statistics(data):
    """WBS 통계 계산"""
    total = len(data)
    
    # 진행현황별 집계
    status_counts = {}
    for item in data:
        status = item.get('진행현황', '미정')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # 업무 영역별 집계
    area_counts = {}
    for item in data:
        area = item.get('업무_영역', '기타')
        area_counts[area] = area_counts.get(area, 0) + 1
    
    # 우선순위별 집계
    priority_counts = {}
    for item in data:
        priority = item.get('우선순위', '미정')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # 평균 진척율
    progress_values = [item.get('진척율', 0) or 0 for item in data]
    avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
    
    return {
        'total_tasks': total,
        'status_distribution': status_counts,
        'area_distribution': area_counts,
        'priority_distribution': priority_counts,
        'average_progress': round(avg_progress * 100, 1)
    }

def main():
    """메인 함수"""
    print("🔄 WBS 데이터 동기화 시작...")
    
    # Notion 클라이언트 초기화
    notion = init_notion_client()
    
    # 데이터 가져오기
    print("📥 Notion에서 데이터 가져오는 중...")
    wbs_data = fetch_wbs_data(notion)
    print(f"✅ {len(wbs_data)}개 항목 조회 완료")
    
    # 통계 계산
    statistics = calculate_statistics(wbs_data)
    
    # 결과 구성
    result = {
        'metadata': {
            'source': 'Notion',
            'database_id': DATABASE_ID,
            'synced_at': datetime.now(KST).isoformat(),
            'total_items': len(wbs_data)
        },
        'statistics': statistics,
        'data': wbs_data
    }
    
    # 디렉토리 생성
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # JSON 파일 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ WBS 데이터 저장 완료: {OUTPUT_FILE}")
    print(f"📊 통계: 총 {statistics['total_tasks']}개 작업, 평균 진척율 {statistics['average_progress']}%")

if __name__ == '__main__':
    main()
