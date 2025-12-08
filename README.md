# 🏙️ 아산시 강소형 스마트시티 구축사업 통합 대시보드

[![자동 업데이트](https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal/actions/workflows/notion-auto-sync.yml/badge.svg)](https://github.com/LEESUNGHO-AI/Asan-Smartcity-integration-Portal/actions)

> **실시간 대시보드**: [https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/](https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/)

---

## 📊 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **사업명** | 아산시 강소형 스마트시티 조성사업 |
| **부제** | 디지털 OASIS 구현을 통한 지역경제 활성화 |
| **사업기간** | 2023년 8월 ~ 2025년 12월 |
| **총사업비** | 240억원 (국비 120억 + 지방비 120억) |
| **사업위치** | 충청남도 아산시 도고면·배방읍 일원 |

---

## 🔄 자동 동기화 시스템

Notion 프로젝트 관리 데이터를 자동으로 분석하고 GitHub Pages 대시보드를 업데이트합니다.

### ⏰ 자동 실행 스케줄

| 시간 | 작업 |
|------|------|
| **매일 09:00 KST** | Notion → GitHub 전체 동기화 |

### 🔗 연동된 시스템

- **Notion**: 프로젝트 관리 페이지
- **GitHub Actions**: 자동 동기화 워크플로우
- **GitHub Pages**: 대시보드 호스팅

---

## 📁 파일 구조

```
/
├── index.html              ← 메인 대시보드 (GitHub Pages)
├── data/
│   └── dashboard.json      ← 대시보드 데이터 (자동 업데이트)
├── scripts/
│   ├── fetch_notion_data.py
│   ├── generate_dashboard_json.py
│   └── calculate_metrics.py
├── .github/
│   └── workflows/
│       └── notion-auto-sync.yml
└── README.md
```

---

## 🚀 설정 방법

### 1. GitHub Secrets 설정

**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | 값 |
|--------|-----|
| `NOTION_API_KEY` | Notion Integration Token |

### 2. GitHub Pages 설정

**Settings** → **Pages** → **Source**
- Branch: `main`
- Folder: `/ (root)`

### 3. 수동 실행

**Actions** → **🔄 아산시 스마트시티 Notion-GitHub 자동 동기화** → **Run workflow**

---

## 📈 대시보드 기능

- 🗓️ D-Day 카운터 (사업 종료일까지)
- 📊 전체 진행률 (가중평균)
- 💰 예산 집행 현황
- 📋 단위사업별 현황 (9개)
- ⚠️ 리스크 현황
- 📅 주요 일정

---

## 🔗 관련 링크

- [Notion 프로젝트 관리](https://www.notion.so/21650aa9577d80dc8278e0187c54677f)
- [대시보드](https://leesungho-ai.github.io/Asan-Smartcity-integration-Portal/)

---

**담당**: 제일엔지니어링 PMO팀  
**최종 업데이트**: 2025년 12월 8일
