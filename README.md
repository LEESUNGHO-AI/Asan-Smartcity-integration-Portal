# 아산시 강소형 스마트시티 조성사업 통합 대시보드

공공기관 스타일의 체계적인 프로젝트 관리 대시보드입니다.  
노션과 실시간 동기화되어 항상 최신 데이터를 표시합니다.

## 📊 주요 기능

- **예산 현황**: 재원별(국비/도비/시비) 배정 및 집행 현황
- **단위사업 현황**: 9개 단위사업별 예산, 집행률, 진행상태
- **리스크 관리**: 긴급/높음/주의 단계별 리스크 현황
- **일정 관리**: D-Day 카운터 및 주요 일정
- **실시계획 변경**: 사업기간 연장, 예산 재편성 현황

## 🔗 노션 연동 페이지

| 페이지 | 용도 | 링크 |
|--------|------|------|
| 프로젝트 관리 | 메인 페이지 | [열기](https://www.notion.so/21650aa9577d80dc8278e0187c54677f) |
| 프로젝트 대시보드 | 대시보드 원본 | [열기](https://www.notion.so/25a50aa9577d81b09085e918f674b7ce) |
| 예산관리 시스템 | 예산 DB | [열기](https://www.notion.so/2aa50aa9577d8128b6d4c5c21d845796) |

---

## 🚀 설치 및 배포

### 1. GitHub 저장소 설정

```bash
# 저장소 클론
git clone https://github.com/leesungho-ai/Asan-smartcity-budget.git
cd Asan-smartcity-budget

# 파일 추가
# index.html, sync-notion.js, .github/workflows/sync-deploy.yml
```

### 2. 노션 Integration 설정

1. [Notion Developers](https://www.notion.so/my-integrations)에서 Integration 생성
2. Integration Token 복사
3. 연동할 노션 페이지에서 `연결` → 생성한 Integration 추가

### 3. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions

| Secret 이름 | 값 |
|-------------|-----|
| `NOTION_API_KEY` | 노션 Integration Token |

### 4. GitHub Pages 활성화

1. Settings → Pages
2. Source: "GitHub Actions" 선택
3. 저장

---

## ⏰ 자동 동기화

GitHub Actions가 다음 시간에 자동으로 노션 데이터를 동기화합니다:

- 매일 오전 9:00 (KST)
- 매일 오후 3:00 (KST)  
- 매일 오후 6:00 (KST)
- main 브랜치에 push할 때

### 수동 동기화

GitHub → Actions → "노션 동기화 및 배포" → Run workflow

---

## 📁 파일 구조

```
├── index.html              # 메인 대시보드 HTML
├── sync-notion.js          # 노션 동기화 스크립트
├── data.json               # 동기화된 데이터 (자동 생성)
├── README.md               # 이 문서
└── .github/
    └── workflows/
        └── sync-deploy.yml # GitHub Actions 워크플로우
```

---

## 🛠 로컬 개발

```bash
# 의존성 설치
npm install @notionhq/client

# 환경변수 설정
export NOTION_API_KEY="your_notion_integration_token"

# 동기화 실행
node sync-notion.js

# 로컬 서버 실행 (선택)
npx serve .
```

---

## 📋 데이터 구조

### 예산 데이터 (budgetData)
```json
{
  "summary": {
    "totalBudget": 240,
    "allocatedBudget": 171.34,
    "executedAmount": 25.3,
    "executionRate": 14.8
  }
}
```

### 단위사업 데이터 (projectsData)
```json
{
  "name": "디지털 OASIS SPOT 구축",
  "budget": 35.54,
  "rate": 1.2,
  "status": "pending"
}
```

---

## 📞 문의

**PMO팀**
- 이성호 (기술/인프라 총괄): airlan506@icloud.com
- 김주용 (PM): smartcity-pmo@cheileng.com

**발주기관**
- 아산시 스마트도시팀: 041-540-2850

---

## 📜 라이선스

© 2025 제일엔지니어링 PMO팀  
아산시 강소형 스마트시티 조성사업
