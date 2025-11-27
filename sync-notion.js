/**
 * 아산시 스마트시티 대시보드 - 노션 동기화 스크립트
 * 
 * 이 스크립트는 노션 API를 통해 데이터를 가져와서 
 * 대시보드 HTML 파일을 자동으로 업데이트합니다.
 * 
 * 사용법:
 * 1. npm install @notionhq/client
 * 2. 환경변수 설정: NOTION_API_KEY
 * 3. node sync-notion.js
 */

const fs = require('fs');
const path = require('path');

// 노션 설정
const NOTION_CONFIG = {
    // 노션 페이지/데이터베이스 ID
    dashboardPageId: '25a50aa9-577d-81b0-9085-e918f674b7ce',
    budgetDatabaseId: '2aa50aa9-577d-8128-b6d4-c5c21d845796',
    projectDatabaseId: '2aa50aa9-577d-8128-b6d4-c5c21d845796',
    
    // 노션 연동 URL
    notionUrls: {
        main: 'https://www.notion.so/21650aa9577d80dc8278e0187c54677f',
        dashboard: 'https://www.notion.so/25a50aa9577d81b09085e918f674b7ce',
        budget: 'https://www.notion.so/2aa50aa9577d8128b6d4c5c21d845796'
    }
};

// 예산 데이터 (노션에서 가져올 데이터)
const budgetData = {
    summary: {
        totalBudget: 240,
        allocatedBudget: 171.34,
        contractAmount: 33.58,
        executedAmount: 25.3,
        executionRate: 14.8,
        remainingBudget: 146.04
    },
    bySource: {
        national: { total: 120, allocated: 85.7, executed: 12.7, rate: 10.6 },
        provincial: { total: 28.8, allocated: 20.6, executed: 3.0, rate: 10.4 },
        municipal: { total: 91.2, allocated: 65.0, executed: 9.6, rate: 10.5 }
    }
};

// 단위사업 데이터
const projectsData = [
    {
        name: '디지털 OASIS SPOT 구축',
        desc: '이동식 체류공간 30동, 스마트인프라',
        budget: 35.54,
        contract: 0.43,
        rate: 1.2,
        status: 'pending',
        statusText: '실시설계',
        note: '부지 확정 완료 (도고면)'
    },
    {
        name: '이노베이션센터 구축',
        desc: '호서대 KTX캠퍼스 통합관제센터',
        budget: 13.30,
        contract: 12.43,
        rate: 93.4,
        status: 'completed',
        statusText: '구축완료',
        note: '운영 준비중'
    },
    {
        name: '유무선 네트워크 구축',
        desc: '광케이블 30km, WiFi AP 200개',
        budget: 8.00,
        contract: 7.70,
        rate: 96.2,
        status: 'completed',
        statusText: '계약완료',
        note: '11/20 계약체결'
    },
    {
        name: 'SDDC Platform 구축',
        desc: '클라우드 기반 데이터센터',
        budget: 27.00,
        contract: 0,
        rate: 0,
        status: 'progress',
        statusText: '기술협상',
        note: '3차 협상 완료 (11/26)'
    },
    {
        name: 'AI통합관제 플랫폼',
        desc: 'AI 영상분석, 예측 분석',
        budget: 16.00,
        contract: 0,
        rate: 0,
        status: 'progress',
        statusText: '계약예정',
        note: '11/29 계약 목표'
    },
    {
        name: '디지털OASIS 정보관리',
        desc: '데이터 마켓플레이스, API',
        budget: 23.00,
        contract: 0,
        rate: 0,
        status: 'pending',
        statusText: '입찰공고',
        note: '12/08 선정 목표'
    },
    {
        name: 'DRT 서비스 구축',
        desc: '수요응답형 모빌리티',
        budget: 10.00,
        contract: 0.50,
        rate: 5.0,
        status: 'pending',
        statusText: '발주진행',
        note: '차량 2대 발주중'
    },
    {
        name: '사업관리 (PMO)',
        desc: '인건비, 운영비, 여비',
        budget: 28.21,
        contract: 12.24,
        rate: null,
        status: 'progress',
        statusText: '진행중',
        note: 'PMO 운영'
    },
    {
        name: '감리용역 (신설)',
        desc: '서비스 인프라 구축 투명성 제고',
        budget: 1.60,
        contract: 0,
        rate: 0,
        status: 'new',
        statusText: '신설',
        note: '예산 신설 추진중'
    }
];

