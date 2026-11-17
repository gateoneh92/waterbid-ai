import json
import math
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
import requests

# ==============================================================================
# [설정 영역] 아버지 회사 스펙에 맞게 숫자를 수정해 주세요 (단위: 원)
# ==============================================================================
COMPANY_CONFIG = {
    "name": "(주)파주상하수도건설",
    "main_field": "상하수도설비공사",
    "capacity_amount": 1_850_000_000,   # 시공능력평가액 (예: 18억 5천만 원)
    "perf_3yr_amount": 1_420_000_000,   # 최근 3년 상하수도 시공실적 합계
    "search_days_back": 25,             # 최근 25일간 공고 조회 (5일씩 분할 호출)
}

RAW_KEY = os.environ.get("G2B_SERVICE_KEY", "").strip()
SERVICE_KEY = unquote(RAW_KEY)

BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService02"
SEARCH_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkPPSSrch02"
BASIS_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkBasisAmount02"

KST = timezone(timedelta(hours=9))


def parse_number(val, default=0):
    if val is None or val == "":
        return default
    try:
        return int(float(str(val).replace(",", "").strip()))
    except ValueError:
        return default


def parse_float(val, default=0.0):
    if val is None or val == "":
        return default
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return default


def safe_parse_g2b_response(res: requests.Response) -> dict:
    raw_text = res.text.strip()
    if raw_text.startswith("<"):
        try:
            root = ET.fromstring(raw_text)
            err_msg = root.findtext(".//returnAuthMsg") or root.findtext(".//resultMsg") or raw_text[:300]
            err_code = root.findtext(".//returnReasonCode") or root.findtext(".//resultCode") or "XML_ERROR"
            raise RuntimeError(f"조달청 API 오류 [{err_code}]: {err_msg}")
        except ET.ParseError:
            raise RuntimeError(f"조달청 API 비정상 응답 (HTTP {res.status_code}): {raw_text[:300]}")
    try:
        data = res.json()
    except Exception:
        raise RuntimeError(f"JSON 파싱 실패 (HTTP {res.status_code}): {raw_text[:300]}")

    if "nkoneps.com.response.Body" in data:
        err_body = data["nkoneps.com.response.Body"]
        raise RuntimeError(f"조달청 서버 오류 [{err_body.get('resultCode')}]: {err_body.get('resultMsg')}")

    if "response" not in data:
        raise RuntimeError(f"예상치 못한 응답 형식: {json.dumps(data, ensure_ascii=False)[:300]}")

    return data


def normalize_items(payload: dict) -> list:
    body = payload.get("response", {}).get("body", {})
    if not body or not isinstance(body, dict):
        return []
    items = body.get("items", [])
    if not items:
        return []
    if isinstance(items, dict):
        return [items]
    return items


def get_basis_amount(bid_no: str, bid_ord: str) -> int:
    """공고번호로 확정 기초금액(bssamt)을 조회합니다."""
    params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "inqryDiv": "2",
        "bidNtceNo": bid_no,
        "bidNtceOrd": bid_ord,
        "numOfRows": "10",
        "pageNo": "1",
    }
    try:
        res = requests.get(BASIS_ENDPOINT, params=params, timeout=10)
        payload = safe_parse_g2b_response(res)
        items = normalize_items(payload)
        if items:
            return parse_number(items[0].get("bssamt"), 0)
    except Exception as e:
        print(f"[참고] 기초금액 조회 생략 ({bid_no}-{bid_ord}): {e}")
    return 0


def query_g2b_all_pages(start_dt: str, end_dt: str) -> list:
    """지역 파라미터 제한 없이 해당 기간의 전체 공사 공고를 페이지 끝까지 수집합니다."""
    collected = []
    page_no = 1
    num_of_rows = 500

    while page_no <= 15:
        params = {
            "serviceKey": SERVICE_KEY,
            "type": "json",
            "numOfRows": str(num_of_rows),
            "pageNo": str(page_no),
            "inqryDiv": "1",
            "inqryBgnDt": start_dt,
            "inqryEndDt": end_dt,
        }
        res = requests.get(SEARCH_ENDPOINT, params=params, timeout=25)
        payload = safe_parse_g2b_response(res)

        header = payload.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            raise RuntimeError(f"G2B API 오류 [{header.get('resultCode')}]: {header.get('resultMsg')}")

        body = payload.get("response", {}).get("body", {})
        total_count = parse_number(body.get("totalCount"), 0)
        items = normalize_items(payload)
        collected.extend(items)

        total_pages = math.ceil(total_count / num_of_rows) if total_count > 0 else 1
        if page_no >= total_pages or not items:
            break
        page_no += 1

    return collected


