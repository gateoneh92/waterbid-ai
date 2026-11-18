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
    "search_days_back": 14,             # 진행 공고 게시일 기준 조회 기간 (일)
    "max_history_days": 730,            # 과거 개찰결과 최대 학습 기간 (2년 = 730일)
    "history_batch_days": 365,          # 1회 실행당 과거 역추적 수집 폭 (1년 = 365일)
}

SERVICE_KEY = unquote(os.environ.get("G2B_SERVICE_KEY", "").strip())
BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService02"
SCSBID_URL = "https://apis.data.go.kr/1230000/as/ScsbidInfoService"
LIST_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwk02"
BASIS_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoCnstwkBasisAmount02"
LICENSE_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoLicenseLimit02"
REGION_ENDPOINT = f"{BASE_URL}/getBidPblancListInfoPrtcptPsblRgn02"
OPENING_ENDPOINT = f"{SCSBID_URL}/getOpengResultListInfoCnstwk"
KST = timezone(timedelta(hours=9))

PAJU_KEYWORDS = (
    "파주", "문산읍", "파주 문산", "운정", "금촌", "교하", "조리읍", "법원읍",
    "광탄면", "탄현면", "월롱면", "적성면", "파평면", "장단면",
    "야당동", "와동동", "목동동", "동패동", "다율동", "금릉동", "금릉역", "봉일천", "파주출판"
)

GYEONGGI_KEYWORDS = (
    "경기도", "수원시", "고양시", "용인시", "성남시", "화성시", "부천시", "남양주시", "안산시",
    "평택시", "안양시", "시흥시", "김포시", "의정부시", "광주시", "하남시", "광명시", "군포시",
    "양주시", "오산시", "이천시", "안성시", "구리시", "의왕시", "포천시", "양평군", "여주시",
    "동두천시", "과천시", "가평군", "연천군"
)

OTHER_PROVINCE_KEYWORDS = (
    "광주지방조달청", "광주광역시", "광주전남", "서울특별시", "인천광역시",
    "강원", "충청", "충북", "충남", "대전광역시", "세종",
    "전라", "전북", "전남", "여수", "순천", "목포", "광양", "나주", "무안", "해남", "영암", "화순",
    "경상", "경북", "경남", "대구광역시", "울산광역시", "부산광역시", "창원", "진주", "포항", "구미", "제주"
)

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

RE_NORMALIZE = re.compile(r"[ㆍ·,\s]")
RE_SPLIT_REGION = re.compile(r"[,/]")
RE_NON_DIGIT = re.compile(r"\D")


def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.6, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16))
    return session


SESSION = create_session()


def normalize_text(text: str) -> str:
    return RE_NORMALIZE.sub("", str(text or ""))


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


def fetch_all_pages(endpoint: str, extra_params: dict, max_pages: int = 20) -> list:
    rows = 500
    try:
        items, total = fetch_page(endpoint, extra_params, 1, rows)
    except Exception as e:
        print(f"[경고] 조회 실패 ({endpoint.split('/')[-1]}): {e}")
        return []

    if total <= rows or not items:
        return items

    total_pages = min(math.ceil(total / rows), max_pages)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch_page, endpoint, extra_params, p, rows) for p in range(2, total_pages + 1)]
        for fut in as_completed(futures):
            try:
                items.extend(fut.result()[0])
            except Exception:
                pass
    return items


def fetch_basis_only(bid_no: str, bid_ord: str = "000") -> int:
    """개찰결과에 기초금액이 누락된 경우 기초금액 API에서 단건 조회합니다."""
    params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "inqryDiv": "2",
        "bidNtceNo": bid_no,
        "bidNtceOrd": bid_ord,
        "numOfRows": "5",
        "pageNo": "1",
    }
    try:
        b_items = extract_items(parse_g2b_json(SESSION.get(BASIS_ENDPOINT, params=params, timeout=8)))
        if b_items:
            return parse_num(b_items[0].get("bssamt"))
    except Exception:
        pass
    return 0


