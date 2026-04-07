# 통합 포털 v4.0 배포 가이드

## 변경 사항 요약

### 문제점 (v3.0)
| 항목 | 포털 표시값 | 실제값 | 원인 |
|------|-----------|--------|------|
| 예산 집행률 | 23.6% | 41.16% | Notion 실패 시 3월 하드코딩 사용 |
| 총예산 | 184.3억 | 240억 | 단위사업 합계 불일치 |
| WBS 공정률 | 49.6% | 52.3% | WBS DB ID 오류 (0ed4b202→559654ae) |
| 비목별 | 하드코딩 | BMS 실시간 | Notion만 사용, fallback 고정 |
| 서비스별 WBS | 하드코딩 11개 | 실시간 7개 Level-1 | 하드코딩 |
| 리스크 | 하드코딩 8건 | 데이터 기반 자동 생성 | 하드코딩 |

### 수정 내용 (v4.0)
1. **3-tier 데이터 소싱**: 하위시스템 JSON → Notion API → Fallback
2. **WBS DB ID 수정**: `559654ae-d940-4d9f-8822-5ea0adc7d746`
3. **BMS JSON 연동**: budget.json에서 비목별 예산 자동 수신
4. **WBS JSON 연동**: summary-data.json + wbs-data.json 자동 수신
5. **동적 리스크 생성**: 집행률/기간/WBS 비교 자동 분석
6. **동적 WBS 서비스**: Level-1 가중치 기반 실시간

## 배포 순서

### 1. scripts/generate_dashboard.py 교체
```bash
# GitHub Web UI에서:
# 1. scripts/generate_dashboard.py 파일 열기
# 2. 연필 아이콘(Edit) 클릭
# 3. 전체 내용을 이 패키지의 scripts/generate_dashboard.py로 교체
# 4. "Commit changes" 클릭
```

### 2. GitHub Actions Secrets 확인
```
Settings → Secrets and variables → Actions
- NOTION_TOKEN: 유효한 Notion Integration Token
  (만료되었으면 https://www.notion.so/my-integrations 에서 재발급)
```

### 3. 수동 실행으로 확인
```
Actions → "대시보드 Notion 자동 동기화" → Run workflow
```

### 4. 결과 확인
- https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/
- 비목별 예산이 BMS와 일치하는지 확인
- WBS 공정률이 52.3%로 표시되는지 확인

## 데이터 흐름도

```
┌──────────────────────────────────────────────────┐
│              통합 포털 v4.0                        │
│              generate_dashboard.py                │
├──────────────────────────────────────────────────┤
│                                                  │
│  1차 소스: 하위 시스템 JSON (HTTP)                   │
│  ┌─────────────┐  ┌──────────────┐               │
│  │ BMS          │  │ WBS           │              │
│  │ budget.json  │  │ summary.json  │              │
│  │ → 비목별 예산 │  │ → 공정률      │               │
│  │ → 총집행률   │  │ → 서비스별    │                │
│  └─────────────┘  └──────────────┘               │
│                                                  │
│  2차 소스: Notion API (NOTION_TOKEN)               │
│  ┌──────────────────────────────────┐            │
│  │ 단위사업별 예산현황 DB (c6073bc5) │             │
│  │ 비목별 예산현황 DB    (c47fceb7) │              │
│  │ WBS 2026 DB          (559654ae) │              │
│  └──────────────────────────────────┘            │
│                                                  │
│  3차 소스: Fallback (하드코딩, 최후수단)             │
│                                                  │
│  출력: index.html + data/snapshot.json            │
└──────────────────────────────────────────────────┘
```

## NOTION_TOKEN 관련 주의사항
- GitHub Actions Secrets에서 `NOTION_TOKEN`이 유효해야 단위사업 데이터가 Notion에서 로드됩니다
- 만료 시: Notion → Settings → My integrations → Token 재발급 → GitHub Secrets 업데이트
- BMS/WBS 데이터는 NOTION_TOKEN 없이도 HTTP로 직접 가져옵니다
