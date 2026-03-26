"""
Yahoo Finance v8 chart API と stooq を使って日本株データを取得するサービス。
- 会社情報・チャート: Yahoo Finance v8 chart API (認証不要)
- 株価チャート: stooq.com (バックアップ)
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
    "Accept": "application/json",
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

# news_service.py との互換性
to_yf_ticker = to_ticker


def _v8_meta(code: str) -> dict:
    """Yahoo Finance v8 chart API からメタデータを取得"""
    ticker = to_ticker(code)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    resp = _session.get(url, params={"interval": "1d", "range": "5d"}, timeout=10)
    if resp.status_code == 404:
        raise NotFoundError(f"銘柄が見つかりません: {code}")
    if resp.status_code == 429:
        raise RateLimitError("Yahoo Finance のレート制限に達しました。")
    resp.raise_for_status()

    result = resp.json().get("chart", {}).get("result") or []
    if not result:
        raise NotFoundError(f"銘柄が見つかりません: {code}")
    return result[0].get("meta", {})


# ---------- 企業概要 ----------

@cached("company")
def fetch_company_info(code: str) -> dict:
    meta = _v8_meta(code)
    return {
        "code": code,
        "ticker": to_ticker(code),
        "name": meta.get("longName") or meta.get("shortName", ""),
        "industry": "",
        "sector": "",
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName", ""),
        "market_cap": None,
        "website": "",
        "address": "",
        "business_summary": "",
        "employees": None,
        "currency": meta.get("currency", "JPY"),
        "price": meta.get("regularMarketPrice"),
        "previous_close": meta.get("chartPreviousClose"),
        "52w_high": meta.get("fiftyTwoWeekHigh"),
        "52w_low": meta.get("fiftyTwoWeekLow"),
    }


# ---------- 財務データ ----------

@cached("financials")
def fetch_financials(code: str) -> dict:
    meta = _v8_meta(code)
    return {
        "code": code,
        "performance": [],
        "valuation": {
            "price": meta.get("regularMarketPrice"),
            "market_cap": None,
            "per": None,
            "forward_per": None,
            "pbr": None,
            "dividend_yield": None,
            "dividend_per_share": None,
            "eps": None,
            "eps_forward": None,
            "ev_ebitda": None,
        },
        "health": {
            "roe": None,
            "roa": None,
            "current_ratio": None,
            "debt_to_equity": None,
            "total_debt": None,
            "total_cash": None,
            "free_cashflow": None,
            "operating_cashflow": None,
            "equity_ratio": None,
        },
    }


# ---------- 株価チャート (stooq) ----------

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}
_PERIOD_DAYS = {
    "1d": 1, "5d": 7, "1mo": 35, "3mo": 100,
    "6mo": 190, "1y": 370, "2y": 740, "5y": 1835,
}


@cached("chart")
def fetch_chart(code: str, period: str = "1y") -> dict:
    if period not in VALID_PERIODS:
        period = "1y"

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=_PERIOD_DAYS.get(period, 370))

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

    if not rows:
        raise NotFoundError(f"株価データが見つかりません: {code}")

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

_STATIC_STOCKS = [
    ("7203", "トヨタ自動車"),
    ("6758", "ソニーグループ"),
    ("9984", "ソフトバンクグループ"),
    ("6861", "キーエンス"),
    ("7974", "任天堂"),
    ("4063", "信越化学工業"),
    ("8306", "三菱UFJフィナンシャル・グループ"),
    ("9432", "日本電信電話（NTT）"),
    ("4519", "中外製薬"),
    ("6098", "リクルートホールディングス"),
    ("8035", "東京エレクトロン"),
    ("6501", "日立製作所"),
    ("6902", "デンソー"),
    ("4543", "テルモ"),
    ("9433", "KDDI"),
    ("8058", "三菱商事"),
    ("7267", "本田技研工業"),
    ("6702", "富士通"),
    ("4568", "第一三共"),
    ("8001", "伊藤忠商事"),
    ("9022", "東海旅客鉄道（JR東海）"),
    ("9020", "東日本旅客鉄道（JR東日本）"),
    ("2802", "味の素"),
    ("3382", "セブン&アイ・ホールディングス"),
    ("4452", "花王"),
    ("7751", "キヤノン"),
    ("6981", "村田製作所"),
    ("5401", "日本製鉄"),
    ("8316", "三井住友フィナンシャルグループ"),
    ("8411", "みずほフィナンシャルグループ"),
]


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
