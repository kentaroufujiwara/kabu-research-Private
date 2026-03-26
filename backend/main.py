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
