<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>파주 상하수도 맞춤형 입찰 분석 시스템</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    body { font-family: 'Pretendard', sans-serif; background-color: #f1f5f9; }
    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      height: 20px; width: 20px; border-radius: 50%;
      background: #2563eb; cursor: pointer; box-shadow: 0 2px 6px rgba(37,99,235,0.4);
    }
  </style>
</head>
<body class="text-slate-800">

  <!-- 상단 헤더 -->
  <header class="bg-slate-900 text-white shadow-md">
    <div class="max-w-7xl mx-auto px-4 py-4 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span id="statusBadge" class="bg-emerald-500 text-slate-950 text-xs font-extrabold px-2 py-0.5 rounded">LIVE 연동</span>
          <h1 class="text-lg md:text-xl font-bold tracking-tight">파주 상하수도 스마트 입찰 지원 시스템</h1>
        </div>
        <p id="lastUpdatedText" class="text-xs text-slate-400 mt-1">나라장터(G2B) 데이터 불러오는 중...</p>
      </div>

      <!-- 우리 회사 스펙 요약 + 설정 열기 버튼 -->
      <div class="bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs flex flex-wrap items-center gap-x-4 gap-y-1.5">
        <div><span class="text-slate-400">업체명:</span> <strong id="companyName" class="text-white">드림건설</strong></div>
        <div><span class="text-slate-400">시공능력:</span> <strong id="companyCap" class="text-emerald-400">18억 5,000만 원</strong></div>
        <div><span class="text-slate-400">3년실적:</span> <strong id="companyPerf" class="text-blue-300">14억 2,000만 원</strong></div>
        <div><span class="text-slate-400">신용등급:</span> <strong id="companyCredit" class="text-amber-300">BBB0</strong></div>
        <button type="button" onclick="toggleSpecPanel()"
          class="ml-auto bg-blue-600 hover:bg-blue-500 text-white font-bold px-2.5 py-1 rounded-lg transition">
          ⚙️ 회사 스펙 입력
        </button>
      </div>
    </div>

    <!-- 접이식 우리 회사 실제 스펙 입력 패널 -->
    <div id="specPanel" class="hidden bg-slate-800 border-t border-slate-700">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-bold text-white">🏢 우리 회사 실제 스펙 입력 (적격심사 및 투찰 한도 실시간 재계산)</h2>
          <button type="button" onclick="resetCompanySpecs()" class="text-xs text-slate-400 hover:text-white underline">
            기본값으로 초기화
          </button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
          <div>
            <label class="block text-slate-300 mb-1">업체명</label>
            <input type="text" id="inputCompName" value="드림건설"
              class="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white font-semibold" />
          </div>
          <div>
            <label class="block text-slate-300 mb-1">시공능력평가액 (원)</label>
            <input type="text" id="inputCompCap" value="1,850,000,000"
              class="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-emerald-300 font-bold text-right" />
          </div>
          <div>
            <label class="block text-slate-300 mb-1">최근 3년 상하수도 실적 (원)</label>
            <input type="text" id="inputCompPerf" value="1,420,000,000"
              class="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-blue-300 font-bold text-right" />
          </div>
          <div>
            <label class="block text-slate-300 mb-1">경영상태 신용등급</label>
            <select id="inputCompCredit"
              class="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-amber-300 font-bold">
              <option value="A">A- 이상 (만점)</option>
              <option value="BBB" selected>BBB+ ~ BBB- (만점)</option>
              <option value="BB0">BB+ ~ BB0 (만점)</option>
              <option value="BB-">BB- (98% 인정 · 소폭감점)</option>
              <option value="B">B+ ~ B- (95% 인정 · 감점)</option>
              <option value="CCC">CCC+ 이하 (90% 인정)</option>
            </select>
          </div>
          <div class="flex items-end">
            <button type="button" onclick="saveCompanySpecs()"
              class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold py-2 px-4 rounded-lg transition">
              저장 및 전체 재판정 ✓
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- 안내 알림 배너 -->
  <div id="fallbackBanner" class="hidden bg-amber-100 border-b border-amber-300 text-amber-950 text-xs py-2.5 px-4 text-center font-medium">
    현재는 <strong>시연용 샘플 공고</strong>가 표시되고 있습니다. GitHub Actions에서 <code>파주 상하수도 공고 자동 수집</code>을 실행하면 실제 나라장터 공고로 전환됩니다.
  </div>

  <!-- 메인 대시보드 -->
  <main class="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- 좌측: 공고 리스트 (5컬럼) -->
    <section class="lg:col-span-5 flex flex-col gap-4">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-bold text-base text-slate-900">📋 파주·경기 상하수도 공고</h2>
          <label class="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 cursor-pointer">
            <input type="checkbox" id="filterEligible" class="rounded text-blue-600 focus:ring-blue-500" />
            참가·통과 가능만 보기
          </label>
        </div>

        <div class="mb-3">
          <input type="text" id="searchInput" placeholder="공고명 또는 발주기관 검색 (예: 문산, 파주시청)"
            class="w-full text-xs border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500" />
        </div>

        <div class="grid grid-cols-3 gap-2 mb-4 text-center">
          <div class="bg-blue-50 rounded-lg p-2">
            <div class="text-xs text-blue-600 font-medium">전체 수집</div>
            <div id="countTotal" class="text-lg font-extrabold text-blue-900">0건</div>
          </div>
          <div class="bg-emerald-50 rounded-lg p-2">
            <div class="text-xs text-emerald-600 font-medium">통과 유력</div>
            <div id="countEligible" class="text-lg font-extrabold text-emerald-800">0건</div>
          </div>
          <div class="bg-slate-100 rounded-lg p-2">
            <div class="text-xs text-slate-500 font-medium">제외·기타</div>
            <div id="countExcluded" class="text-lg font-extrabold text-slate-600">0건</div>
          </div>
        </div>

        <div id="bidList" class="space-y-2.5 max-h-[650px] overflow-y-auto pr-1"></div>
      </div>
    </section>

    <!-- 우측: 적격심사 상세 진단 & 투찰가 계산기 (7컬럼) -->
    <section class="lg:col-span-7 space-y-5">

      <!-- 1. 공고 상세 & 적격심사·투찰한도 진단 카드 -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div class="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
          <div class="flex-1 min-w-[220px]">
            <div class="flex flex-wrap items-center gap-2 mb-1.5">
              <span id="detailBadge" class="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">-</span>
              <span id="detailAgency" class="text-xs font-semibold text-slate-500">-</span>
              <span id="detailBidNo" class="text-[11px] font-mono text-slate-400"></span>
            </div>
            <h2 id="detailTitle" class="text-lg font-bold text-slate-900 leading-snug">공고를 선택해 주세요</h2>
          </div>
          <div class="flex flex-col items-end gap-1.5">
            <div class="text-right">
              <span class="text-[11px] text-slate-400 block">투찰 마감일시</span>
              <span id="detailDeadline" class="text-sm font-bold text-rose-600">-</span>
            </div>
            <a id="detailUrl" href="https://www.g2b.go.kr" target="_blank" rel="noopener noreferrer"
              class="inline-flex items-center gap-1 text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 px-3 py-1.5 rounded-lg transition">
              나라장터 공고원문 ↗
            </a>
          </div>
        </div>

        <!-- 적격심사 & 시공능력 정밀 진단 박스 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <div class="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <div class="text-[11px] text-slate-500 mb-0.5">시공능력 한도 진단</div>
            <div id="detailCapStatus" class="text-sm font-extrabold text-slate-900">-</div>
            <div id="detailCapMargin" class="text-[11px] text-slate-500 mt-0.5">-</div>
          </div>
          <div class="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <div class="text-[11px] text-slate-500 mb-0.5">수행능력 예상점수</div>
            <div id="detailQualScore" class="text-sm font-extrabold text-blue-700">-</div>
            <div id="detailQualBreakdown" class="text-[11px] text-slate-500 mt-0.5">-</div>
          </div>
          <div class="bg-emerald-50 rounded-lg p-3 border border-emerald-200">
            <div class="text-[11px] text-emerald-700 mb-0.5">적격통과 최소 투찰율</div>
            <div id="detailMinPassRate" class="text-sm font-extrabold text-emerald-900">-</div>
            <div id="detailDeficitNote" class="text-[11px] text-emerald-700 mt-0.5">-</div>
          </div>
        </div>

        <div class="bg-blue-50/70 border border-blue-100 rounded-lg p-3 text-xs text-slate-700 space-y-1">
          <div class="font-bold text-blue-900">📌 공고 및 심사 핵심 요약</div>
          <p id="detailSummary" class="whitespace-pre-line leading-relaxed">-</p>
        </div>
      </div>

      <!-- 2. 투찰가 계산기 -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div class="flex flex-wrap items-center justify-between gap-2 mb-4">
          <h3 class="font-bold text-base text-slate-900">🎯 적격심사 반영 투찰금액 계산기</h3>
          <span id="basePriceStatusBadge" class="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
            확정 기초금액 반영됨
          </span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">기초금액 (원)</label>
            <input type="text" id="basePriceInput" value="200,000,000"
              class="w-full font-bold text-right text-base border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500" />
          </div>
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-semibold text-slate-600">적용 투찰하한율 (%)</label>
              <button type="button" id="applyPassRateBtn" onclick="applyMinPassRate()"
                class="text-[11px] font-bold text-blue-600 hover:underline">
                적격통과 하한율 적용
              </button>
            </div>
            <input type="number" id="lowerRateInput" step="0.001" value="89.745"
              class="w-full font-bold text-right text-base border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500" />
          </div>
        </div>

        <div class="bg-slate-50 rounded-xl p-4 border border-slate-200 mb-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold text-slate-700">목표 사정률 조절</span>
            <div class="flex items-center gap-1">
              <input type="number" id="rateNumberInput" step="0.005" min="97" max="103" value="100.150"
                class="w-24 text-right font-extrabold text-blue-700 text-lg bg-white border border-blue-300 rounded px-2 py-0.5" />
              <span class="font-bold text-blue-700">%</span>
            </div>
          </div>

          <input type="range" id="rateSlider" min="97.000" max="103.000" step="0.005" value="100.150"
            class="w-full h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer my-2" />

          <div class="flex justify-between text-[11px] text-slate-400 mb-3">
            <span>97.0% (-3%)</span>
            <span>100.0% (기초금액)</span>
            <span>103.0% (+3%)</span>
          </div>

          <div class="flex flex-wrap gap-2">
            <button type="button" onclick="setRate(99.850)" class="text-xs bg-white hover:bg-slate-100 border border-slate-300 rounded-md px-2.5 py-1 font-medium">
              보수적 (99.850%)
            </button>
            <button type="button" onclick="setRate(100.150)" class="text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md px-2.5 py-1 font-semibold">
              지자체 평균권 (100.150%)
            </button>
            <button type="button" onclick="setRate(100.400)" class="text-xs bg-white hover:bg-slate-100 border border-slate-300 rounded-md px-2.5 py-1 font-medium">
              상향 투찰 (100.400%)
            </button>
          </div>
        </div>

        <div class="bg-slate-900 text-white rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div class="text-xs text-slate-400">예상 예정가격: <span id="expectedPriceText" class="text-slate-200 font-semibold">0원</span></div>
            <div class="text-xs text-blue-300 mt-1 font-semibold">최종 권장 투찰금액 (원 단위 절상)</div>
            <div id="finalBidText" class="text-2xl sm:text-3xl font-extrabold text-emerald-400 tracking-tight mt-0.5">
              0 원
            </div>
          </div>
          <button type="button" onclick="copyBidPrice()" id="copyBtn"
            class="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-sm px-4 py-3 rounded-lg transition shrink-0">
            투찰금액 복사하기
          </button>
        </div>
      </div>

      <!-- 3. 복수예가 15개 가상 추첨 시뮬레이션 -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div>
            <h3 class="font-bold text-sm text-slate-900">🎲 나라장터 복수예가 15개 가상 추첨 체험</h3>
            <p class="text-xs text-slate-500">기초금액 ±3% 범위 내 15개 예비가격 중 4개 추첨 평균을 시뮬레이션합니다.</p>
          </div>
          <button type="button" onclick="runLottery()"
            class="bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold px-3.5 py-2 rounded-lg transition">
            15개 생성 및 4개 추첨
          </button>
        </div>

        <div id="lotteryGrid" class="grid grid-cols-5 gap-2 text-center text-xs my-3"></div>
        <div id="lotteryResult" class="hidden bg-indigo-50 border border-indigo-200 rounded-lg p-3 flex items-center justify-between text-xs">
          <div>
            <span class="text-indigo-900 font-semibold">추첨된 4개 평균 사정률: </span>
            <strong id="drawnAvgText" class="text-indigo-700 text-sm">100.120%</strong>
          </div>
          <button type="button" onclick="applyDrawnRate()" class="bg-indigo-600 text-white font-bold px-3 py-1.5 rounded hover:bg-indigo-700">
            이 사정률로 투찰가 계산
          </button>
        </div>
      </div>

    </section>
  </main>

  <script>
    const STORAGE_KEY = "dream_bid_company_specs_v1";
    const CREDIT_RATIO = { A: 1.0, BBB: 1.0, BB0: 1.0, "BB-": 0.98, B: 0.95, CCC: 0.90 };

    let defaultCompany = {
      name: "드림건설",
      capacity_amount: 1850000000,
      perf_3yr_amount: 1420000000,
      credit_grade: "BBB"
    };

    let currentCompany = { ...defaultCompany };
    let allBids = [];
    let selectedBid = null;
    let lastDrawnRate = 100.120;

    const fallbackBids = [
      {
        id: "SAMPLE-001",
        bidNo: "20261117001-00",
        title: "[샘플] 문산읍 선유리 일원 노후 상수관로 정비공사",
        agency: "파주시청 상하수도과",
        region: "경기도 파주시",
        mainField: "상하수도설비공사",
        presmptPrice: 258636363,
        basePrice: 284500000,
        isEstimatedBase: false,
        lowerRate: 89.745,
        contractMethod: "제한경쟁",
        deadline: "2026-11-24 10:00",
        url: "https://www.g2b.go.kr",
        isWater: true
      }
    ];

    function formatNum(num) {
      return Math.round(num).toLocaleString('ko-KR');
    }

    function parseNum(str) {
      return Number(String(str).replace(/[^0-9.-]/g, '')) || 0;
    }

    function formatKoreanUnit(won) {
      const sign = won < 0 ? "-" : "";
      const absWon = Math.abs(won);
      const eok = Math.floor(absWon / 100000000);
      const man = Math.round((absWon % 100000000) / 10000);
      if (eok > 0 && man > 0) return `${sign}${eok}억 ${man.toLocaleString()}만 원`;
      if (eok > 0) return `${sign}${eok}억 원`;
      return `${sign}${man.toLocaleString()}만 원`;
    }

    // 클라이언트 측 적격심사 & 투찰한도 실시간 재계산 엔진
    function evaluateBidClient(bid) {
      const cap = currentCompany.capacity_amount;
      const perf = currentCompany.perf_3yr_amount;
      const grade = currentCompany.credit_grade;
      const mgmtRatio = CREDIT_RATIO[grade] || 1.0;

      const basePrice = bid.basePrice || 0;
      const estPrice = bid.presmptPrice > 0 ? bid.presmptPrice : Math.round(basePrice / 1.1);
      const lowerRate = bid.lowerRate || (estPrice < 1000000000 ? 89.745 : 88.745);
      const contractMethod = bid.contractMethod || bid.method || "";

      const withinCapacity = basePrice <= cap;
      const capacityMargin = cap - basePrice;

      const isSmallQuote = (estPrice < 200000000) && (
        contractMethod.includes("수의") || bid.title.includes("견적") || estPrice < 100000000
      );

      let qual = {};
      if (isSmallQuote) {
        qual = {
          withinCapacity,
          capacityMargin,
          evalTier: "소액수의 (적격심사 생략)",
          maxCapScore: 0,
          earnedCapScore: 0,
          expDetail: "실적심사 없음",
          mgmtDetail: "경영상태심사 없음",
          deficit: 0,
          minPassBidRate: lowerRate,
          qualPass: withinCapacity,
          scoreNote: withinCapacity ? "적격심사 생략 · 견적경쟁" : "시공능력 한도 초과"
        };
      } else {
        let tierName, maxExp, maxMgmt, perfMult, priceCoeff;
        if (estPrice < 200000000) {
          tierName = "적격심사 (2억 미만)";
          [maxExp, maxMgmt, perfMult, priceCoeff] = [0, 10, 0, 20];
        } else if (estPrice < 300000000) {
          tierName = "적격심사 (2억~3억)";
          [maxExp, maxMgmt, perfMult, priceCoeff] = [5, 5, 0.5, 20];
        } else if (estPrice < 1000000000) {
          tierName = "적격심사 (3억~10억)";
          [maxExp, maxMgmt, perfMult, priceCoeff] = [10, 10, estPrice < 400000000 ? 0.5 : 1.0, 20];
        } else {
          tierName = "적격심사 (10억~50억)";
          [maxExp, maxMgmt, perfMult, priceCoeff] = [15, 15, 2.0, 4];
        }

        let earnedExp = 0;
        let expDetail = "해당없음";
        if (maxExp > 0) {
          const reqPerf = Math.max(basePrice * perfMult, 1);
          const ratio = perf / reqPerf;
          const factor = ratio >= 1.0 ? 1.0 : ratio >= 0.7 ? 0.9 : ratio >= 0.4 ? 0.8 : ratio >= 0.2 ? 0.7 : 0.6;
          earnedExp = Number((maxExp * factor).toFixed(2));
          expDetail = `${earnedExp}/${maxExp}점 (기준실적 대비 ${Math.min(Math.round(ratio * 100), 999)}%)`;
        }

        const earnedMgmt = Number((maxMgmt * mgmtRatio).toFixed(2));
        const mgmtDetail = `${earnedMgmt}/${maxMgmt}점 (${grade}등급)`;
        const maxCap = Number((maxExp + maxMgmt).toFixed(2));
        const earnedCap = Number((earnedExp + earnedMgmt).toFixed(2));
        const deficit = Number((maxCap - earnedCap).toFixed(2));

        let minPassRate, qualPass, scoreNote;
        if (deficit > 5.0) {
          minPassRate = 90.000;
          qualPass = false;
          scoreNote = `수행능력 ${earnedCap}/${maxCap}점 (점수미달 불가)`;
        } else {
          minPassRate = Number((lowerRate + deficit / priceCoeff).toFixed(3));
          qualPass = withinCapacity;
          scoreNote = deficit === 0
            ? `수행능력 ${earnedCap}/${maxCap}점 만점 (하한율 통과)`
            : `수행능력 ${earnedCap}/${maxCap}점 (-${deficit}점 → ${minPassRate}% 이상)`;
        }

        qual = {
          withinCapacity,
          capacityMargin,
          evalTier: tierName,
          maxCapScore: maxCap,
          earnedCapScore: earnedCap,
          expDetail,
          mgmtDetail,
          deficit,
          minPassBidRate: minPassRate,
          qualPass,
          scoreNote
        };
      }

      const eligible = bid.isWater && qual.withinCapacity && qual.qualPass;
      let badge, badgeColor;
      if (!bid.isWater) {
        badge = "파주 기타공사";
        badgeColor = "bg-slate-200 text-slate-600";
      } else if (!qual.withinCapacity) {
        badge = "시공능력 초과";
        badgeColor = "bg-rose-100 text-rose-700";
      } else if (!qual.qualPass) {
        badge = "적격점수 미달";
        badgeColor = "bg-rose-100 text-rose-700";
      } else if (qual.evalTier.includes("소액수의")) {
        badge = "상하수도 · 소액수의";
        badgeColor = "bg-blue-100 text-blue-800";
      } else if (qual.deficit > 0) {
        badge = "상하수도 · 투찰상향";
        badgeColor = "bg-amber-100 text-amber-800";
      } else {
        badge = "상하수도 · 추천";
        badgeColor = "bg-emerald-100 text-emerald-800";
      }

      const summary = [
        `• 발주처: ${bid.agency} / 계약방법: ${contractMethod}`,
        `• 참가가능지역: ${bid.region} / 주력분야: ${bid.mainField}`,
        `• 심사구분: ${qual.evalTier} | 시공경험: ${qual.expDetail} | 경영상태: ${qual.mgmtDetail}`,
        bid.isEstimatedBase ? "• ※ 아직 확정 기초금액이 공개되지 않아 추정가격(×1.1) 기준으로 계산기에 세팅되었습니다." : ""
      ].filter(Boolean).join("\n");

      return { ...bid, qual, eligible, badge, badgeColor, summary };
    }

    function updateCompanyHeaderUI() {
      document.getElementById('companyName').textContent = currentCompany.name;
      document.getElementById('companyCap').textContent = formatKoreanUnit(currentCompany.capacity_amount);
      document.getElementById('companyPerf').textContent = formatKoreanUnit(currentCompany.perf_3yr_amount);
      document.getElementById('companyCredit').textContent = currentCompany.credit_grade;

      document.getElementById('inputCompName').value = currentCompany.name;
      document.getElementById('inputCompCap').value = formatNum(currentCompany.capacity_amount);
      document.getElementById('inputCompPerf').value = formatNum(currentCompany.perf_3yr_amount);
      document.getElementById('inputCompCredit').value = currentCompany.credit_grade;
    }

    function toggleSpecPanel() {
      document.getElementById('specPanel').classList.toggle('hidden');
    }

    function saveCompanySpecs() {
      currentCompany = {
        name: document.getElementById('inputCompName').value.trim() || "드림건설",
        capacity_amount: parseNum(document.getElementById('inputCompCap').value),
        perf_3yr_amount: parseNum(document.getElementById('inputCompPerf').value),
        credit_grade: document.getElementById('inputCompCredit').value
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentCompany));
      updateCompanyHeaderUI();
      recalculateAllBids();
      document.getElementById('specPanel').classList.add('hidden');
    }

    function resetCompanySpecs() {
      localStorage.removeItem(STORAGE_KEY);
      currentCompany = { ...defaultCompany };
      updateCompanyHeaderUI();
      recalculateAllBids();
    }

    function recalculateAllBids() {
      allBids = allBids.map(evaluateBidClient);
      allBids.sort((a, b) => (b.eligible - a.eligible) || (b.isWater - a.isWater) || b.bidNo.localeCompare(a.bidNo));
      updateCounters();
      renderBidList();
      if (selectedBid) {
        const refreshed = allBids.find(b => b.id === selectedBid.id) || allBids[0];
        if (refreshed) selectBid(refreshed.id);
      } else if (allBids.length > 0) {
        selectBid(allBids[0].id);
      }
    }

    async function initDashboard() {
      try {
        const res = await fetch(`./paju_bids.json?t=${Date.now()}`);
        if (!res.ok) throw new Error("JSON 없음");
        const data = await res.json();

        allBids = Array.isArray(data.bids) ? data.bids : [];
        document.getElementById('lastUpdatedText').textContent =
          `최근 자동 수집: ${data.updated_at || '방금 전'} (경기·파주 ${data.total_scanned || 0}건 스캔 완료)`;

        if (data.company) {
          defaultCompany = {
            name: data.company.name || "드림건설",
            capacity_amount: data.company.capacity_amount || 1850000000,
            perf_3yr_amount: data.company.perf_3yr_amount || 1420000000,
            credit_grade: (data.company.credit_grade || "BBB").replace(/[0+-]/g, '') || "BBB"
          };
        }
      } catch (err) {
        allBids = fallbackBids;
        document.getElementById('statusBadge').textContent = '샘플 모드';
        document.getElementById('statusBadge').className = 'bg-amber-400 text-slate-950 text-xs font-extrabold px-2 py-0.5 rounded';
        document.getElementById('lastUpdatedText').textContent = 'paju_bids.json 대기 중 (GitHub Actions 실행 필요)';
        document.getElementById('fallbackBanner').classList.remove('hidden');
      }

      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        try {
          currentCompany = { ...defaultCompany, ...JSON.parse(saved) };
        } catch (e) {
          currentCompany = { ...defaultCompany };
        }
      } else {
        currentCompany = { ...defaultCompany };
      }

      updateCompanyHeaderUI();
      recalculateAllBids();
      runLottery();
    }

    function updateCounters() {
      const eligibleCnt = allBids.filter(b => b.eligible).length;
      document.getElementById('countTotal').textContent = `${allBids.length}건`;
      document.getElementById('countEligible').textContent = `${eligibleCnt}건`;
      document.getElementById('countExcluded').textContent = `${allBids.length - eligibleCnt}건`;
    }

    function renderBidList() {
      const hideIneligible = document.getElementById('filterEligible').checked;
      const keyword = document.getElementById('searchInput').value.trim().toLowerCase();
      const listEl = document.getElementById('bidList');
      listEl.innerHTML = '';

      const filtered = allBids.filter(bid => {
        if (hideIneligible && !bid.eligible) return false;
        if (keyword && !(`${bid.title} ${bid.agency} ${bid.region}`.toLowerCase().includes(keyword))) return false;
        return true;
      });

      if (filtered.length === 0) {
        listEl.innerHTML = `
          <div class="text-center py-10 text-xs text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            조건에 일치하는 공고가 없습니다.
          </div>`;
        return;
      }

      filtered.forEach(bid => {
        const isSelected = selectedBid && bid.id === selectedBid.id;
        const card = document.createElement('div');
        card.className = `p-3.5 rounded-xl border transition cursor-pointer ${
          isSelected
            ? 'border-blue-600 bg-blue-50/40 ring-2 ring-blue-500/20'
            : bid.eligible
              ? 'border-slate-200 hover:border-blue-300 bg-white'
              : 'border-slate-200 bg-slate-50 opacity-65'
        }`;
        card.onclick = () => selectBid(bid.id);

        const priceLabel = bid.isEstimatedBase ? '추정환산' : '기초금액';
        card.innerHTML = `
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-[11px] font-bold px-2 py-0.5 rounded ${bid.badgeColor}">${bid.badge}</span>
            <span class="text-[11px] text-slate-400 font-medium truncate max-w-[140px]">${bid.agency}</span>
          </div>
          <div class="font-bold text-sm text-slate-900 mb-1.5 leading-snug">${bid.title}</div>
          <div class="flex items-center justify-between text-xs text-slate-600">
            <span>${priceLabel}: <strong class="text-slate-900">${formatNum(bid.basePrice)}원</strong></span>
            <span class="text-rose-600 font-semibold">${(bid.deadline || '').slice(5, 16)}</span>
          </div>
        `;
        listEl.appendChild(card);
      });
    }

    function selectBid(id) {
      selectedBid = allBids.find(b => b.id === id);
      if (!selectedBid) return;
      renderBidList();

      const q = selectedBid.qual;
      document.getElementById('detailBadge').className = `text-xs font-bold px-2 py-0.5 rounded ${selectedBid.badgeColor}`;
      document.getElementById('detailBadge').textContent = selectedBid.badge;
      document.getElementById('detailAgency').textContent = selectedBid.agency;
      document.getElementById('detailBidNo').textContent = selectedBid.bidNo ? `(${selectedBid.bidNo})` : '';
      document.getElementById('detailTitle').textContent = selectedBid.title;
      document.getElementById('detailDeadline').textContent = selectedBid.deadline;
      document.getElementById('detailUrl').href = selectedBid.url || 'https://www.g2b.go.kr';
      document.getElementById('detailSummary').textContent = selectedBid.summary;

      // 1) 시공능력 한도 카드
      const capStatusEl = document.getElementById('detailCapStatus');
      if (q.withinCapacity) {
        capStatusEl.textContent = "한도 내 (투찰 가능)";
        capStatusEl.className = "text-sm font-extrabold text-emerald-700";
        document.getElementById('detailCapMargin').textContent = `잔여 여력: +${formatKoreanUnit(q.capacityMargin)}`;
      } else {
        capStatusEl.textContent = "시공능력 한도 초과";
        capStatusEl.className = "text-sm font-extrabold text-rose-600";
        document.getElementById('detailCapMargin').textContent = `초과액: ${formatKoreanUnit(q.capacityMargin)}`;
      }

      // 2) 수행능력 예상점수 카드
      if (q.maxCapScore === 0) {
        document.getElementById('detailQualScore').textContent = "적격심사 생략 (소액수의)";
        document.getElementById('detailQualBreakdown').textContent = "실적·경영상태 점수 미평가";
      } else {
        document.getElementById('detailQualScore').textContent = `${q.earnedCapScore} / ${q.maxCapScore}점`;
        document.getElementById('detailQualBreakdown').textContent = `경험 ${q.expDetail.split(' ')[0]} · 경영 ${q.mgmtDetail.split(' ')[0]}`;
      }

      // 3) 적격통과 최소 투찰율 카드
      const minPassEl = document.getElementById('detailMinPassRate');
      if (!q.qualPass && q.deficit > 5) {
        minPassEl.textContent = "점수 미달 (통과 불가)";
        minPassEl.className = "text-sm font-extrabold text-rose-600";
        document.getElementById('detailDeficitNote').textContent = `수행능력 -${q.deficit}점 감점 초과`;
      } else {
        minPassEl.textContent = `${q.minPassBidRate.toFixed(3)}% 이상`;
        minPassEl.className = "text-sm font-extrabold text-emerald-900";
        document.getElementById('detailDeficitNote').textContent =
          q.deficit > 0 ? `감점 -${q.deficit}점 보완 상향 적용` : `기본 하한율(${selectedBid.lowerRate}%) 통과`;
      }

      const baseBadge = document.getElementById('basePriceStatusBadge');
      if (selectedBid.isEstimatedBase) {
        baseBadge.textContent = '기초금액 미공개 (추정가격×1.1 자동환산)';
        baseBadge.className = 'text-xs font-semibold text-amber-800 bg-amber-100 px-2.5 py-1 rounded-full';
      } else {
        baseBadge.textContent = '나라장터 확정 기초금액 반영됨';
        baseBadge.className = 'text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full';
      }

      document.getElementById('basePriceInput').value = formatNum(selectedBid.basePrice);
      document.getElementById('lowerRateInput').value = q.minPassBidRate.toFixed(3);
      calculateBid();
    }

    function applyMinPassRate() {
      if (!selectedBid) return;
      document.getElementById('lowerRateInput').value = selectedBid.qual.minPassBidRate.toFixed(3);
      calculateBid();
    }

    function calculateBid() {
      const basePrice = parseNum(document.getElementById('basePriceInput').value);
      const lowerRate = parseFloat(document.getElementById('lowerRateInput').value) || 0;
      const rate = parseFloat(document.getElementById('rateNumberInput').value) || 100;

      const expectedPrice = Math.round(basePrice * (rate / 100));
      const finalBid = Math.ceil(expectedPrice * (lowerRate / 100));

      document.getElementById('expectedPriceText').textContent = `${formatNum(expectedPrice)}원`;
      document.getElementById('finalBidText').textContent = `${formatNum(finalBid)} 원`;
    }

    function setRate(val) {
      const fixed = Number(val).toFixed(3);
      document.getElementById('rateSlider').value = fixed;
      document.getElementById('rateNumberInput').value = fixed;
      calculateBid();
    }

    function runLottery() {
      const rates = [];
      for (let i = 0; i < 15; i++) {
        const offset = -3 + (i * (6 / 14)) + ((Math.random() - 0.5) * 0.25);
        rates.push(100 + offset);
      }
      const indices = [...Array(15).keys()].sort(() => Math.random() - 0.5);
      const picked = new Set(indices.slice(0, 4));

      let sum = 0;
      const grid = document.getElementById('lotteryGrid');
      grid.innerHTML = '';

      rates.forEach((r, idx) => {
        const isPicked = picked.has(idx);
        if (isPicked) sum += r;
        const box = document.createElement('div');
        box.className = `py-2 px-1 rounded border font-mono ${
          isPicked
            ? 'bg-indigo-600 text-white border-indigo-700 font-bold shadow-sm'
            : 'bg-slate-50 text-slate-500 border-slate-200'
        }`;
        box.innerHTML = `<div class="text-[10px] opacity-75">#${idx + 1}</div><div>${r.toFixed(3)}%</div>`;
        grid.appendChild(box);
      });

      lastDrawnRate = sum / 4;
      document.getElementById('drawnAvgText').textContent = `${lastDrawnRate.toFixed(3)}%`;
      document.getElementById('lotteryResult').classList.remove('hidden');
    }

    function applyDrawnRate() {
      setRate(lastDrawnRate);
    }

    function copyBidPrice() {
      const raw = parseNum(document.getElementById('finalBidText').textContent);
      navigator.clipboard.writeText(String(raw));
      const btn = document.getElementById('copyBtn');
      btn.textContent = '복사 완료! ✓';
      setTimeout(() => btn.textContent = '투찰금액 복사하기', 1500);
    }

    ['inputCompCap', 'inputCompPerf'].forEach(id => {
      document.getElementById(id).addEventListener('input', (e) => {
        const num = parseNum(e.target.value);
        e.target.value = num ? formatNum(num) : '';
      });
    });

    document.getElementById('filterEligible').addEventListener('change', renderBidList);
    document.getElementById('searchInput').addEventListener('input', renderBidList);
    document.getElementById('basePriceInput').addEventListener('input', (e) => {
      const num = parseNum(e.target.value);
      e.target.value = num ? formatNum(num) : '';
      calculateBid();
    });
    document.getElementById('lowerRateInput').addEventListener('input', calculateBid);
    document.getElementById('rateSlider').addEventListener('input', (e) => {
      document.getElementById('rateNumberInput').value = Number(e.target.value).toFixed(3);
      calculateBid();
    });
    document.getElementById('rateNumberInput').addEventListener('input', (e) => {
      document.getElementById('rateSlider').value = e.target.value;
      calculateBid();
    });

    initDashboard();
  </script>
</body>
</html>
