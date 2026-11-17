import json
import math
import os
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==============================================================================
# [기본 설정] 아버지 회사 기본 스펙 (웹 화면에서 실시간 변경 가능)
# ==============================================================================
COMPANY_CONFIG = {
    "name": "드림건설",
    "capacity_amount": 1_850_000_000,   # 시공능력평가액 (원)
    "perf_3yr_amount": 1_420_000_000,   # 최근 3년 상하수도 실적 (원)
    "credit_grade": "BBB",              # 신용등급 (A, BBB, BB0, BB-, B, CCC)
    "search_days_back": 14,             # 조회 기간 (일)
}

SERVICE_KEY = unquote(os.environ.get("G2B_SERVICE_KEY", "").strip())
BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService02"
SEARCH_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkPPSSrch02"
BASIS_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkBasisAmount02"
KST = timezone(timedelta(hours=9))

PAJU_KEYWORDS = (
    "파주", "문산", "운정", "금촌", "교하", "조리읍", "법원읍",
    "광탄면", "탄현면", "월롱면", "적성면", "파평면", "장단면",
    "야당동", "와동동", "목동동", "동패동", "다율동", "금릉", "봉일천", "선유리", "출판단지"
)
WATER_KEYWORDS = (
    "상하수도", "상수도", "하수도", "관로", "급수", "배수", "오수", "우수관",
    "우수받이", "맨홀", "송수", "정수장", "누수", "가압장", "관거", "용수로",
    "하수처리", "배수지", "취수", "차집관", "측구", "암거", "집수정",
    "유수율", "제수변", "소화전", "노후관", "오폐수"
)
OTHER_TRADE_KEYWORDS = (
    "전기공사", "정보통신공사", "소방시설공사", "조경식재", "조경시설물",
    "실내건축", "도장공사", "방수공사", "승강기", "기계설비공사"
)


def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10))
    return session


SESSION = create_session()


def parse_num(val, as_float: bool = False, default=0):
    if val in (None, ""):
        return float(default) if as_float else default
    try:
        num = float(str(val).replace(",", "").strip())
        return num if as_float else int(num)
    except ValueError:
        return float(default) if as_float else default


def parse_g2b_json(res: requests.Response) -> dict:
    text = res.text.strip()
    if text.startswith("<"):
        root = ET.fromstring(text)
        code = root.findtext(".//returnReasonCode") or root.findtext(".//resultCode") or "XML_ERR"
        msg = root.findtext(".//returnAuthMsg") or root.findtext(".//resultMsg") or text[:200]
        raise RuntimeError(f"조달청 API 오류 [{code}]: {msg}")

    data = res.json()
    if "nkoneps.com.response.Body" in data:
        err = data["nkoneps.com.response.Body"]
        raise RuntimeError(f"조달청 서버 오류 [{err.get('resultCode')}]: {err.get('resultMsg')}")

    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        raise RuntimeError(f"G2B 응답 오류 [{header.get('resultCode')}]: {header.get('resultMsg')}")
    return data


def extract_items(payload: dict) -> list:
    items = payload.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return []
    return [items] if isinstance(items, dict) else items


def fetch_search_page(start_dt: str, end_dt: str, page_no: int, rows: int = 500) -> tuple[list, int]:
    params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "numOfRows": str(rows),
        "pageNo": str(page_no),
        "inqryDiv": "1",
        "inqryBgnDt": start_dt,
        "inqryEndDt": end_dt,
    }
    payload = parse_g2b_json(SESSION.get(SEARCH_ENDPOINT, params=params, timeout=20))
    total = parse_num(payload.get("response", {}).get("body", {}).get("totalCount"))
    return extract_items(payload), total


def fetch_period_all(start_dt: str, end_dt: str) -> list:
    rows = 500
    items, total = fetch_search_page(start_dt, end_dt, 1, rows)
    if total <= rows or not items:
        return items

    total_pages = min(math.ceil(total / rows), 15)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch_search_page, start_dt, end_dt, p, rows) for p in range(2, total_pages + 1)]
        for fut in as_completed(futures):
            items.extend(fut.result()[0])
    return items


def fetch_basis_amount(bid_no: str, bid_ord: str) -> int:
    params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "inqryDiv": "2",
        "bidNtceNo": bid_no,
        "bidNtceOrd": bid_ord,
        "numOfRows": "1",
        "pageNo": "1",
    }
    try:
        items = extract_items(parse_g2b_json(SESSION.get(BASIS_ENDPOINT, params=params, timeout=8)))
        return parse_num(items[0].get("bssamt")) if items else 0
    except Exception:
        return 0


