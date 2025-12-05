# 🔄 아산시 스마트시티 Notion-GitHub 자동 동기화

Notion 프로젝트 관리 데이터를 자동으로 분석하고 GitHub Pages 대시보드를 업데이트하는 시스템입니다.

## 📅 자동 실행 스케줄

| 시간 | 작업 | 설명 |
|------|------|------|
| **매일 09:00 KST** | 전체 동기화 | Notion → GitHub 자동 동기화 |

## 🚀 빠른 시작 (3단계)

### 1단계: 저장소에 파일 추가

이 폴더의 모든 파일을 기존 `LEESUNGHO-AI/Asan-Smartcity-integration-Portal` 저장소에 복사합니다.

```bash
# 기존 저장소 클론
git clone https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal.git
cd Asan-Smartcity-integration-Portal

# 이 폴더의 파일들 복사 (수동 또는 명령어)
# .github/workflows/notion-auto-sync.yml
# scripts/fetch_notion_data.py
# scripts/generate_dashboard_json.py
# scripts/calculate_metrics.py

git add -A
git commit -m "🔄 Notion 자동 동기화 시스템 추가"
git push
```

### 2단계: GitHub Secrets 설정

GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 이름 | 값 | 필수 |
|-------------|-----|------|
| `NOTION_API_KEY` | Notion Integration Token | ✅ |

#### Notion API Key 발급 방법:
1. https://www.notion.so/my-integrations 접속
2. **+ New integration** 클릭
3. 이름 입력 (예: "아산시 스마트시티 자동화")
4. **Submit** 클릭
5. **Internal Integration Token** 복사

#### Notion 페이지에 Integration 연결:
1. Notion 워크스페이스의 메인 페이지 열기
2. 우측 상단 **...** 클릭 → **Connections** → **Add connections**
3. 방금 만든 Integration 선택

### 3단계: 수동 실행 테스트

1. GitHub 저장소 → **Actions** 탭
2. **🔄 아산시 스마트시티 Notion-GitHub 자동 동기화** 선택
3. **Run workflow** 클릭
4. 동기화 유형 선택 → **Run workflow**

## 📁 파일 구조

```
.github/
└── workflows/
    └── notion-auto-sync.yml    # GitHub Actions 워크플로우

scripts/
├── fetch_notion_data.py        # Notion API 데이터 수집
├── generate_dashboard_json.py  # 대시보드 JSON 생성
└── calculate_metrics.py        # 지표 계산

docs/
└── data/
    ├── dashboard.json          # 대시보드 데이터
    └── metrics.json            # 지표 데이터

data/                           # 로컬 데이터 백업
```

## 🔗 연동된 Notion ID

| 항목 | Notion ID |
|------|-----------|
| 프로젝트 관리 | `21650aa9577d80dc8278e0187c54677f` |
| 대시보드 | `25a50aa9577d81b09085e918f674b7ce` |
| 예산관리 DB | `2aa50aa9-577d-8184-b2ad-000b15cd9ea9` |
| WBS 관리 DB | `7d94e975-ed67-475b-8ac5-48b4fa36b755` |
| 리스크 관리 DB | `051e4cd8-cc33-413f-a176-dad2ba669fed` |
| 문서 허브 DB | `1b650aa9-577d-80f4-a23c-000b413fe02a` |

## 🔄 동기화되는 데이터

### 자동 수집
- 📊 예산 집행 현황
- 📈 단위사업별 진행률
- ⚠️ 리스크 현황
- 📅 일정 D-Day

### 자동 생성
- `dashboard.json` - GitHub Pages 대시보드용
- `metrics.json` - KPI 지표 데이터

## ❓ 문제 해결

### Actions가 실행되지 않음
- GitHub Settings → Actions → General → **Allow all actions** 확인

### Notion 데이터가 수집되지 않음
- Notion Integration이 페이지에 연결되어 있는지 확인
- API Key가 올바른지 확인

### 권한 오류
- GitHub Settings → Actions → General → **Read and write permissions** 활성화

---

**문의**: 제일엔지니어링 PMO팀  
**최종 업데이트**: 2025년 12월 5일