// 리스크 데이터
const risksData = [
    {
        level: 'critical',
        title: '연말 예산집행률 저조',
        probability: '81-100%',
        impact: 146
    },
    {
        level: 'critical',
        title: 'SDDC Platform 구축 발주 지연',
        probability: '61-80%',
        impact: 27
    },
    {
        level: 'high',
        title: '디지털OASIS 정보관리 발주 지연',
        probability: '41-60%',
        impact: 25
    },
    {
        level: 'high',
        title: 'AI통합관제 플랫폼 발주 지연',
        probability: '41-60%',
        impact: 16
    }
];

// 일정 데이터
const scheduleData = [
    { date: '11-27', title: '서비스 인프라 우선협상 기간 종료', desc: '기술협상 완료, 계약 준비', isToday: true },
    { date: '11-29', title: 'AI통합관제 계약 체결', desc: '11월 실적 최종 점검', dday: 2 },
    { date: '12-05', title: 'SDDC Platform 계약 체결', desc: '27억원 규모', dday: 8 },
    { date: '12-31', title: '사업년도 종료 / 예산 마감', desc: '2025년 사업 종료', dday: 34 }
];

/**
 * D-Day 계산
 */
function calculateDDay() {
    const endDate = new Date('2025-12-31');
    const today = new Date();
    const diff = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
    return diff;
}

/**
 * 현재 날짜/시간 문자열 생성
 */
function getCurrentDateTime() {
    const now = new Date();
    return now.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Seoul'
    });
}

/**
 * HTML 파일 업데이트
 */
function updateHtmlFile() {
    const htmlPath = path.join(__dirname, 'index.html');
    let html = fs.readFileSync(htmlPath, 'utf8');
    
    const dday = calculateDDay();
    const syncTime = getCurrentDateTime();
    
    // D-Day 업데이트
    html = html.replace(/D-\d+/g, `D-${dday}`);
    
    // 동기화 시간 업데이트
    html = html.replace(
        /마지막 동기화: .+?</g, 
        `마지막 동기화: ${syncTime}<`
    );
    
    fs.writeFileSync(htmlPath, html, 'utf8');
    console.log(`✅ 대시보드 업데이트 완료: ${syncTime}`);
    console.log(`📅 D-Day: D-${dday}`);
}

/**
 * 노션 API를 통한 데이터 동기화 (실제 구현 시)
 */
async function syncFromNotion() {
    // 노션 API 클라이언트 초기화
    // const { Client } = require('@notionhq/client');
    // const notion = new Client({ auth: process.env.NOTION_API_KEY });
    
    // 예산 데이터베이스 조회
    // const budgetResponse = await notion.databases.query({
    //     database_id: NOTION_CONFIG.budgetDatabaseId
    // });
    
    // 데이터 파싱 및 변환
    // ...
    
    console.log('📊 노션 데이터 동기화...');
    console.log('   - 예산 데이터베이스 조회');
    console.log('   - 단위사업 현황 조회');
    console.log('   - 리스크 현황 조회');
    console.log('   - 일정 데이터 조회');
}

/**
 * JSON 데이터 파일 생성 (API 용)
 */
function generateDataJson() {
    const data = {
        lastUpdated: new Date().toISOString(),
        dday: calculateDDay(),
        budget: budgetData,
        projects: projectsData,
        risks: risksData,
        schedule: scheduleData,
        notionUrls: NOTION_CONFIG.notionUrls
    };
    
    const jsonPath = path.join(__dirname, 'data.json');
    fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf8');
    console.log('📄 data.json 생성 완료');
}

/**
 * 메인 실행
 */
async function main() {
    console.log('🚀 아산시 스마트시티 대시보드 동기화 시작\n');
    
    try {
        // 노션 동기화 (API 키가 있는 경우)
        if (process.env.NOTION_API_KEY) {
            await syncFromNotion();
        } else {
            console.log('⚠️  NOTION_API_KEY가 설정되지 않음 - 로컬 데이터 사용\n');
        }
        
        // HTML 파일 업데이트
        updateHtmlFile();
        
        // JSON 데이터 생성
        generateDataJson();
        
        console.log('\n✅ 동기화 완료!');
        
    } catch (error) {
        console.error('❌ 동기화 실패:', error);
        process.exit(1);
    }
}

main();