def is_closed(deadline_str: str, now_kst: datetime) -> bool:
    digits = "".join(ch for ch in str(deadline_str or "") if ch.isdigit())
    try:
        if len(digits) >= 12:
            return datetime.strptime(digits[:12], "%Y%m%d%H%M").replace(tzinfo=KST) < now_kst
        if len(digits) == 8:
            return datetime.strptime(digits + "2359", "%Y%m%d%H%M").replace(tzinfo=KST) < now_kst
    except ValueError:
        pass
    return False


def main():
    t0 = time.time()
    if not SERVICE_KEY:
        raise ValueError("환경변수 G2B_SERVICE_KEY가 비어 있습니다.")

    now_kst = datetime.now(KST)
    days = COMPANY_CONFIG["search_days_back"]
    chunks = [
        (
            (now_kst - timedelta(days=min(offset + 4, days))).strftime("%Y%m%d0000"),
            (now_kst - timedelta(days=offset)).strftime("%Y%m%d2359"),
        )
        for offset in range(0, days, 5)
    ]

    raw_map = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for fut in as_completed([pool.submit(fetch_period_all, s, e) for s, e in chunks]):
            for item in fut.result():
                raw_map[f"{item.get('bidNtceNo')}-{item.get('bidNtceOrd', '000')}"] = item

    # 1차 필터: 파주 관련 공고 추출
    paju_items = []
    for key, item in raw_map.items():
        loc_text = " ".join(
            str(item.get(k, "")) for k in ("bidNtceNm", "ntceInsttNm", "dminsttNm", "prtcptPsblRgnNm", "cnstrtsiteRgnNm")
        )
        if any(kw in loc_text for kw in PAJU_KEYWORDS):
            closed = is_closed(item.get("bidClseDt", ""), now_kst)
            paju_items.append((key, item, closed))

    # 2차 조회: 마감되지 않은 진행 공고만 기초금액 조회 (API 호출 최소화)
    open_items = [(k, it) for k, it, closed in paju_items if not closed]
    basis_map = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        fut_to_key = {
            pool.submit(fetch_basis_amount, it.get("bidNtceNo", ""), it.get("bidNtceOrd", "000")): k
            for k, it in open_items
        }
        for fut in as_completed(fut_to_key):
            basis_map[fut_to_key[fut]] = fut.result()

    # 3차 정제: 프론트엔드용 경량 데이터 구성
    bids = []
    for key, item, closed in paju_items:
        title = str(item.get("bidNtceNm", "제목 없음"))
        field_text = f"{item.get('indstrytyMfrcFldNm', '')} {item.get('pubPrcrmntClsfcNm', '')}".strip()
        work_text = f"{title} {field_text}"

        is_water = ("상하수도" in field_text) or (
            any(w in work_text for w in WATER_KEYWORDS) and not any(ot in field_text for ot in OTHER_TRADE_KEYWORDS)
        )

        presmpt = parse_num(item.get("presmptPrce"))
        basis = basis_map.get(key, 0)
        is_est_base = basis <= 0
        default_lower = 89.745 if presmpt < 1_000_000_000 else 88.745
        lower_rate = parse_num(item.get("sucsfbidLwltRate"), as_float=True, default=default_lower) or default_lower

        bids.append({
            "id": key,
            "bidNo": key,
            "title": title,
            "agency": item.get("dminsttNm") or item.get("ntceInsttNm") or "발주처 미상",
            "region": item.get("prtcptPsblRgnNm") or "공고문 참조",
            "mainField": field_text or "공고문 확인",
            "presmptPrice": presmpt,
            "basePrice": round(presmpt * 1.1) if is_est_base else basis,
            "isEstimatedBase": is_est_base,
            "lowerRate": lower_rate,
            "contractMethod": item.get("cntrctCnclsMthdNm") or "입찰방식 확인",
            "deadline": item.get("bidClseDt", "마감일시 확인"),
            "isClosed": closed,
            "url": item.get("bidNtceDtlUrl") or "https://www.g2b.go.kr",
            "isWater": is_water,
        })

    bids.sort(key=lambda x: (not x["isClosed"], x["isWater"], x["bidNo"]), reverse=True)
    water_cnt = sum(1 for b in bids if b["isWater"])
    open_water_cnt = sum(1 for b in bids if b["isWater"] and not b["isClosed"])

    with open("paju_bids.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": now_kst.strftime("%Y-%m-%d %H:%M"),
            "company": COMPANY_CONFIG,
            "total_scanned": len(raw_map),
            "bids": bids,
        }, f, ensure_ascii=False, indent=2)

    print(
        f"수집 완료 ({time.time() - t0:.1f}초): 전국 {len(raw_map)}건 -> "
        f"파주 {len(bids)}건 (상하수도 {water_cnt}건 / 진행중 {open_water_cnt}건)"
    )


if __name__ == "__main__":
    main()
