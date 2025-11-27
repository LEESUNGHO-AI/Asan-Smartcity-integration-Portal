# 🏙️ 아산시 강소형 스마트시티 프로젝트 대시보드

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-success?logo=github)](https://leesungho-ai.github.io/Asan-smartcity-budget/)
[![Notion](https://img.shields.io/badge/Notion-Connected-black?logo=notion)](https://www.notion.so/21650aa9577d80dc8278e0187c54677f)
[![Last Updated](https://img.shields.io/badge/Updated-2025.11.27-blue)](https://github.com/leesungho-ai/Asan-smartcity-budget)

> **디지털 OASIS 구현을 통한 지역경제 활성화 및 데이터 기반 스마트시티 조성**  
> 충청남도 아산시 도고면·배방읍 일원 | 2023년 ~ 2025년 12월 | 총 240억원

## 📊 대시보드 미리보기

![Dashboard Preview](./assets/dashboard-preview.png)

## 🔗 바로가기

- **📊 라이브 대시보드**: [https://leesungho-ai.github.io/Asan-smartcity-budget/](https://leesungho-ai.github.io/Asan-smartcity-budget/)
- **📝 노션 프로젝트 관리**: [노션에서 보기](https://www.notion.so/21650aa9577d80dc8278e0187c54677f)

## 🎯 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **사업명** | 아산시 강소형 스마트시티 조성사업 |
| **사업유형** | 기존도시 - 지역소멸대응/인구변화대응 |
| **사업위치** | 충청남도 아산시 도고면·배방읍 일원 (약 44,350,000㎡) |
| **사업기간** | 2023년 8월 ~ 2025년 12월 (구축 3년, 운영 3년) |
| **총사업비** | 240억원 (국비 120억원, 지방비 120억원) |
| **총괄책임자** | 박상국 (아산시 스마트도시팀장) |
| **주관기관장** | 오세현 (아산시장) |

## 📈 핵심 지표 현황 (2025.11.27 기준)

### 예산 집행 현황
| 구분 | 금액 | 비율 |
|------|------|------|
| 총 사업비 | 240억원 | 100% |
| 배정예산 | 171.34억원 | 71.4% |
| 계약금액 | 33.58억원 | 14.0% |
| 집행금액 | 25.3억원 | 14.8% |
| 잔액 | 146.04억원 | - |

### 단위사업별 진행상태
| 단위사업 | 예산 | 집행률 | 상태 |
|---------|------|--------|------|
| 디지털 OASIS SPOT | 35.54억원 | 1.2% | 🟡 실시설계 |
| 이노베이션센터 | 13.3억원 | 93.4% | ✅ 구축완료 |
| 유무선 네트워크 | 8억원 | 96.2% | ✅ 계약완료 |
| SDDC Platform | 27억원 | 0% | 🔄 기술협상완료 |
| AI통합관제 | 16억원 | 0% | 🔄 계약예정 |
| 정보관리 서비스 | 23억원 | 0% | 🟡 입찰공고 |
| DRT 서비스 | 10억원 | 5.0% | 🟡 발주진행 |
| 사업관리(PMO) | 28.21억원 | - | 🔄 진행중 |
| **감리용역(신설)** | **1.6억원** | 0% | 🆕 신설 |

## 🛠️ 기술 스택

- **Frontend**: HTML5, CSS3 (Custom Properties), Vanilla JavaScript
- **Charts**: Chart.js
- **Icons**: Remix Icon
- **Fonts**: Noto Sans KR, IBM Plex Sans, JetBrains Mono
- **Hosting**: GitHub Pages
- **Data Source**: Notion API (MCP 연동)

## 📁 프로젝트 구조

```
Asan-smartcity-budget/
├── index.html          # 메인 대시보드 HTML
├── README.md           # 프로젝트 설명
├── assets/             # 이미지 및 리소스
│   └── dashboard-preview.png
└── .github/
    └── workflows/
        └── pages.yml   # GitHub Pages 자동 배포
```

## 🚀 배포 방법

### GitHub Pages 자동 배포

이 프로젝트는 GitHub Pages를 통해 자동으로 배포됩니다.

1. Repository Settings → Pages로 이동
2. Source를 "GitHub Actions"로 설정
3. `main` 브랜치에 push하면 자동 배포

### 로컬 개발

```bash
# 저장소 클론
git clone https://github.com/leesungho-ai/Asan-smartcity-budget.git

# 디렉토리 이동
cd Asan-smartcity-budget

# 로컬 서버 실행 (Python 3)
python -m http.server 8000

# 브라우저에서 확인
# http://localhost:8000
```

## 🔄 노션 연동

이 대시보드는 노션 MCP(Model Context Protocol)를 통해 데이터를 동기화합니다.

### 연동된 노션 데이터베이스
- 📊 예산관리 시스템
- 📋 WBS 관리 시스템
- ⚠️ 리스크 관리 시스템
- 📬 Slack 채널 통합 관리

### 데이터 업데이트 주기
- **자동 동기화**: Claude MCP 연동 시 실시간 반영
- **수동 업데이트**: 노션 페이지 편집 후 대시보드 재생성

## 📧 문의처

### 🏗️ 수행기관 (PMO)
- **이성호** (기술/인프라 총괄): airlan506@icloud.com
- **김주용** (PM): smartcity-pmo@cheileng.com
- **임혁** (계약/행정): smartcity-admin@cheileng.com

### 🏢 발주기관
- **아산시 스마트도시팀**: smartcity@asan.go.kr | 041-540-2850
- **국토교통부 도시경제과**: 044-201-4974

---

<p align="center">
  <strong>© 2025 제일엔지니어링 PMO팀</strong><br>
  아산시 강소형 스마트시티 조성사업
</p>
