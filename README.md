# 🌆 아산시 강소형 스마트시티 통합 포털

## 📋 개요
아산시 강소형 스마트시티 조성사업의 Slack - Notion - GitHub 실시간 연동 시스템입니다.

## 🔄 자동화 파이프라인

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Slack     │───>│   Notion    │───>│   GitHub    │
│  (#채널)    │    │  (Database) │    │   Pages     │
└─────────────┘    └─────────────┘    └─────────────┘
      ↑                   ↑                   ↓
      │                   │                   │
      └───────────────────┴───────────────────┘
              실시간 데이터 동기화 (2시간 주기)
```

## 📁 디렉토리 구조

```
.
├── .github/
│   └── workflows/
│       └── sync-notion-data.yml  # GitHub Actions 워크플로우
├── scripts/
│   ├── sync_wbs.py              # WBS 데이터 동기화
│   ├── sync_budget.py           # 예산 데이터 동기화
│   ├── sync_assets.py           # 자산 데이터 동기화
│   ├── sync_personnel.py        # 인력 데이터 동기화
│   └── generate_dashboard.py    # 대시보드 통합 데이터 생성
├── data/
│   ├── dashboard_data.json      # 통합 대시보드 데이터
│   ├── wbs_data.json           # WBS 데이터
│   ├── budget_data.json        # 예산 데이터
│   ├── assets_data.json        # 자산 데이터
│   └── personnel_data.json     # 인력 데이터
└── README.md
```

## ⚙️ GitHub Secrets 설정

GitHub Repository Settings > Secrets and variables > Actions에서 다음 시크릿을 설정하세요:

| Secret Name | 설명 |
|------------|------|
| `NOTION_API_KEY` | Notion Integration API Key |
| `NOTION_DATABASE_WBS` | WBS 데이터베이스 ID |
| `NOTION_DATABASE_BUDGET` | 예산관리 데이터베이스 ID |
| `NOTION_DATABASE_ASSETS` | 자산관리 데이터베이스 ID |
| `NOTION_DATABASE_PERSONNEL` | 인력관리 데이터베이스 ID |
| `SLACK_WEBHOOK_URL` | (선택) Slack 알림 Webhook URL |

## 🚀 사용 방법

### 자동 동기화
- GitHub Actions가 **매 2시간마다** 자동으로 실행됩니다.
- 스케줄: `0 */2 * * *` (UTC 기준)

### 수동 동기화
1. GitHub Repository의 Actions 탭으로 이동
2. "🔄 Notion-GitHub 실시간 동기화" 워크플로우 선택
3. "Run workflow" 버튼 클릭
4. 동기화 유형 선택 (full/wbs/budget/assets/personnel)

## 📊 대시보드 링크

- **통합 대시보드**: https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/
- **Notion 프로젝트**: https://www.notion.so/21650aa9577d80dc8278e0187c54677f

## 📈 프로젝트 현황 (2025-12-03 기준)

| 항목 | 값 |
|------|-----|
| 총 사업비 | 240억원 |
| 집행률 | 14.8% |
| 전체 진행률 | 42.5% |
| 남은 일수 | D-28 |

## 👥 담당자

- **PMO팀**: smartcity-pmo@cheileng.com
- **기술지원**: 이성호 (airlan506@icloud.com)

---
*마지막 업데이트: 2025-12-03*
