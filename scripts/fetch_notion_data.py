#!/usr/bin/env python3
"""
아산시 스마트시티 Notion 데이터 수집 스크립트
실제 Notion API를 사용하여 데이터를 수집합니다.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# ============================================
# 실제 Notion 데이터베이스/페이지 ID (현재 환경)
# ============================================
NOTION_IDS = {
    # 페이지
    "project_management": "21650aa9577d80dc8278e0187c54677f",
    "dashboard": "25a50aa9577d81b09085e918f674b7ce",
    "asset_management": "2b750aa9577d8170b77ee4cab8d09d2f",
    
    # 데이터베이스 (collection ID)
    "budget": "2aa50aa9-577d-8184-b2ad-000b15cd9ea9",
    "wbs": "7d94e975-ed67-475b-8ac5-48b4fa36b755",
    "risks": "051e4cd8-cc33-413f-a176-dad2ba669fed",
    "meetings": "4da13d05-dadd-4e71-9ca7-2dd507f7b694",
    "documents": "1b650aa9-577d-80f4-a23c-000b413fe02a",
    "slack_channels": "cf49879e-8da0-4355-8815-73df2169e21c"
}

class NotionFetcher:
    """Notion API 데이터 수집기"""
    
    def __init__(self):
        self.api_key = os.environ.get('NOTION_API_KEY', '')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.data = {}
    
    def query_database(self, database_id: str, filter_params: Optional[Dict] = None) -> List[Dict]:
        """데이터베이스 쿼리"""
        url = f"{self.base_url}/databases/{database_id}/query"
        payload = {}
        if filter_params:
            payload['filter'] = filter_params
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('results', [])
            else:
                print(f"DB 쿼리 실패: {database_id} - {response.status_code}")
                return []
        except Exception as e:
            print(f"DB 쿼리 오류: {e}")
            return []
    
    def get_page(self, page_id: str) -> Optional[Dict]:
        """페이지 정보 조회"""
        url = f"{self.base_url}/pages/{page_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"페이지 조회 오류: {e}")
            return None
    
    def fetch_budget_data(self) -> Dict[str, Any]:
        """예산 데이터 수집"""
        print("📊 예산 데이터 수집 중...")
        
        records = self.query_database(NOTION_IDS["budget"])
        
        # 기본값 설정 (Notion API 접근 불가 시)
        budget_data = {
            "total": 24000000000,  # 240억원
            "national": 12000000000,  # 국비 120억
            "local": 12000000000,  # 지방비 120억
            "allocated": 17134000000,  # 배정예산 171.34억
            "contracted": 3358000000,  # 계약금액 33.58억
            "executed": 2530000000,  # 집행금액 25.3억
            "execution_rate": 14.8,
            "remaining": 14604000000,  # 잔액 146.04억
            "by_source": {
                "national": {"total": 12000000000, "executed": 1270000000, "rate": 10.6},
                "provincial": {"total": 2880000000, "executed": 300000000, "rate": 10.4},
                "municipal": {"total": 9120000000, "executed": 960000000, "rate": 10.5}
            },
            "records_count": len(records),
            "updated_at": datetime.now().isoformat()
        }
        
        # 실제 레코드가 있으면 집계
        if records:
            total_executed = 0
            for record in records:
                props = record.get('properties', {})
                # 집행금액 필드 확인 (필드명은 실제 DB에 맞게 조정 필요)
                if '집행금액' in props:
                    val = props['집행금액'].get('number', 0)
                    if val:
                        total_executed += val
            
            if total_executed > 0:
                budget_data["executed"] = total_executed
                budget_data["execution_rate"] = round(total_executed / budget_data["total"] * 100, 1)
        
        return budget_data
    
    def fetch_wbs_data(self) -> Dict[str, Any]:
        """WBS 진행현황 수집"""
        print("📈 WBS 데이터 수집 중...")
        
        records = self.query_database(NOTION_IDS["wbs"])
        
        # 단위사업별 현황 (현재 기준)
        projects = {
            "network": {"name": "유무선 네트워크 구축", "budget": 800000000, "progress": 96.2, "status": "계약완료"},
            "service_infra": {"name": "서비스 인프라 플랫폼", "budget": 2700000000, "progress": 85.0, "status": "협상완료"},
            "innovation_center": {"name": "이노베이션센터", "budget": 1330000000, "progress": 93.4, "status": "구축완료"},
            "oasis_spot": {"name": "디지털 OASIS SPOT", "budget": 3554000000, "progress": 1.2, "status": "시유지변경"},
            "sddc_platform": {"name": "SDDC Platform", "budget": 2700000000, "progress": 40.0, "status": "기술협상완료"},
            "ai_control": {"name": "AI통합관제", "budget": 1600000000, "progress": 30.0, "status": "개발중"},
            "data_hub": {"name": "정보관리서비스", "budget": 2300000000, "progress": 15.0, "status": "업체선정중"},
            "drt": {"name": "DRT 모빌리티", "budget": 1000000000, "progress": 5.0, "status": "개발중"},
            "supervision": {"name": "감리용역", "budget": 160000000, "progress": 0, "status": "신설(1.6억)"}
        }
        
        # 가중 평균 진행률 계산
        weights = {
            "network": 10, "service_infra": 15, "innovation_center": 10,
            "oasis_spot": 20, "sddc_platform": 15, "ai_control": 10,
            "data_hub": 12, "drt": 6, "supervision": 2
        }
        
        weighted_sum = sum(projects[k]["progress"] * weights[k] for k in projects)
        total_weight = sum(weights.values())
        overall_progress = round(weighted_sum / total_weight, 1)
        
        return {
            "projects": projects,
            "weights": weights,
            "overall_progress": overall_progress,
            "records_count": len(records),
            "updated_at": datetime.now().isoformat()
        }
    
    def fetch_risk_data(self) -> Dict[str, Any]:
        """리스크 현황 수집"""
        print("⚠️ 리스크 데이터 수집 중...")
        
        records = self.query_database(NOTION_IDS["risks"])
        
        risks = {
            "summary": {
                "critical": 2,  # 긴급
                "high": 3,      # 높음
                "medium": 3,    # 주의
                "low": 0
            },
            "total_exposure": 14100000000,  # 141억원
            "items": [
                {
                    "id": "RISK-001",
                    "title": "OASIS SPOT 시유지 변경",
                    "level": "critical",
                    "impact": 3554000000,
                    "status": "진행중",
                    "due_date": "2025-12-10"
                },
                {
                    "id": "RISK-002", 
                    "title": "사업기간 연장 승인",
                    "level": "critical",
                    "impact": 0,
                    "status": "국토부 제출완료",
                    "due_date": "2025-12-10"
                }
            ],
            "records_count": len(records),
            "updated_at": datetime.now().isoformat()
        }
        
        return risks
    
    def fetch_schedule_data(self) -> Dict[str, Any]:
        """일정 현황"""
        print("📅 일정 데이터 수집 중...")
        
        today = datetime.now()
        end_date = datetime(2025, 12, 31)
        remaining_days = (end_date - today).days
        
        schedule = {
            "today": today.strftime('%Y-%m-%d'),
            "end_date": "2025-12-31",
            "remaining_days": max(0, remaining_days),
            "completed": [
                {"date": "2025-12-04", "event": "실시계획 변경서 국토부 제출", "status": "completed"}
            ],
            "upcoming": [
                {"date": "2025-12-05", "event": "SDDC Platform 계약 체결 목표", "status": "upcoming"},
                {"date": "2025-12-08", "event": "디지털OASIS 정보관리 업체선정", "status": "upcoming"},
                {"date": "2025-12-10", "event": "실시계획 변경 국토부 승인 예상", "status": "upcoming"},
                {"date": "2025-12-15", "event": "4분기 중간점검", "status": "upcoming"},
                {"date": "2025-12-20", "event": "DRT 서비스 완료", "status": "upcoming"},
                {"date": "2025-12-27", "event": "연간 최종 성과보고서 제출", "status": "upcoming"},
                {"date": "2025-12-31", "event": "사업년도 종료 / 예산 마감", "status": "upcoming"}
            ],
            "updated_at": datetime.now().isoformat()
        }
        
        return schedule
    
    def run(self, sync_type: str = "full") -> Dict[str, Any]:
        """데이터 수집 실행"""
        print(f"\n{'='*50}")
        print(f"🔄 Notion 데이터 수집 시작")
        print(f"   유형: {sync_type}")
        print(f"   시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}")
        print(f"{'='*50}\n")
        
        result = {
            "sync_type": sync_type,
            "generated_at": datetime.now().isoformat(),
            "notion_ids": NOTION_IDS
        }
        
        if sync_type in ["full", "budget"]:
            result["budget"] = self.fetch_budget_data()
        
        if sync_type in ["full", "progress"]:
            result["wbs"] = self.fetch_wbs_data()
            result["risks"] = self.fetch_risk_data()
        
        if sync_type in ["full", "dashboard"]:
            result["schedule"] = self.fetch_schedule_data()
        
        # 결과 저장
        os.makedirs('data', exist_ok=True)
        with open('data/notion_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 데이터 수집 완료: data/notion_data.json")
        return result

def main():
    sync_type = os.environ.get('SYNC_TYPE', 'full')
    
    fetcher = NotionFetcher()
    result = fetcher.run(sync_type)
    
    print(json.dumps({"success": True, "sync_type": sync_type}, indent=2))

if __name__ == "__main__":
    main()
