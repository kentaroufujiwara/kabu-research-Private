from fastapi import APIRouter, HTTPException, Query
from services.yfinance_service import search_stocks

router = APIRouter(tags=["search"])


@router.get("/search")
def search(
    q: str = Query(..., description="企業名または証券コード", min_length=1, max_length=50),
):
    """
    銘柄を検索して候補リストを返す。
    - 4桁コード入力 → コード完全一致を優先
    - 企業名入力 → 部分一致 + yfinance Search
    """
    try:
        results = search_stocks(q)
        return {"success": True, "query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")
