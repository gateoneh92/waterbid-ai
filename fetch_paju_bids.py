import json
import math
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
import requests

# ==============================================================================
# [설정 영역] 아버지 회사 실제 스펙을 입력해 주세요 (단위: 원)
# ==============================================================================
COMPANY_CONFIG = {
    "name": "드림건설",
    "main_field": "상하수도설비공사",
    "capacity_amount": 1_850_000_000,   # 1. 시공능력평가액 (예: 18억 5,000만 원)
    "perf_3yr_amount": 1_420_000_000,   # 2. 최근 3년 상하수도 시공실적 합계
    "credit_grade": "BBB",              # 3. 경영상태 신용등급 (A, BBB, BB0, BB-, B, CCC)
    "search_days_back": 14,             # 최근 14일간 공고 조회
}

RAW_KEY = os.environ.get("G2B_SERVICE_KEY", "").strip()
SERVICE_KEY = unquote(RAW_KEY)

BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService02"
SEARCH_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkPPSSrch02"
BASIS_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkBasisAmount02"

KST = timezone(timedelta(hours=9))
SESSION = requests.Session()

CREDIT_GRADE_RATIO = {
    "A": 1.00,      # A- 이상
    "BBB": 1.00,    # BBB+ ~ BBB-
    "BB0": 1.00,    # BB+ ~ BB0 (전문공사 만점 기준)
    "BB-": 0.98,    # BB- (98% 인정)
    "B": 0.95,      # B+ ~ B- (95% 인정)
    "CCC": 0.90,    # CCC+ 이하 (90% 인정)
}


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
        res = SESSION.get(BASIS_ENDPOINT, params=params, timeout=6)
        payload = safe_parse_g2b_response(res)
        items = normalize_items(payload)
        if items:
            return parse_number(items[0].get("bssamt"), 0)
    except Exception as e:
        print(f"[참고] 기초금액 조회 생략 ({bid_no}-{bid_ord}): {e}")
    return 0


def query_g2b_region_chunk(start_dt: str, end_dt: str, official_region: str) -> list:
    collected = []
    page_no = 1
    num_of_rows = 300

    while page_no <= 5:
        params = {
            "serviceKey": SERVICE_KEY,
            "type": "json",
            "numOfRows": str(num_of_rows),
            "pageNo": str(page_no),
            "inqryDiv": "1",
            "inqryBgnDt": start_dt,
            "inqryEndDt": end_dt,
            "prtcptPsblRgnNm": official_region,
        }
        res = SESSION.get(SEARCH_ENDPOINT, params=params, timeout=12)
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


def evaluate_qualification(presmpt_price: int, base_price: int, lower_rate: float, contract_method: str, title: str) -> dict:
    capacity = COMPANY_CONFIG["capacity_amount"]
    perf_3yr = COMPANY_CONFIG["perf_3yr_amount"]
    grade = COMPANY_CONFIG.get("credit_grade", "BBB")
    mgmt_ratio = CREDIT_GRADE_RATIO.get(grade, 1.0)

    within_capacity = base_price <= capacity
    capacity_margin = capacity - base_price
    est_price = presmpt_price if presmpt_price > 0 else round(base_price / 1.1)

    is_small_quote = (est_price < 200_000_000) and ("수의" in contract_method or "견적" in title or est_price < 100_000_000)
    if is_small_quote:
        return {
            "withinCapacity": within_capacity,
            "capacityMargin": capacity_margin,
            "evalTier": "소액수의 (적격심사 생략)",
            "maxCapScore": 0.0,
            "earnedCapScore": 0.0,
            "expDetail": "실적심사 없음",
            "mgmtDetail": "경영상태심사 없음",
            "deficit": 0.0,
            "minPassBidRate": lower_rate,
            "qualPass": within_capacity,
            "scoreNote": "적격심사 생략 · 견적경쟁" if within_capacity else "시공능력 한도 초과",
        }

    if est_price < 200_000_000:
        tier_name = "적격심사 (2억 미만)"
        max_exp, max_mgmt, perf_mult, price_coeff = 0.0, 10.0, 0.0, 20.0
    elif est_price < 300_000_000:
        tier_name = "적격심사 (2억~3억)"
        max_exp, max_mgmt, perf_mult, price_coeff = 5.0, 5.0, 0.5, 20.0
    elif est_price < 1_000_000_000:
        tier_name = "적격심사 (3억~10억)"
        mult = 0.5 if est_price < 400_000_000 else 1.0
        max_exp, max_mgmt, perf_mult, price_coeff = 10.0, 10.0, mult, 20.0
    else:
        tier_name = "적격심사 (10억~50억)"
        max_exp, max_mgmt, perf_mult, price_coeff = 15.0, 15.0, 2.0, 4.0

    if max_exp == 0:
        earned_exp = 0.0
        exp_detail = "해당없음"
    else:
        req_perf = max(base_price * perf_mult, 1)
        ratio = perf_3yr / req_perf
        if ratio >= 1.0:
            exp_factor = 1.0
        elif ratio >= 0.7:
            exp_factor = 0.9
        elif ratio >= 0.4:
            exp_factor = 0.8
        elif ratio >= 0.2:
            exp_factor = 0.
