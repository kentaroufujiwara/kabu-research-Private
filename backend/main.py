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
