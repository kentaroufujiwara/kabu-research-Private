from fastapi import APIRouter, HTTPException, Path, Query
from services.jquants_service import fetch_chart, NotFoundError, AuthError

router = APIRouter(tags=["chart"])


@router.get("/chart/{code}")
def get_chart(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5),
    period: str = Query("1y", description="期間: 1d / 5d / 1mo / 3mo / 6mo / 1y / 2y / 5y"),
):
    try:
        data = fetch_chart(code, period)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")