def fetch_bid_details(bid_no: str, bid_ord: str) -> tuple[int, int, str, str]:
    """개별 공고의 기초금액, A값 합계, 참가가능지역, 업종제한사항을 조회합니다."""
    base_params = {
        "serviceKey": SERVICE_KEY,
        "type": "json",
        "inqryDiv": "2",
        "bidNtceNo": bid_no,
        "bidNtceOrd": bid_ord,
        "numOfRows": "10",
        "pageNo": "1",
    }
    basis, a_val = 0, 0
    regions, licenses = [], []

    try:
        b_items = extract_items(parse_g2b_json(SESSION.get(BASIS_ENDPOINT, params=base_params, timeout=8)))
        if b_items:
            row = b_items[0]
            basis = parse_num(row.get("bssamt"))
            a_val = sum(max(parse_num(row.get(f)), 0) for f in A_VALUE_FIELDS)
    except Exception:
        pass

    try:
        r_items = extract_items(parse_g2b_json(SESSION.get(REGION_ENDPOINT, params=base_params, timeout=8)))
        for r in r_items:
            reg = str(r.get("prtcptPsblRgnNm") or "").strip()
            if reg and reg not in regions:
                regions.append(reg)
    except Exception:
        pass

    try:
        l_items = extract_items(parse_g2b_json(SESSION.get(LICENSE_ENDPOINT, params=base_params, timeout=8)))
        for r in l_items:
            lic = str(r.get("lcnsLmtNm") or "").strip()
            if lic and lic not in licenses:
                licenses.append(lic)
    except Exception:
        pass

    return basis, a_val, ", ".join(regions), ", ".join(licenses)


def update_historical_bids(now_kst: datetime):
    """
    과거 개찰결과를 최대 2년(730일)까지 자동 역추적 수집·누적합니다.
    - 1회차 실행: 최근 1년(0~365일) 일괄 수집
    - 2회차 실행: 과거 1~2년(365~730일) 이어받기 완료 (최대 2,000건 학습)
    - 이후 실행: 최근 14일 신규 개찰결과만 빠르게 증분 업데이트
    """
    existing = {}
    fetched_days_depth = 0
    if os.path.exists("historical_bids.json"):
        try:
            with open("historical_bids.json", "r", encoding="utf-8") as f:
                saved = json.load(f)
                fetched_days_depth = int(saved.get("fetched_days_depth", 0))
                for rec in saved.get("records", []):
                    if rec.get("bidNo"):
                        existing[rec["bidNo"]] = rec
        except Exception:
            pass

    max_days = COMPANY_CONFIG["max_history_days"]
    batch_days = COMPANY_CONFIG["history_batch_days"]
    chunk_days = 15

    # 1) API 활성 여부 사전 점검 (미신청 시 불필요한 대량 호출 방지)
    probe_start = (now_kst - timedelta(days=7)).strftime("%Y%m%d0000")
    probe_end = now_kst.strftime("%Y%m%d2359")
    try:
        probe_items, _ = fetch_page(OPENING_ENDPOINT, {"inqryBgnDt": probe_start, "inqryEndDt": probe_end}, 1, 50)
    except Exception as e:
        print(f"[안내] 낙찰정보 API 미연동 상태로 개찰 자동학습을 건너뜁니다: {e}")
        if not os.path.exists("historical_bids.json"):
            with open("historical_bids.json", "w", encoding="utf-8") as f:
                json.dump({"updated_at": now_kst.strftime("%Y-%m-%d %H:%M"), "fetched_days_depth": 0, "records": []}, f, ensure_ascii=False, indent=2)
        return

    # 2) 조회 구간 설정: 항상 최근 14일 + 아직 안 긁어온 과거 구간(1년 단위 최대 2년)
    ranges = [(0, 14)]
    next_depth = fetched_days_depth
    if fetched_days_depth < max_days:
        back_start = max(fetched_days_depth, 14)
        back_end = min(fetched_days_depth + batch_days, max_days)
        if back_end > back_start:
            ranges.append((back_start, back_end))
            next_depth = back_end

    chunks = []
    for r_start, r_end in ranges:
        for offset in range(r_start, r_end, chunk_days):
            s = (now_kst - timedelta(days=min(offset + chunk_days - 1, r_end))).strftime("%Y%m%d0000")
            e = (now_kst - timedelta(days=offset)).strftime("%Y%m%d2359")
            chunks.append((s, e))

    raw_openings = list(probe_items)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(fetch_all_pages, OPENING_ENDPOINT, {"inqryBgnDt": s, "inqryEndDt": e}, 15)
            for s, e in chunks
        ]
        for fut in as_completed(futures):
            raw_openings.extend(fut.result())

    candidates = {}
    for it in raw_openings:
        b_no = str(it.get("bidNtceNo", "")).strip()
        if not b_no or b_no in existing:
            continue

        title = str(it.get("bidNtceNm", ""))
        agency = str(it.get("dminsttNm") or it.get("ntceInsttNm") or "")
        loc_text = f"{title} {agency}"
        norm_title = normalize_text(title)

        if any(op in loc_text for op in OTHER_PROVINCE_KEYWORDS):
            continue
        if not any(kw in loc_text for kw in PAJU_KEYWORDS + GYEONGGI_KEYWORDS):
            continue
        if not any(wk in norm_title for wk in WATER_KEYWORDS):
            continue

        plan_amt = parse_num(it.get("plnprc"))
        if plan_amt <= 0:
            continue

        candidates[b_no] = {
            "bidNo": b_no,
            "bidOrd": str(it.get("bidNtceOrd") or "000").strip(),
            "agency": agency,
            "title": title,
            "basePrice": parse_num(it.get("bssamt")),
            "planPrice": plan_amt,
            "openedAt": str(it.get("opengDt") or ""),
        }

    # 개찰결과에 기초금액(bssamt)이 빠진 건은 기초금액 API에서 보완 조회
    missing_basis = [c for c in candidates.values() if c["basePrice"] <= 0]
    if missing_basis:
        with ThreadPoolExecutor(max_workers=6) as pool:
            fut_to_no = {
                pool.submit(fetch_basis_only, c["bidNo"], c["bidOrd"]): c["bidNo"]
                for c in missing_basis
            }
            for fut in as_completed(fut_to_no):
                b_no = fut_to_no[fut]
                candidates[b_no]["basePrice"] = fut.result()

    added_cnt = 0
    for b_no, c in candidates.items():
        base_amt = c["basePrice"]
        plan_amt = c["planPrice"]
        if base_amt > 0 and plan_amt > 0:
            rate = round((plan_amt / base_amt) * 100, 4)
            if 96.5 <= rate <= 103.5:
                existing[b_no] = {
                    "bidNo": b_no,
                    "agency": c["agency"],
                    "title": c["title"],
                    "basePrice": base_amt,
                    "planPrice": plan_amt,
                    "rate": rate,
                    "openedAt": c["openedAt"],
                    "source": "나라장터자동수집",
                }
                added_cnt += 1

    records = sorted(
        existing.values(),
        key=lambda x: (x.get("openedAt", ""), x.get("bidNo", "")),
        reverse=True,
    )[:2000]

    with open("historical_bids.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": now_kst.strftime("%Y-%m-%d %H:%M"),
            "fetched_days_depth": next_depth,
            "records": records,
        }, f, ensure_ascii=False, indent=2)

    print(
        f"[개찰학습 누적깊이 {next_depth}/{max_days}일] 개찰 스캔 {len(raw_openings)}건 -> "
        f"신규 {added_cnt}건 추가 (총 학습표본 {len(records)}건)"
    )


