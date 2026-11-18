import json
import math
import os
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==============================================================================
# [기본 설정] (주)드림건설 기본 스펙 (웹 화면에서 실시간 변경 가능)
# ==============================================================================
COMPANY_CONFIG = {
    "name": "(주)드림건설",
    "capacity_amount": 701_470_000,     # 시공능력평가액 (7억 147만 원)
    "perf_3yr_amount": 1_281_570_000,   # 최근 3년 상하수도 실적 (12억 8,157만 원)
    "credit_grade": "BBB",              # 신용등급 (A, BBB, BB0, BB-, B, CCC)
    "search_days_back": 14,             # 조회 기간 (일)
}

SERVICE_KEY = unquote(os.environ.get("G2B_SERVICE_KEY", "").strip())
BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService02"
LIST_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwk02"
SEARCH_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkPPSSrch02"
BASIS_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkBasisAmount02"
LICENSE_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoLicenseLimit02"
REGION_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoPrtcptPsblRgn02"
KST = timezone(timedelta(hours=9))

# 파주 고유 지명 (타 지역 동명 지명인 진주 문산면·김천 금릉동 오탐 방지)
PAJU_KEYWORDS = (
    "파주", "문산읍", "파주 문산", "운정", "금촌", "교하", "조리읍", "법원읍",
    "광탄면", "탄현면", "월롱면", "적성면", "파평면", "장단면",
    "야당동", "와동동", "목동동", "동패동", "다율동", "금릉동", "금릉역", "봉일천", "파주출판"
)

# 경기도 시·군 명시 키워드 ('광주지방조달청'·'광주광역시' 오탐 방지를 위해 '광주시'로 명시)
GYEONGGI_KEYWORDS = (
    "경기도", "수원시", "고양시", "용인시", "성남시", "화성시", "부천시", "남양주시", "안산시",
    "평택시", "안양시", "시흥시", "김포시", "의정부시", "광주시", "하남시", "광명시", "군포시",
    "양주시", "오산시", "이천시", "안성시", "구리시", "의왕시", "포천시", "양평군", "여주시",
    "동두천시", "과천시", "가평군", "연천군"
)

# 타 시·도 및 지방조달청 배제 키워드 (광주지방조달청·전남·여수 등 원천 차단)
OTHER_PROVINCE_KEYWORDS = (
    "광주지방조달청", "광주광역시", "광주전남", "서울특별시", "인천광역시",
    "강원", "충청", "충북", "충남", "대전광역시", "세종",
    "전라", "전북", "전남", "여수", "순천", "목포", "광양", "나주", "무안", "해남", "영암", "화순",
    "경상", "경북", "경남", "대구광역시", "울산광역시", "부산광역시", "창원", "진주", "포항", "구미", "제주"
)

# 국방조달(D2B) 연계 공고 식별 키워드
DEFENSE_KEYWORDS = (
    "국방", "국군", "육군", "해군", "공군", "해병", "사령부", "여단", "단장", "대대", "부대", "국방시설"
)

# 상하수도설비공사업 관련 키워드 (준설, 비점오염, 심정, 관정, 지하수 등 보강)
WATER_KEYWORDS = (
    "상하수도", "상수도", "하수도", "상수관", "하수관", "관로", "급수", "배수", "오수", "우수관",
    "우수받이", "맨홀", "송수", "정수장", "누수", "가압장", "관거", "용수로",
    "하수처리", "배수지", "취수", "차집관", "측구", "암거", "집수정",
    "유수율", "제수변", "소화전", "노후관", "오폐수",
    "준설", "비점오염", "심정", "관정", "지하수"
)

OTHER_TRADE_KEYWORDS = (
    "전기공사", "정보통신공사", "소방시설공사", "조경식재", "조경시설물",
    "실내건축", "도장공사", "방수공사", "승강기", "기계설비공사"
)

A_VALUE_FIELDS = (
    "npnInsrprm", "mrfnHealthInsrprm", "odsnLngtrmRcprInsrprm",
    "rtrmzPayDdcAmt", "sftyMngmAmt", "qltyMngmAmt", "sftyChckMngmAmt"
)


def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=12, pool_maxsize=12))
    return session


SESSION = create_session()


def normalize_text(text: str) -> str:
    return re.sub(r"[ㆍ·,\s]", "", str(text or ""))


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
    body = payload.get("response", {}).get("body", {})
    if not isinstance(body, dict):
        return []
    items = body.get("items")
    if not items:
        return []
    if isinstance(items, dict):
        if "item" in items:
            inner = items["item"]
            return inner if isinstance(inner, list) else ([inner] if inner else [])
        return [items]
    return items if isinstance(items, list) else []


def fetch_page(endpoint: str, extra_params: dict, page_no: int, rows: int = 500) -> tuple[list, int]:
    params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "numOfRows": str(rows),
        "pageNo": str(page_no),
        "inqryDiv": "1",
        **extra_params,
    }
    payload = parse_g2b_json(SESSION.get(endpoint, params=params, timeout=20))
    total = parse_num(payload.get("response", {}).get("body", {}).get("totalCount"))
    return extract_items(payload), total


def fetch_all_pages(endpoint: str, extra_params: dict, max_pages
