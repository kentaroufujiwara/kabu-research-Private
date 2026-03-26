"""
J-Quants API V2 (JPX公式) を使って日本株データを取得するサービス。
環境変数: JQUANTS_API_KEY
登録: https://jpx-jquants.com/
"""

import os
import datetime
import requests
from cache import cached

_BASE = "https://api.jquants.com/v2"
_session = requests.Session()


class NotFoundError(Exception):
    pass


class AuthError(Exception):
    pass


def _get_headers() -> dict:
    api_key = os.environ.get("JQUANTS_API_KEY", "")
    if not api_key:
        raise AuthError("JQUANTS_API_KEY が設定されていません")
    return {"x-api-key": api_key}


def _get(path: str, params: dict | None = None) -> dict:
    try:
        headers = _get_headers()
    except AuthError:
        raise
    r = _session.get(f"{_BASE}{path}", params=params, headers=headers, timeout=15)
    if r.status_code == 404:
        raise NotFoundError(f"データが見つかりません: {path}")
    if r.status_code == 401 or r.status_code == 403:
        raise AuthError(f"認証エラー: APIキーを確認してください ({r.status_code})")
    r.raise_for_status()
    return r.json()


def _to_code5(code: str) -> str:
    """4桁コードを5桁に変換 (7203 → 72030)"""
    if len(code) == 4:
        return code + "0"
    return code


# ---------- 企業概要 ----------

@cached("company")
def fetch_company_info(code: str) -> dict:
    code5 = _to_code5(code)

    # 企業マスタ
    master_data = _get("/equities/master", params={"code": code})
    items = master_data.get("data") or []
    if not items:
        raise NotFoundError(f"銘柄が見つかりません: {code}")
    info = items[0]

    # 最新株価
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=370)).strftime("%Y-%m-%d")
    price_data = _get("/equities/bars/daily", params={"code": code, "from": start})
    quotes = sorted(price_data.get("data") or [], key=lambda q: q.get("Date", ""))
    latest = quotes[-1] if quotes else {}
    prev = quotes[-2] if len(quotes) > 1 else latest

    high_52w = max((q.get("H") or 0) for q in quotes) if quotes else None
    low_52w = min((q.get("L") or 0) for q in quotes if q.get("L")) if quotes else None

    return {
        "code": code,
        "ticker": f"{code}.T",
        "name": info.get("CoName") or info.get("CoNameEn", ""),
        "industry": info.get("S33Nm", ""),
        "sector": info.get("S33Nm", ""),
        "exchange": info.get("MktNm", "東証"),
        "market_cap": None,
        "website": "",
        "address": "",
        "business_summary": "",
        "employees": None,
        "currency": "JPY",
        "price": latest.get("C") or latest.get("AdjC"),
        "previous_close": prev.get("C") or prev.get("AdjC"),
        "52w_high": high_52w or None,
        "52w_low": low_52w or None,
    }


# ---------- 財務データ ----------

@cached("financials")
def fetch_financials(code: str) -> dict:
    # 最新株価
    today = datetime.date.today()
    start = (today - datetime.timedelta(days=400)).strftime("%Y-%m-%d")
    price_data = _get("/equities/bars/daily", params={"code": code, "from": start})
    quotes = sorted(price_data.get("data") or [], key=lambda q: q.get("Date", ""))
    price = quotes[-1].get("C") if quotes else None

    # 財務サマリー
    fin_data = _get("/fins/summary", params={"code": code})
    statements = fin_data.get("data") or []

    # 年次データのみ
    annual = [s for s in statements if "FY" in (s.get("CurPerType") or "")]
    if not annual:
        annual = statements

    annual_sorted = sorted(annual, key=lambda s: s.get("CurPerEn", ""), reverse=True)

    performance = []
    for stmt in annual_sorted[:5]:
        year = (stmt.get("CurPerEn") or "")[:4]
        performance.append({
            "fiscal_year": year,
            "revenue": _to_int(stmt.get("Sales")),
            "operating_income": _to_int(stmt.get("OP")),
            "net_income": _to_int(stmt.get("NP")),
            "eps": _to_float(stmt.get("EPS")),
        })

    latest_stmt = annual_sorted[0] if annual_sorted else {}

    return {
        "code": code,
        "performance": performance,
        "valuation": {
            "price": price,
            "market_cap": None,
            "per": None,
            "forward_per": None,
            "pbr": None,
            "dividend_yield": None,
            "dividend_per_share": _to_float(latest_stmt.get("DivAnn")),
            "eps": _to_float(latest_stmt.get("EPS")),
            "eps_forward": _to_float(latest_stmt.get("FEPS") or latest_stmt.get("NxFEPS")),
            "ev_ebitda": None,
        },
        "health": {
            "roe": None,
            "roa": None,
            "current_ratio": None,
            "debt_to_equity": None,
            "total_debt": None,
            "total_cash": _to_int(latest_stmt.get("CashEq")),
            "free_cashflow": None,
            "operating_cashflow": _to_int(latest_stmt.get("CFO")),
            "equity_ratio": _to_float(latest_stmt.get("EqAR")),
        },
    }


# ---------- 株価チャート ----------

@cached("chart")
def fetch_chart(code: str, period: str = "1y") -> dict:
    period_days = {
        "1d": 1, "5d": 7, "1mo": 35, "3mo": 100,
        "6mo": 190, "1y": 370, "2y": 740, "5y": 1835,
    }
    days = period_days.get(period, 370)
    start = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")

    price_data = _get("/equities/bars/daily", params={"code": code, "from": start})
    quotes = sorted(price_data.get("data") or [], key=lambda q: q.get("Date", ""))

    if not quotes:
        raise NotFoundError(f"株価データが見つかりません: {code}")

    candles = []
    for q in quotes:
        try:
            candles.append({
                "date": q["Date"],
                "open": float(q.get("O") or q.get("AdjO") or 0),
                "high": float(q.get("H") or q.get("AdjH") or 0),
                "low": float(q.get("L") or q.get("AdjL") or 0),
                "close": float(q.get("C") or q.get("AdjC") or 0),
                "volume": int(q.get("Vo") or 0),
            })
        except (TypeError, ValueError):
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


# ---------- ユーティリティ ----------

def _to_int(val) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _to_float(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None
# J-Quants V2 API
