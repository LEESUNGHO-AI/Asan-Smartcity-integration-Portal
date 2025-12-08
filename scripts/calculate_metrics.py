#!/usr/bin/env python3
"""
지표 계산 스크립트
예산 집행률, 진행률, D-Day 등 핵심 지표를 계산합니다.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

def calculate_metrics() -> Dict[str, Any]:
    """모든 지표 계산"""
    now = datetime.now()
    
    # 프로젝트 기간
    start_date = datetime(2023, 8, 1)
    end_date = datetime(2025, 12, 31)
    
    total_days = (end_date - start_date).days
    elapsed_days = (now - start_date).days
    remaining_days = max(0, (end_date - now).days)
    
    # 시간 진행률
    time_progress = min(100, round((elapsed_days / total_days) * 100, 1))
    
    # 단위사업별 가중치 및 진행률
    projects = {
        "network": {"weight": 10, "progress": 96.2, "budget": 800000000},
        "service_infra": {"weight": 15, "progress": 85.0, "budget": 2700000000},
        "innovation_center": {"weight": 10, "progress": 93.4, "budget": 1330000000},
        "oasis_spot": {"weight": 20, "progress": 1.2, "budget": 3554000000},
        "sddc_platform": {"weight": 15, "progress": 40.0, "budget": 2700000000},
        "ai_control": {"weight": 10, "progress": 30.0, "budget": 1600000000},
        "data_hub": {"weight": 12, "progress": 15.0, "budget": 2300000000},
        "drt": {"weight": 6, "progress": 5.0, "budget": 1000000000},
        "supervision": {"weight": 2, "progress": 0, "budget": 160000000}
    }
    
    # 가중 평균 진행률
    weighted_sum = sum(p["weight"] * p["progress"] for p in projects.values())
    total_weight = sum(p["weight"] for p in projects.values())
    overall_progress = round(weighted_sum / total_weight, 1)
    
    # 예산 지표
    total_budget = 24000000000  # 240억
    allocated_budget = 17134000000  # 171.34억
    executed_amount = 2530000000  # 25.3억
    execution_rate = round(executed_amount / total_budget * 100, 1)
    
    # 리스크 점수 (단순화)
    risk_score = 68  # 100점 만점, 낮을수록 위험
    
    metrics = {
        "timestamp": now.isoformat(),
        "date": now.strftime('%Y-%m-%d'),
        "time": now.strftime('%H:%M:%S KST'),
        
        # 시간 지표
        "time_metrics": {
            "total_days": total_days,
            "elapsed_days": elapsed_days,
            "remaining_days": remaining_days,
            "time_progress": time_progress,
            "d_day": f"D-{remaining_days}"
        },
        
        # 진행 지표
        "progress_metrics": {
            "overall_progress": overall_progress,
            "target_progress": time_progress,  # 시간 대비 목표
            "gap": round(overall_progress - time_progress, 1),  # 목표 대비 차이
            "status": "정상" if overall_progress >= time_progress * 0.8 else "주의"
        },
        
        # 예산 지표
        "budget_metrics": {
            "total_budget": total_budget,
            "allocated_budget": allocated_budget,
            "executed_amount": executed_amount,
            "execution_rate": execution_rate,
            "allocation_rate": round(allocated_budget / total_budget * 100, 1),
            "remaining_budget": total_budget - executed_amount
        },
        
        # 단위사업별 현황
        "project_metrics": {
            name: {
                "progress": data["progress"],
                "weight": data["weight"],
                "budget": data["budget"],
                "contribution": round(data["weight"] * data["progress"] / 100, 2)
            }
            for name, data in projects.items()
        },
        
        # 리스크 지표
        "risk_metrics": {
            "risk_score": risk_score,
            "critical_count": 2,
            "high_count": 3,
            "medium_count": 3,
            "total_exposure": 14100000000
        },
        
        # KPI 요약
        "kpi_summary": {
            "overall_health": "양호" if risk_score >= 60 and execution_rate >= 10 else "주의",
            "schedule_status": "정상" if remaining_days > 20 else "긴급",
            "budget_status": "정상" if execution_rate >= 10 else "지연",
            "risk_status": "관리중" if risk_score >= 50 else "위험"
        }
    }
    
    return metrics

def save_metrics():
    """지표 저장"""
    metrics = calculate_metrics()
    
    os.makedirs('data', exist_ok=True)
    
    # 저장
    with open('data/metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    # 요약 출력
    print(f"\n{'='*50}")
    print(f"📊 지표 계산 완료")
    print(f"{'='*50}")
    print(f"📅 날짜: {metrics['date']}")
    print(f"⏰ D-Day: {metrics['time_metrics']['d_day']}")
    print(f"📈 전체 진행률: {metrics['progress_metrics']['overall_progress']}%")
    print(f"💰 예산 집행률: {metrics['budget_metrics']['execution_rate']}%")
    print(f"⚠️ 리스크 점수: {metrics['risk_metrics']['risk_score']}/100")
    print(f"✅ 종합 상태: {metrics['kpi_summary']['overall_health']}")
    print(f"{'='*50}\n")
    
    return metrics

def main():
    metrics = save_metrics()
    print(json.dumps({"success": True, "d_day": metrics['time_metrics']['d_day']}, indent=2))

if __name__ == "__main__":
    main()
