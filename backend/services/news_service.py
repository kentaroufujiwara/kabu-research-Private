"""
ニュース・適時開示情報の取得サービス。
1. Yahoo Finance RSS（英語ニュース、認証不要）
2. EDINET API（適時開示）※ APIキー取得後に有効化
"""

import xml.etree.ElementTree as ET
import httpx
from datetime import datetime, timezone
from services.yfinance_service import to_yf_ticker
from cache import cached


class NotFoundError(Exception):
    pass


# ---------- Yahoo Finance RSS ----------

def _fetch_yahoo_rss(code: str) -> list[dict]:
    ticker = to_yf_ticker(code)  # e.g. "7203.T"
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        resp = httpx.get(url, timeout=8, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (compatible; kabu-research/1.0)"
        })
        if resp.status_code != 200:
            return []
        return _parse_rss(resp.text, source="Yahoo Finance")
    except Exception:
        return []


def _parse_rss(xml_text: str, source: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item")[:10]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            description = item.findtext("description", "").strip()
            if title:
                items.append({
                    "title": title,
                    "url": link,
                    "published_at": _normalize_date(pub_date),
                    "source": source,
                    "description": description[:200] if description else None,
                })
    except Exception:
        pass
    return items


def _normalize_date(date_str: str) -> str | None:
    if not date_str:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
    return date_str


# ---------- EDINET API（APIキー必要） ----------

def _fetch_edinet_docs(code: str) -> list[dict]:
    """
    EDINET API v2 で適時開示を取得。
    環境変数 EDINET_API_KEY が設定されている場合のみ有効。
    取得先: https://api.edinet-fsa.go.jp/
    """
    import os
    from datetime import date, timedelta

    api_key = os.environ.get("EDINET_API_KEY", "")
    if not api_key:
        return []

    items = []
    for delta in range(0, 14):
        target_date = (date.today() - timedelta(days=delta)).strftime("%Y-%m-%d")
        try:
            resp = httpx.get(
                "https://api.edinet-fsa.go.jp/api/v2/documents.json",
                params={"date": target_date, "type": 2, "Subscription-Key": api_key},
                timeout=8,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            if data.get("statusCode") == 401:
                break
            for doc in data.get("results", []):
                sec_code = doc.get("secCode", "")
                if sec_code and sec_code[:4] != code[:4]:
                    continue
                doc_type_labels = {
                    "120": "有価証券報告書", "130": "訂正有価証券報告書",
                    "140": "半期報告書", "160": "四半期報告書",
                    "050": "臨時報告書", "060": "訂正臨時報告書",
                }
                doc_type = doc.get("docTypeCode", "")
                doc_name = doc_type_labels.get(doc_type, doc.get("docDescription", "開示書類"))
                doc_id = doc.get("docID", "")
                company_name = doc.get("filerName", "")
                submitted_at = doc.get("submitDateTime", "")
                if doc_id:
                    items.append({
                        "title": f"【{doc_name}】{company_name}",
                        "url": f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.aspx?S1{doc_id}",
                        "published_at": submitted_at or None,
                        "source": "EDINET",
                        "description": f"書類種別: {doc_name}",
                    })
        except Exception:
            continue
        if len(items) >= 5:
            break
    return items[:5]


# ---------- メイン ----------

@cached("news")
def fetch_news(code: str) -> dict:
    yahoo_items = _fetch_yahoo_rss(code)
    edinet_items = _fetch_edinet_docs(code)

    all_items = yahoo_items + edinet_items
    all_items.sort(
        key=lambda x: x.get("published_at") or "",
        reverse=True,
    )

    return {
        "code": code,
        "items": all_items[:15],
        "sources": {
            "yahoo_count": len(yahoo_items),
            "edinet_count": len(edinet_items),
        },
    }
