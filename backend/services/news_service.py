"""
ニュース取得サービス。
Google News RSS で銘柄名検索 → 銘柄固有のニュースを返す。
"""

import xml.etree.ElementTree as ET
import httpx
from datetime import datetime, timezone
from services.jquants_service import get_company_name
from cache import cached


class NotFoundError(Exception):
    pass


def _fetch_google_news(company_name: str, code: str) -> list[dict]:
    """Google News RSS で銘柄名検索"""
    query = f"{company_name} {code}"
    url = f"https://news.google.com/rss/search?q={httpx.URL('', params={'q': query}).params}&hl=ja&gl=JP&ceid=JP:ja"
    # シンプルにURLを構築
    import urllib.parse
    encoded_q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=ja&gl=JP&ceid=JP:ja"
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (compatible; kabu-research/1.0)"
        })
        if resp.status_code != 200:
            return []
        return _parse_rss(resp.text, source="Google News")
    except Exception:
        return []


def _fetch_yahoo_rss(code: str) -> list[dict]:
    """Yahoo Finance RSS（英語ニュース、フォールバック用）"""
    ticker = f"{code}.T"
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


@cached("news")
def fetch_news(code: str) -> dict:
    # 会社名を取得してGoogle Newsで検索
    company_name = get_company_name(code)
    google_items = _fetch_google_news(company_name, code)

    # Google Newsで十分取れなければYahoo Finance RSSも追加
    yahoo_items = []
    if len(google_items) < 5:
        yahoo_items = _fetch_yahoo_rss(code)

    all_items = google_items + yahoo_items
    # 重複URLを除去
    seen = set()
    unique_items = []
    for item in all_items:
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_items.append(item)

    unique_items.sort(key=lambda x: x.get("published_at") or "", reverse=True)

    return {
        "code": code,
        "items": unique_items[:15],
        "sources": {
            "yahoo_count": len(yahoo_items),
            "edinet_count": 0,
        },
    }
