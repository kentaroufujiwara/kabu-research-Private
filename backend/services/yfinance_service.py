"""
stooq.com を使って日本株データを取得するサービス。
Yahoo Finance への依存を完全に排除。
"""

import io
import csv
import datetime
import requests
from cache import cached

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

_session = requests.Session()
_session.headers.update(_HEADERS)


class NotFoundError(Exception):
    pass


class RateLimitError(Exception):
    pass


def to_ticker(code: str) -> str:
    code = code.strip().upper()
    if not code.endswith(".T"):
        code = f"{code}.T"
    return code

to_yf_ticker = to_ticker


# ---------- 銘柄名マスタ ----------

_STOCK_NAMES: dict[str, str] = {
    "7203": "トヨタ自動車",
    "6758": "ソニーグループ",
    "9984": "ソフトバンクグループ",
    "6861": "キーエンス",
    "7974": "任天堂",
    "4063": "信越化学工業",
    "8306": "三菱UFJフィナンシャル・グループ",
    "9432": "日本電信電話（NTT）",
    "4519": "中外製薬",
    "6098": "リクルートホールディングス",
    "8035": "東京エレクトロン",
    "6501": "日立製作所",
    "6902": "デンソー",
    "4543": "テルモ",
    "9433": "KDDI",
    "8058": "三菱商事",
    "7267": "本田技研工業",
    "6702": "富士通",
    "4568": "第一三共",
    "8001": "伊藤忠商事",
    "9022": "東海旅客鉄道（JR東海）",
    "9020": "東日本旅客鉄道（JR東日本）",
    "2802": "味の素",
    "3382": "セブン&アイ・ホールディングス",
    "4452": "花王",
    "7751": "キヤノン",
    "6981": "村田製作所",
    "5401": "日本製鉄",
    "8316": "三井住友フィナンシャルグループ",
    "8411": "みずほフィナンシャルグループ",
    "6367": "ダイキン工業",
    "4901": "富士フイルムホールディングス",
    "8031": "三井物産",
    "2914": "日本たばこ産業（JT）",
    "4502": "武田薬品工業",
    "9984": "ソフトバンクグループ",
    "7741": "HOYA",
    "6645": "オムロン",
    "6503": "三菱電機",
    "7733": "オリンパス",
}


# ---------- stooq CSV 取得 ----------

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}
_PERIOD_DAYS = {
    "1d": 1, "5d": 7, "1mo": 35, "3mo": 100,
    "6mo": 190, "1y": 370, "2y": 740, "5y": 1835,
}


def _fetch_stooq(code: str, days: int = 370) -> list[dict]:
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    url = "https://stooq.com/q/d/l/"
    params = {
        "s": f"{code}.jp",
        "d1": start_date.strftime("%Y%m%d"),
        "d2": end_date.strftime("%Y%m%d"),
        "i": "d",
    }
    resp = _session.get(url, params=params, timeout=15)
    resp.raise_for_status()

    content = resp.text.strip()
    if not content or "Date" not in content:
        raise NotFoundError(f"株価データが見つかりません: {code}")

    reader = csv.DictReader(io.StringIO(content))
    rows = sorted(list(reader), key=lambda r: r.get("Date", ""))

    candles = []
    for row in rows:
        try:
            vol_str = row.get("Volume", "")
            candles.append({
                "date": row["Date"],
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(float(vol_str)) if vol_str else None,
            })
        except (ValueError, KeyError):
            continue

    if not candles:
        raise NotFoundError(f"株価データが見つかりません: {code}")

    return candles


# ---------- 企業概要 ----------

@cached("company")
def fetch_company_info(code: str) -> dict:
    candles = _fetch_stooq(code, days=370)
    latest = candles[-1]
    prev = candles[-2] if len(candles) > 1 else candles[-1]

    high_52w = max(c["high"] for c in candles)
    low_52w = min(c["low"] for c in candles)

    return {
        "code": code,
        "ticker": to_ticker(code),
        "name": _STOCK_NAMES.get(code, f"銘柄 {code}"),
        "industry": "",
        "sector": "",
        "exchange": "東証",
        "market_cap": None,
        "website": "",
        "address": "",
        "business_summary": "",
        "employees": None,
        "currency": "JPY",
        "price": latest["close"],
        "previous_close": prev["close"],
        "52w_high": high_52w,
        "52w_low": low_52w,
    }


# ---------- 財務データ ----------

@cached("financials")
def fetch_financials(code: str) -> dict:
    candles = _fetch_stooq(code, days=5)
    price = candles[-1]["close"] if candles else None

    return {
        "code": code,
        "performance": [],
        "valuation": {
            "price": price,
            "market_cap": None,
            "per": None, "forward_per": None, "pbr": None,
            "dividend_yield": None, "dividend_per_share": None,
            "eps": None, "eps_forward": None, "ev_ebitda": None,
        },
        "health": {
            "roe": None, "roa": None, "current_ratio": None,
            "debt_to_equity": None, "total_debt": None, "total_cash": None,
            "free_cashflow": None, "operating_cashflow": None, "equity_ratio": None,
        },
    }


# ---------- 株価チャート ----------

@cached("chart")
def fetch_chart(code: str, period: str = "1y") -> dict:
    if period not in VALID_PERIODS:
        period = "1y"

    candles = _fetch_stooq(code, days=_PERIOD_DAYS.get(period, 370))

    latest = candles[-1]
    first = candles[0]
    change_pct = None
    if first["close"] and latest["close"]:
        change_pct = round((latest["close"] - first["close"]) / first["close"] * 100, 2)

    return {
        "code": code,
        "period": period,
        "candles": candles,
        "summary": {
            "latest_close": latest["close"],
            "period_start": first["date"],
            "period_end": latest["date"],
            "change_pct": change_pct,
            "high": max(c["high"] for c in candles),
            "low": min(c["low"] for c in candles),
        },
    }


# ---------- 銘柄検索 ----------

_STATIC_STOCKS = [(code, name) for code, name in _STOCK_NAMES.items()]


@cached("search")
def search_stocks(query: str) -> list[dict]:
    query = query.strip()
    results = []
    seen_codes = set()

    if query.isdigit() and len(query) == 4:
        for code, name in _STATIC_STOCKS:
            if code == query:
                results.append({"code": code, "name": name, "matched_by": "code"})
                seen_codes.add(code)
                break
        if query not in seen_codes:
            results.append({"code": query, "name": "", "matched_by": "code"})
            seen_codes.add(query)

    q_lower = query.lower()
    for code, name in _STATIC_STOCKS:
        if code in seen_codes:
            continue
        if q_lower in name.lower() or q_lower in code:
            results.append({"code": code, "name": name, "matched_by": "name"})
            seen_codes.add(code)

    # Yahoo Finance 検索（失敗してもOK）
    try:
        resp = _session.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": query, "quotesCount": 10, "newsCount": 0, "listsCount": 0},
            timeout=5,
        )
        resp.raise_for_status()
        for item in resp.json().get("quotes", []):
            symbol = item.get("symbol", "")
            if not symbol.endswith(".T"):
                continue
            code = symbol.replace(".T", "")
            if code in seen_codes:
                continue
            name = item.get("longname") or item.get("shortname") or ""
            results.append({"code": code, "name": name, "matched_by": "yfinance"})
            seen_codes.add(code)
            if len(results) >= 10:
                break
    except Exception:
        pass

    return results[:10]
