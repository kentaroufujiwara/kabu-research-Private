"""
yfinance を使って日本株データを取得するサービス。
証券コードは yfinance 形式（例: 7203 → "7203.T"）に変換して使用。
"""

import json
import yfinance as yf
import requests
from cache import cached

# Yahoo Finance のレート制限を回避するためのカスタムセッション
_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
})


class NotFoundError(Exception):
    pass


class RateLimitError(Exception):
    pass


def _wrap_yf_errors(func):
    """yfinance の HTTPError / JSONDecodeError を適切な例外に変換するデコレータ"""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                raise RateLimitError("Yahoo Finance のレート制限に達しました。しばらく待ってから再試行してください。") from e
            raise
        except json.JSONDecodeError as e:
            # yfinance が空レスポンスを返すのはレート制限時が多い
            raise RateLimitError("Yahoo Finance からデータを取得できませんでした（レート制限の可能性）。") from e

    return wrapper


def to_yf_ticker(code: str) -> str:
    """4桁証券コードを yfinance のティッカー形式に変換"""
    code = code.strip().upper()
    if not code.endswith(".T"):
        code = f"{code}.T"
    return code


def get_ticker(code: str) -> yf.Ticker:
    return yf.Ticker(to_yf_ticker(code), session=_session)


# ---------- 企業概要 ----------

@cached("company")
@_wrap_yf_errors
def fetch_company_info(code: str) -> dict:
    ticker = get_ticker(code)
    info = ticker.info

    if not info or info.get("quoteType") is None:
        raise NotFoundError(f"銘柄が見つかりません: {code}")

    return {
        "code": code,
        "ticker": to_yf_ticker(code),
        "name": info.get("longName") or info.get("shortName", ""),
        "industry": info.get("industry", ""),
        "sector": info.get("sector", ""),
        "exchange": info.get("exchange", ""),
        "market_cap": info.get("marketCap"),
        "website": info.get("website", ""),
        "address": _build_address(info),
        "business_summary": info.get("longBusinessSummary", ""),
        "employees": info.get("fullTimeEmployees"),
        "currency": info.get("currency", "JPY"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
    }


def _build_address(info: dict) -> str:
    parts = [
        info.get("address1", ""),
        info.get("city", ""),
        info.get("state", ""),
        info.get("country", ""),
    ]
    return " ".join(p for p in parts if p)


# ---------- 財務データ ----------

@cached("financials")
@_wrap_yf_errors
def fetch_financials(code: str) -> dict:
    ticker = get_ticker(code)
    info = ticker.info

    if not info or info.get("quoteType") is None:
        raise NotFoundError(f"銘柄が見つかりません: {code}")

    # 損益計算書（年次）
    income_stmt = ticker.financials  # columns = 決算期, rows = 項目
    # キャッシュフロー
    cashflow = ticker.cashflow
    # バランスシート
    balance = ticker.balance_sheet

    performance = _build_performance(income_stmt, balance)

    valuation = {
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "per": info.get("trailingPE"),
        "forward_per": info.get("forwardPE"),
        "pbr": info.get("priceToBook"),
        "dividend_yield": _pct(info.get("dividendYield")),
        "dividend_per_share": info.get("dividendRate"),
        "eps": info.get("trailingEps"),
        "eps_forward": info.get("forwardEps"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
    }

    health = {
        "roe": _pct(info.get("returnOnEquity")),
        "roa": _pct(info.get("returnOnAssets")),
        "current_ratio": info.get("currentRatio"),
        "debt_to_equity": info.get("debtToEquity"),
        "total_debt": _extract_latest(balance, "Total Debt"),
        "total_cash": info.get("totalCash"),
        "free_cashflow": info.get("freeCashflow"),
        "operating_cashflow": info.get("operatingCashflow"),
        "equity_ratio": _calc_equity_ratio(balance),
    }

    return {
        "code": code,
        "performance": performance,
        "valuation": valuation,
        "health": health,
    }


def _pct(value) -> float | None:
    """小数 → パーセント変換（例: 0.035 → 3.5）"""
    if value is None:
        return None
    return round(value * 100, 2)


def _extract_latest(df, label: str):
    """DataFrameから最新期の値を取得"""
    if df is None or df.empty:
        return None
    if label in df.index:
        series = df.loc[label].dropna()
        if not series.empty:
            return int(series.iloc[0])
    return None


def _calc_equity_ratio(balance) -> float | None:
    """自己資本比率 = 自己資本 / 総資産"""
    if balance is None or balance.empty:
        return None
    try:
        equity_labels = ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"]
        asset_labels = ["Total Assets"]

        equity = None
        for label in equity_labels:
            val = _extract_latest(balance, label)
            if val is not None:
                equity = val
                break

        assets = _extract_latest(balance, "Total Assets")

        if equity and assets and assets != 0:
            return round((equity / assets) * 100, 2)
    except Exception:
        pass
    return None


def _build_performance(income_stmt, balance) -> list[dict]:
    """過去3〜5期分の業績データを組み立てる"""
    if income_stmt is None or income_stmt.empty:
        return []

    results = []
    for col in income_stmt.columns[:5]:  # 最大5期
        year = str(col.year) if hasattr(col, "year") else str(col)[:4]

        revenue = _safe_int(income_stmt, col, "Total Revenue")
        op_income = _safe_int(income_stmt, col, "Operating Income")
        net_income = _safe_int(income_stmt, col, "Net Income")

        # EPS は損益計算書から取得（Basic EPS）
        eps_row = None
        for label in ["Basic EPS", "Diluted EPS"]:
            if label in income_stmt.index:
                val = income_stmt.loc[label, col]
                if val is not None and str(val) != "nan":
                    eps_row = round(float(val), 2)
                    break

        results.append({
            "fiscal_year": year,
            "revenue": revenue,
            "operating_income": op_income,
            "net_income": net_income,
            "eps": eps_row,
        })

    return results


def _safe_int(df, col, label: str):
    if label not in df.index:
        return None
    val = df.loc[label, col]
    if val is None or str(val) == "nan":
        return None
    try:
        return int(val)
    except Exception:
        return None


# ---------- 株価チャート ----------

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}

@cached("chart")
@_wrap_yf_errors
def fetch_chart(code: str, period: str = "1y") -> dict:
    if period not in VALID_PERIODS:
        period = "1y"

    ticker = get_ticker(code)
    hist = ticker.history(period=period, interval="1d", auto_adjust=True)

    if hist is None or hist.empty:
        raise NotFoundError(f"株価データが見つかりません: {code}")

    # フロントエンドが使いやすい形式に変換
    candles = []
    for ts, row in hist.iterrows():
        candles.append({
            "date": ts.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]) if row["Volume"] == row["Volume"] else None,
        })

    latest = candles[-1] if candles else {}
    first = candles[0] if candles else {}
    change_pct = None
    if first.get("close") and latest.get("close"):
        change_pct = round((latest["close"] - first["close"]) / first["close"] * 100, 2)

    return {
        "code": code,
        "period": period,
        "candles": candles,
        "summary": {
            "latest_close": latest.get("close"),
            "period_start": first.get("date"),
            "period_end": latest.get("date"),
            "change_pct": change_pct,
            "high": max(c["high"] for c in candles) if candles else None,
            "low": min(c["low"] for c in candles) if candles else None,
        },
    }