def evaluate_bid(item: dict, basis_amount: int, is_water: bool) -> dict:
    bid_no = item.get("bidNtceNo", "")
    bid_ord = item.get("bidNtceOrd", "000")
    title = item.get("bidNtceNm", "제목 없음")
    agency = item.get("dminsttNm") or item.get("ntceInsttNm") or "발주처 미상"
    region = item.get("prtcptPsblRgnNm") or "지역제한 정보없음"
    main_field = item.get("indstrytyMfrcFldNm") or ""
    contract_method = item.get("cntrctCnclsMthdNm") or "입찰방식 확인"
    bid_method = item.get("sucsfbidMthdNm") or contract_method

    presmpt_price = parse_number(item.get("presmptPrce"), 0)
    lower_rate = parse_float(item.get("sucsfbidLwltRate"), 87.745)
    if lower_rate <= 0:
        lower_rate = 87.745

    is_estimated_base = basis_amount <= 0
    calc_base_price = round(presmpt_price * 1.1) if is_estimated_base else basis_amount

    capacity = COMPANY_CONFIG["capacity_amount"]
    within_capacity = calc_base_price <= capacity

    # 상하수도 공고이면서 시공능력 이내인 건을 '참가적합(eligible)'으로 최상단 노출
    is_eligible = is_water and within_capacity

    if not is_water:
        badge = "파주 기타공사"
        badge_color = "bg-slate-200 text-slate-600"
        score_note = "타 업종 공고 (상하수도 외)"
    elif not within_capacity:
        badge = "시공능력 초과"
        badge_color = "bg-rose-100 text-rose-700"
        score_note = f"시공능력({capacity // 10000:,}만 원) 초과"
    elif presmpt_price < 200_000_000 and ("수의" in contract_method or "견적" in title):
        badge = "상하수도 · 소액수의"
        badge_color = "bg-blue-100 text-blue-800"
        score_note = "적격심사 생략 (견적 경쟁)"
    else:
        badge = "상하수도 · 추천"
        badge_color = "bg-emerald-100 text-emerald-800"
        score_note = "시공능력 충족 (공고문 실적확인)"

    summary_parts = [
        f"• 발주처: {agency} / 계약방법: {contract_method}",
        f"• 참가가능지역: {region} / 주력분야: {main_field if main_field else '공고문 면허제한 확인'}",
    ]
    if is_estimated_base:
        summary_parts.append("• ※ 아직 확정 기초금액이 공개되지 않아 추정가격(×1.1) 기준으로 계산기에 자동 세팅되었습니다.")

    return {
        "id": f"{bid_no}-{bid_ord}",
        "bidNo": f"{bid_no}-{bid_ord}",
        "title": title,
        "agency": agency,
        "region": region,
        "mainField": main_field if main_field else "공고문 확인",
        "presmptPrice": presmpt_price,
        "basePrice": calc_base_price,
        "isEstimatedBase": is_estimated_base,
        "lowerRate": lower_rate,
        "method": f"{bid_method} ({lower_rate}%)",
        "score": score_note,
        "noticeDate": item.get("bidNtceDt", ""),
        "deadline": item.get("bidClseDt", "마감일시 확인"),
        "openDate": item.get("opengDt", ""),
        "url": item.get("bidNtceDtlUrl") or "https://www.g2b.go.kr",
        "eligible": is_eligible,
        "isWater": is_water,
        "badge": badge,
        "badgeColor": badge_color,
        "summary": "\n".join(summary_parts),
    }


def main():
    if not SERVICE_KEY:
        raise ValueError("환경변수 G2B_SERVICE_KEY가 비어 있습니다.")

    now_kst = datetime.now(KST)
    total_days = COMPANY_CONFIG["search_days_back"]

    raw_map = {}
    for offset in range(0, total_days, 5):
        chunk_end = now_kst - timedelta(days=offset)
        chunk_start = now_kst - timedelta(days=min(offset + 4, total_days))
        start_str = chunk_start.strftime("%Y%m%d0000")
        end_str = chunk_end.strftime("%Y%m%d2359")

        chunk_items = query_g2b_all_pages(start_str, end_str)
        print(f"조회 구간 {start_str} ~ {end_str}: {len(chunk_items)}건 수신")
        for item in chunk_items:
            key = f"{item.get('bidNtceNo')}-{item.get('bidNtceOrd', '000')}"
            raw_map[key] = item

    water_keywords = [
        "상하수도", "상수도", "하수도", "관로", "급수", "배수", "오수", "우수",
        "맨홀", "송수", "정수", "누수", "펌프", "가압장", "관거", "용수로", "하수처리"
    ]
    matched_bids = []

    for key, item in raw_map.items():
        title = item.get("bidNtceNm", "")
        agency = item.get("ntceInsttNm", "")
        demand = item.get("dminsttNm", "")
        region = item.get("prtcptPsblRgnNm", "")
        site = item.get("cnstrtsiteRgnNm", "")
        main_field = item.get("indstrytyMfrcFldNm", "")

        # 파주시 관련 공고인지 확인
        is_paju = any("파주" in str(t) for t in [region, agency, demand, site, title])
        if not is_paju:
            continue

        # 상하수도 관련 공고인지 판별
        is_water = ("상하수도" in str(main_field)) or any(w in str(title) for w in water_keywords)

        basis_amt = get_basis_amount(item.get("bidNtceNo", ""), item.get("bidNtceOrd", "000"))
        matched_bids.append(evaluate_bid(item, basis_amt, is_water))

    # 1순위: 상하수도 적합 공고 -> 2순위: 상하수도 초과 공고 -> 3순위: 파주 기타공사 -> 최신순
    matched_bids.sort(
        key=lambda x: (x["eligible"], x["isWater"], x["bidNo"]),
        reverse=True
    )

    water_cnt = sum(1 for b in matched_bids if b["isWater"])
    output_data = {
        "updated_at": now_kst.strftime("%Y-%m-%d %H:%M"),
        "company": COMPANY_CONFIG,
        "total_scanned": len(raw_map),
        "bids": matched_bids,
    }

    with open("paju_bids.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"수집 완료: 전국 {len(raw_map)}건 스캔 -> 파주 전체 {len(matched_bids)}건 (상하수도 {water_cnt}건) 저장됨.")


if __name__ == "__main__":
    main()
