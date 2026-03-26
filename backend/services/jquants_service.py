"""
J-Quants API (JPX公式) を使って日本株データを取得するサービス。
環境変数: JQUANTS_EMAIL, JQUANTS_PASSWORD
登録: https://jpx-jquants.com/
"""

import os
import time
import requests
from cache import cached

_BASE = "https://api.jquants.com/v1"
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})

_token_cache: dict = {"id_token": None, "expires_at": 0}


class NotFoundError(Exception):
    pass


class AuthError(Exception):
    pass


def _get_id_token() -> str:
    """IDトークンを取得（キャッシュあり）"""
    now = time.time()
    if _token_cache["id_token"] and now < _token_cache["expires_at"]:
        return _token_cache["id_token"]

    # JQUANTS_API_KEY または JQUANTS_REFRESH_TOKEN をリフレッシュトークンとして使用
    refresh_token = os.environ.get("JQUANTS_API_KEY", "") or os.environ.get("JQUANTS_REFRESH_TOKEN", "")

    # なければメール/パスワードから取得
    if not refresh_token:
        email = os.environ.get("JQUANTS_EMAIL", "")
        password = os.environ.get("JQUANTS_PASSWORD", "")
        if not email or not password:
            raise AuthError("JQUANTS_API_KEY（リフレッシュトークン）または JQUANTS_EMAIL/JQUANTS_PASSWORD が設定されていません")
        r = _session.post(
            f"{_BASE}/token/auth_user",
            json={"mailaddress": email, "password": password},
            timeout=10,
        )
        r.raise_for_status()
        refresh_token = r.json().get("refreshToken")
        if not refresh_token:
            raise AuthError("リフレッシュトークンの取得に失敗しました")

    r2 = _session.post(
        f"{_BASE}/token/auth_refresh",
        params={"refreshtoken": refresh_token},
        timeout=10,
    )
    r2.raise_for_status()
    id_token = r2.json().get("idToken")
    if not id_token:
        raise AuthError("IDトークンの取得に失敗しました")

    _token_cache["id_token"] = id_token
    _token_cache["expires_at"] = now + 23 * 3600
    return id_token


def _get(path: str, params: dict | None = None) -> dict:
    token = _get_id_token()
    headers = {"Authorization": f"Bearer {token}"}
    r = _session.get(f"{_BASE}{path}", params=params, headers=headers, timeout=15)
    if r.status_code == 404:
        raise NotFoundError(f"データが見つかりません: {path}")
    r.raise_for_status()
    return r.json()


# ---------- 企業概要 ----------

@cached("company")
def fetch_company_info(code: str) -> dict:
    data = _get("/listed/info", params={"code": code})
    info_list = data.get("info") or []
    if not info_list:
        raise NotFoundError(f"銘柄が見つかりません: {code}")
    info = info_list[0]

    # 最新株価
    price_data = _get("/prices/daily_quotes", params={"code": code})
    quotes = sorted(price_data.get("daily_quotes") or [], key=lambda q: q.get("Date", ""))
    latest = quotes[-1] if quotes else {}
    prev = quotes[-2] if len(quotes) > 1 else latest

    high_52w = max((q.get("High") or 0) for q in quotes) if quotes else None
    low_52w = min((q.get("Low") or 0) for q in quotes if q.get("Low")) if quotes else None

    sector_map = {
        "0050": "食品", "1050": "繊維", "2050": "化学", "3050": "医薬品",
        "3100": "石油・石炭", "3150": "ゴム", "3200": "ガラス・土石",
        "3250": "鉄鋼", "3300": "非鉄金属", "3350": "金属製品",
        "3400": "機械", "3450": "電気機器", "3500": "輸送用機器",
        "3550": "精密機器", "3600": "その他製造", "4050": "鉱業",
        "5050": "建設", "5100": "食料品", "5150": "繊維製品",
        "6050": "電気・ガス", "7050": "陸運", "7100": "海運",
        "7150": "空運", "7200": "倉庫・運輸", "7250": "情報・通信",
        "8050": "卸売", "8100": "小売", "8150": "銀行",
        "8200": "証券・商品先物", "8250": "保険", "8300": "その他金融",
        "9050": "不動産", "9100": "サービス", "9150": "その他",
    }

    sector_code = str(info.get("Sector33Code", ""))
    sector_name = sector_map.get(sector_code, info.get("Sector33CodeName", ""))

    return {
        "code": code,
        "ticker": f"{code}.T",
        "name": info.get("CompanyName") or info.get("CompanyNameEnglish", ""),
        "industry": sector_name,
        "sector": sector_name,
        "exchange": info.get("MarketCodeName", "東証"),
        "market_cap": None,
        "website": "",
        "address": "",
        "business_summary": "",
        "employees": None,
        "currency": "JPY",
        "price": latest.get("Close") or latest.get("AdjustmentClose"),
        "previous_close": prev.get("Close") or prev.get("AdjustmentClose"),
        "52w_high": high_52w or None,
        "52w_low": low_52w or None,
    }


