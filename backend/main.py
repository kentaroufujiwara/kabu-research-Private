from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import company, financials, chart, search, news

app = FastAPI(title="Japan Stock Research API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api")
app.include_router(company.router, prefix="/api")
app.include_router(financials.router, prefix="/api")
app.include_router(chart.router, prefix="/api")
app.include_router(news.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "message": "Japan Stock Research API"}


@app.get("/debug/jquants")
def debug_jquants():
    """J-Quants 認証診断用（一時エンドポイント）"""
    import os, requests as req
    refresh_token = os.environ.get("JQUANTS_REFRESH_TOKEN", "")
    try:
        # リフレッシュトークン → IDトークン
        r = req.post(
            "https://api.jquants.com/v1/token/auth_refresh",
            params={"refreshtoken": refresh_token},
            timeout=10,
        )
        id_token = r.json().get("idToken", "")
        if not id_token:
            return {"step": "auth_refresh", "status": r.status_code, "response": r.json()}

        # IDトークンでAPIテスト
        r2 = req.get(
            "https://api.jquants.com/v1/listed/info",
            params={"code": "7203"},
            headers={"Authorization": f"Bearer {id_token}"},
            timeout=10,
        )
        return {
            "auth": "ok",
            "api_status": r2.status_code,
            "sample": r2.json(),
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug/stooq")
def debug_stooq():
    """stooq アクセス診断用（一時エンドポイント）"""
    import requests as req
    try:
        resp = req.get(
            "https://stooq.com/q/d/l/",
            params={"s": "7203.jp", "d1": "20250101", "d2": "20260326", "i": "d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        return {
            "status_code": resp.status_code,
            "content_length": len(resp.text),
            "first_200_chars": resp.text[:200],
        }
    except Exception as e:
        return {"error": str(e)}