def is_region_allowed_for_paju(region_str: str) -> bool:
    r = str(region_str or "").strip()
    if not r or r in ("공고문 참조", "제한없음"):
        return True
    if any(other in r for other in OTHER_PROVINCE_KEYWORDS):
        return False
    return any(
        ("전국" in tok or "파주" in tok or tok in ("경기도", "경기"))
        for tok in (t.strip() for t in RE_SPLIT_REGION.split(r) if t.strip())
    )


def is_closed(deadline_str: str, now_kst: datetime) -> bool:
    digits = RE_NON_DIGIT.sub("", str(deadline_str or ""))
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
            (now_kst - timedelta(days=min(offset + 3, days))).strftime("%Y%m%d0000"),
            (now_kst - timedelta(days=offset)).strftime("%Y%m%d2359"),
        )
        for offset in range(0, days, 4)
    ]

    raw_map = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch_all_pages, LIST_ENDPOINT, {"inqryBgnDt": s, "inqryEndDt": e}, 20) for s, e in chunks]
        for fut in as_completed(futures):
            for item in fut.result():
                b_no = str(item.get("bidNtceNo", "")).strip()
                b_ord = str(item.get("bidNtceOrd", "000")).strip()
                if b_no and (b_no not in raw_map or b_ord >= str(raw_map[b_no].get("bidNtceOrd", "000"))):
                    raw_map[b_no] = item

    preliminary = []
    for b_no, item in raw_map.items():
        title = str(item.get("bidNtceNm", "제목 없음"))
        loc_text = " ".join(
            str(item.get(k, "")) for k in ("bidNtceNm", "ntceInsttNm", "dminsttNm", "prtcptPsblRgnNm", "cnstrtsiteRgnNm")
        )
        field_text = " ".join(
            str(item.get(k, "")) for k in ("indstrytyMfrcFldNm", "pubPrcrmntClsfcNm", "lcnsLmtNm")
        )
        norm_work = normalize_text(f"{title} {field_text}")

        is_paju_local = any(kw in loc_text for kw in PAJU_KEYWORDS)
        if not is_paju_local and any(op in loc_text for op in OTHER_PROVINCE_KEYWORDS):
            continue

        has_water_signal = ("상하수도" in norm_work) or any(w in norm_work for w in WATER_KEYWORDS)
        if is_paju_local or has_water_signal:
            closed = is_closed(item.get("bidClseDt", ""), now_kst)
            preliminary.append((b_no, item, closed, is_paju_local))

    open_prelim = [(b_no, it) for b_no, it, closed, _ in preliminary if not closed]
    detail_map = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        fut_to_no = {
            pool.submit(fetch_bid_details, b_no, str(it.get("bidNtceOrd") or "000").strip()): b_no
            for b_no, it in open_prelim
        }
        for fut in as_completed(fut_to_no):
            detail_map[fut_to_no[fut]] = fut.result()

    bids = []
    for b_no, item, closed, is_paju_local in preliminary:
        b_ord = str(item.get("bidNtceOrd") or "000").strip()
        full_id = f"{b_no}-{b_ord}"
        title = str(item.get("bidNtceNm", "제목 없음"))
        agency = item.get("dminsttNm") or item.get("ntceInsttNm") or "발주처 미상"

        basis, a_val, lic_region, lic_trade = detail_map.get(b_no, (0, 0, "", ""))
        region = lic_region or str(item.get("prtcptPsblRgnNm") or "").strip() or "공고문 참조"
        main_field = lic_trade or " ".join(
            str(item.get(k, "")) for k in ("indstrytyMfrcFldNm", "pubPrcrmntClsfcNm", "lcnsLmtNm")
        ).strip() or "공고문 확인"

        loc_all = f"{title} {agency} {region} {item.get('cnstrtsiteRgnNm', '')}"
        norm_work_all = normalize_text(f"{title} {main_field}")
        norm_field = normalize_text(main_field)

        if not is_paju_local and any(op in loc_all for op in OTHER_PROVINCE_KEYWORDS):
            continue

        is_gyeonggi_ok = is_paju_local or any(kw in loc_all for kw in GYEONGGI_KEYWORDS)
        region_allowed = is_region_allowed_for_paju(region)
        is_water = ("상하수도" in norm_work_all) or (
            any(w in norm_work_all for w in WATER_KEYWORDS) and not any(ot in norm_field for ot in OTHER_TRADE_KEYWORDS)
        )

        if not is_paju_local and not (is_gyeonggi_ok and region_allowed and is_water):
            continue

        presmpt = parse_num(item.get("presmptPrce"))
        is_est_base = basis <= 0
        default_lower = 89.745 if presmpt < 1_000_000_000 else 88.745
        lower_rate = parse_num(item.get("sucsfbidLwltRate"), as_float=True, default=default_lower) or default_lower

        bids.append({
            "id": full_id,
            "bidNo": full_id,
            "title": title,
            "agency": agency,
            "region": region,
            "mainField": main_field,
            "presmptPrice": presmpt,
            "basePrice": round(presmpt * 1.1) if is_est_base else basis,
            "aValue": a_val,
            "isEstimatedBase": is_est_base,
            "lowerRate": lower_rate,
            "contractMethod": item.get("cntrctCnclsMthdNm") or "입찰방식 확인",
            "deadline": item.get("bidClseDt", "마감일시 확인"),
            "isClosed": closed,
            "url": item.get("bidNtceDtlUrl") or "https://www.g2b.go.kr",
            "isWater": is_water,
            "isPajuLocal": is_paju_local,
        })

    bids.sort(key=lambda x: (not x["isClosed"], x["isWater"], x["isPajuLocal"], x["bidNo"]), reverse=True)
    water_cnt = sum(1 for b in bids if b["isWater"])
    open_water_cnt = sum(1 for b in bids if b["isWater"] and not b["isClosed"])

    with open("paju_bids.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": now_kst.strftime("%Y-%m-%d %H:%M"),
            "company": COMPANY_CONFIG,
            "total_scanned": len(raw_map),
            "bids": bids,
        }, f, ensure_ascii=False, indent=2)

    update_historical_bids(now_kst)

    print(
        f"수집 완료 ({time.time() - t0:.1f}초): 전국 {len(raw_map)}건 -> "
        f"파주·경기 대상 {len(bids)}건 (상하수도 {water_cnt}건 / 진행중 {open_water_cnt}건)"
    )


if __name__ == "__main__":
    main()