# ---------- 財務データ ----------

@cached("financials")
def fetch_financials(code: str) -> dict:
    # 最新株価
    price_data = _get("/prices/daily_quotes", params={"code": code})
    quotes = sorted(price_data.get("daily_quotes") or [], key=lambda q: q.get("Date", ""))
    price = quotes[-1].get("Close") if quotes else None

    # 財務諸表
    fin_data = _get("/fins/statements", params={"code": code})
    statements = fin_data.get("statements") or []

    # 年次データのみ（TypeOfDocument: "FYAnnouncement" や "Annual"）
    annual = [s for s in statements if "Annual" in (s.get("TypeOfDocument") or "")]
    if not annual:
        annual = statements  # 無ければ全件

    annual_sorted = sorted(annual, key=lambda s: s.get("CurrentPeriodEndDate", ""), reverse=True)

    performance = []
    for stmt in annual_sorted[:5]:
        year = (stmt.get("CurrentPeriodEndDate") or "")[:4]
        performance.append({
            "fiscal_year": year,
            "revenue": _to_int(stmt.get("NetSales")),
            "operating_income": _to_int(stmt.get("OperatingProfit")),
            "net_income": _to_int(stmt.get("NetIncome")),
            "eps": _to_float(stmt.get("EarningsPerShare")),
        })

    latest_stmt = annual_sorted[0] if annual_sorted else {}

    return {
        "code": code,
        "performance": performance,
        "valuation": {
            "price": price,
            "market_cap": None,
            "per": None, "forward_per": None,
            "pbr": _to_float(latest_stmt.get("PriceBookValueRatio")),
            "dividend_yield": _to_float(latest_stmt.get("DividendYield")),
            "dividend_per_share": _to_float(latest_stmt.get("DividendPerShare")),
            "eps": _to_float(latest_stmt.get("EarningsPerShare")),
            "eps_forward": None,
            "ev_ebitda": None,
        },
        "health": {
            "roe": _to_float(latest_stmt.get("ROE")),
            "roa": _to_float(latest_stmt.get("ROA")),
            "current_ratio": None,
            "debt_to_equity": None,
            "total_debt": None,
            "total_cash": None,
            "free_cashflow": None,
            "operating_cashflow": _to_int(latest_stmt.get("CashFlowsFromOperatingActivities")),
            "equity_ratio": _to_float(latest_stmt.get("EquityToAssetRatio")),
        },
    }


# ---------- 株価チャート ----------

@cached("chart")
def fetch_chart(code: str, period: str = "1y") -> dict:
    import datetime

    period_days = {
        "1d": 1, "5d": 7, "1mo": 35, "3mo": 100,
        "6mo": 190, "1y": 370, "2y": 740, "5y": 1835,
    }
    days = period_days.get(period, 370)
    start = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")

    price_data = _get("/prices/daily_quotes", params={"code": code, "from": start})
    quotes = sorted(price_data.get("daily_quotes") or [], key=lambda q: q.get("Date", ""))

    if not quotes:
        raise NotFoundError(f"株価データが見つかりません: {code}")

    candles = []
    for q in quotes:
        try:
            candles.append({
                "date": q["Date"],
                "open": float(q.get("Open") or q.get("AdjustmentOpen") or 0),
                "high": float(q.get("High") or q.get("AdjustmentHigh") or 0),
                "low": float(q.get("Low") or q.get("AdjustmentLow") or 0),
                "close": float(q.get("Close") or q.get("AdjustmentClose") or 0),
                "volume": int(q.get("Volume") or 0),
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