# ---------- 銘柄検索 ----------

# 主要銘柄の静的リスト（検索のフォールバック用）
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
    """
    証券コードまたは企業名で銘柄を検索。
    1. コードで完全一致
    2. 名前の部分一致（静的リスト）
    3. yfinance の search（利用可能な場合）
    """
    query = query.strip()
    results = []
    seen_codes = set()

    # --- 1. コード完全一致 ---
    if query.isdigit() and len(query) == 4:
        for code, name in _STATIC_STOCKS:
            if code == query:
                results.append({"code": code, "name": name, "matched_by": "code"})
                seen_codes.add(code)
                break
        # リストに無くても候補として追加
        if query not in seen_codes:
            results.append({"code": query, "name": "", "matched_by": "code"})
            seen_codes.add(query)

    # --- 2. 名前の部分一致（静的リスト） ---
    q_lower = query.lower()
    for code, name in _STATIC_STOCKS:
        if code in seen_codes:
            continue
        if q_lower in name.lower() or q_lower in code:
            results.append({"code": code, "name": name, "matched_by": "name"})
            seen_codes.add(code)

    # --- 3. Yahoo Finance 検索 API（最大10件補完） ---
    try:
        resp = _session.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": query, "quotesCount": 10, "newsCount": 0, "listsCount": 0},
            timeout=5,
        )
        resp.raise_for_status()
        quotes = resp.json().get("quotes", [])
        for item in quotes:
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
        # 検索 API が失敗しても静的リスト結果を返す
        pass

    return results[:10]
