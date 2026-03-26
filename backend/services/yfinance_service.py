"""
Yahoo Finance v7 APIとstooq.comを使って日本株データを取得するサービス。
yfinanceライブラリを使わず直接HTTPリクエストを行う。
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

# news_service.py との互換性のためのエイリアス
to_yf_ticker = to_ticker


def _pct(value) -> float | None:
    if value is None:
        return None
    return round(float(value) * 100, 2)


# ---------- 企業概要 ----------

@cached("company")
def fetch_company_info(code: str) -> dict:
    ticker = to_ticker(code)
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ticker, "lang": "en-US", "region": "JP"}

    resp = _session.get(url, params=params, timeout=10)
    if resp.status_code == 429:
        raise RateLimitError("Yahoo Finance のレート制限に達しました。")
    resp.raise_for_status()

    results = resp.json().get("quoteResponse", {}).get("result", [])
    if not results:
        raise NotFoundError(f"銘柄が見つかりません: {code}")

    info = results[0]
    if not info.get("longName") and not info.get("shortName"):
        raise NotFoundError(f"銘柄が見つかりません: {code}")

    return {
        "code": code,
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName", ""),
        "industry": info.get("industry", ""),
        "sector": info.get("sector", ""),
        "exchange": info.get("fullExchangeName", info.get("exchange", "")),
        "market_cap": info.get("marketCap"),
        "website": "",
        "address": "",
        "business_summary": "",
        "employees": info.get("fullTimeEmployees"),
        "currency": info.get("currency", "JPY"),
        "price": info.get("regularMarketPrice"),
        "previous_close": info.get("regularMarketPreviousClose"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
    }


# ---------- 財務データ ----------

@cached("financials")
def fetch_financials(code: str) -> dict:
    ticker = to_ticker(code)

    # バリュエーション・健全性指標: v7 quote API
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ticker, "lang": "en-US", "region": "JP"}
    resp = _session.get(url, params=params, timeout=10)
    if resp.status_code == 429:
        raise RateLimitError("Yahoo Finance のレート制限に達しました。")
    resp.raise_for_status()

    results = resp.json().get("quoteResponse", {}).get("result", [])
    if not results:
        raise NotFoundError(f"銘柄が見つかりません: {code}")
    info = results[0]

    # 業績推移: timeseries API
    performance = _fetch_timeseries(ticker)

    return {
        "code": code,
        "performance": performance,
        "valuation": {
            "price": info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "per": info.get("trailingPE"),
            "forward_per": info.get("forwardPE"),
            "pbr": info.get("priceToBook"),
            "dividend_yield": _pct(info.get("dividendYield")),
            "dividend_per_share": info.get("dividendRate"),
            "eps": info.get("epsTrailingTwelveMonths"),
            "eps_forward": info.get("epsForward"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
        },
        "health": {
            "roe": _pct(info.get("returnOnEquity")),
            "roa": _pct(info.get("returnOnAssets")),
            "current_ratio": info.get("currentRatio"),
            "debt_to_equity": info.get("debtToEquity"),
            "total_debt": info.get("totalDebt"),
            "total_cash": info.get("totalCash"),
            "free_cashflow": info.get("freeCashflow"),
            "operating_cashflow": info.get("operatingCashflow"),
            "equity_ratio": None,
        },
    }


def _fetch_timeseries(ticker: str) -> list[dict]:
    url = (
        "https://query1.finance.yahoo.com/ws/fundamentals-timeseries"
        f"/v1/finance/timeseries/{ticker}"
    )
    params = {
        "type": "annualTotalRevenue,annualOperatingIncome,annualNetIncome,annualBasicEPS",
        "period1": "1000000000",
        "period2": "9999999999",
    }
    try:
        resp = _session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        ts_results = resp.json().get("timeseries", {}).get("result", [])
    except Exception:
        return []

    buckets: dict[str, dict] = {}
    key_map = {
        "annualTotalRevenue": "revenue",
        "annualOperatingIncome": "operating_income",
        "annualNetIncome": "net_income",
        "annualBasicEPS": "eps",
    }
    for series in ts_results:
        series_type = (series.get("meta", {}).get("type") or [""])[0]
        field = key_map.get(series_type)
        if not field:
            continue
        for item in (series.get(series_type) or []):
            if item is None:
                continue
            year = (item.get("asOfDate") or "")[:4]
            raw = (item.get("reportedValue") or {}).get("raw")
            if not year or raw is None:
                continue
            buckets.setdefault(year, {"fiscal_year": year, "revenue": None,
                                       "operating_income": None, "net_income": None, "eps": None})
            if field == "eps":
                buckets[year][field] = round(float(raw), 2)
            else:
                buckets[year][field] = int(raw)

    return sorted(buckets.values(), key=lambda r: r["fiscal_year"], reverse=True)[:5]


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
    if not content or content.startswith("No data") or "Date" not in content:
        raise NotFoundError(f"株価データが見つかりません: {code}")

    reader = csv.DictReader(io.StringIO(content))
    rows = sorted(list(reader), key=lambda r: r["Date"])

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
