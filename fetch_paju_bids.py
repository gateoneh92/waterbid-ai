import json
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
    "search_days_back": 21,             # 최근 21일간 공고 조회 (7일씩 분할 호출)
}

RAW_KEY = os.environ.get("G2B_SERVICE_KEY", "").strip()
SERVICE_KEY = unquote(RAW_KEY)

# 조달청 차세대 나라장터 실제 운영 엔드포인트
BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"
SEARCH_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkPPSSrch"
BASIS_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkBasisAmount"

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
    """조달청 API 응답(JSON 또는 XML 에러)을 안전하게 파싱합니다."""
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

    # 게이트웨이 자체 JSON 오류(response 키가 없는 경우) 방어
    if "response" not in data:
        raise RuntimeError(f"조달청 게이트웨이 응답 오류: {json.dumps(data, ensure_ascii=False)[:300]}")
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


def query_g2b_chunk(start_dt: str, end_dt: str, region_keyword: str) -> list:
    """7일 단위로 나라장터 공사 입찰공고 목록을 조회합니다."""
    params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "numOfRows": "200",
        "pageNo": "1",
        "inqryDiv": "1",
        "inqryBgnDt": start_dt,
        "inqryEndDt": end_dt,
        "prtcptPsblRgnNm": region_keyword,
    }
    res = requests.get(SEARCH_ENDPOINT, params=params, timeout=20)
    payload = safe_parse_g2b_response(res)

    header = payload.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        raise RuntimeError(f"G2B API 오류 [{header.get('resultCode')}]: {header.get('resultMsg')}")

    return normalize_items(payload)


def evaluate_bid(item: dict, basis_amount: int) -> dict:
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
    is_eligible = calc_base_price <= capacity

    if not is_eligible:
        badge = "시공능력 초과 · 제외"
        badge_color = "bg-slate-200 text-slate-600"
        score_note = f"시공능력({capacity // 10000:,}만 원) 초과"
    elif presmpt_price < 200_000_000 and ("수의" in contract_method or "견적" in title):
        badge = "소액수의 · 추천"
        badge_color = "bg-blue-100 text-blue-800"
        score_note = "적격심사 생략 (견적 경쟁)"
    else:
        badge = "참가적합 · 추천"
        badge_color = "bg-emerald-100 text-emerald-800"
        score_note = "시공능력 충족 (공고문 실적확인)"

    summary_parts = [
        f"• 발주처: {agency} / 계약방법: {contract_method}",
        f"• 참가가능지역: {region} / 주력분야: {main_field if main_field else '상하수도설비(공고문 확인)'}",
    ]
    if is_estimated_base:
        summary_parts.append("• ※ 아직 확정 기초금액이 공개되지 않아 추정가격(×1.1) 기준으로 계산기에 자동 세팅되었습니다.")

    return {
        "id": f"{bid_no}-{bid_ord}",
        "bidNo": f"{bid_no}-{bid_ord}",
        "title": title,
        "agency": agency,
        "region": region,
        "mainField": main_field if main_field else "상하수도설비공사",
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
        "badge": badge,
        "badgeColor": badge_color,
        "summary": "\n".join(summary_parts),
    }


def main():
    if not SERVICE_KEY:
        raise ValueError("환경변수 G2B_SERVICE_KEY가 비어 있습니다. GitHub Secrets 이름을 확인하세요.")

    print(f"인증키 로드 완료 (길이: {len(SERVICE_KEY)}자)")
    now_kst = datetime.now(KST)
    total_days = COMPANY_CONFIG["search_days_back"]

    raw_map = {}
    for offset in range(0, total_days, 7):
        chunk_end = now_kst - timedelta(days=offset)
        chunk_start = now_kst - timedelta(days=min(offset + 7, total_days))
        start_str = chunk_start.strftime("%Y%m%d0000")
        end_str = chunk_end.strftime("%Y%m%d2359")
        print(f"조회 구간: {start_str} ~ {end_str}")

        for kw in ["경기", "파주"]:
            for item in query_g2b_chunk(start_str, end_str, kw):
                key = f"{item.get('bidNtceNo')}-{item.get('bidNtceOrd', '000')}"
                raw_map[key] = item

    water_keywords = ["상하수도", "상수도", "하수도", "관로", "급수", "배수관", "오수", "우수", "맨홀", "송수관"]
    matched_bids = []

    for key, item in raw_map.items():
        title = item.get("bidNtceNm", "")
        agency = item.get("ntceInsttNm", "")
        demand = item.get("dminsttNm", "")
        region = item.get("prtcptPsblRgnNm", "")
        site = item.get("cnstrtsiteRgnNm", "")
        main_field = item.get("indstrytyMfrcFldNm", "")

        is_paju = any("파주" in str(t) for t in [region, agency, demand, site, title])
        if not is_paju:
            continue

        is_water = ("상하수도" in str(main_field)) or any(w in str(title) for w in water_keywords)
        if not is_water:
            continue

        basis_amt = get_basis_amount(item.get("bidNtceNo", ""), item.get("bidNtceOrd", "000"))
        matched_bids.append(evaluate_bid(item, basis_amt))

    matched_bids.sort(key=lambda x: x["bidNo"], reverse=True)

    output_data = {
        "updated_at": now_kst.strftime("%Y-%m-%d %H:%M"),
        "company": COMPANY_CONFIG,
        "total_scanned": len(raw_map),
        "bids": matched_bids,
    }

    with open("paju_bids.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"수집 완료: 전체 {len(raw_map)}건 스캔 -> 파주 상하수도 맞춤 공고 {len(matched_bids)}건 저장됨.")


if __name__ == "__main__":
    main()
