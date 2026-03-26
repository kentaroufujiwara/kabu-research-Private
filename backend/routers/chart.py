from fastapi import APIRouter, HTTPException, Path, Query
from services.yfinance_service import fetch_chart, NotFoundError, RateLimitError

router = APIRouter(tags=["chart"])


@router.get("/chart/{code}")
def get_chart(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5),
    period: str = Query("1y", description="期間: 1d / 5d / 1mo / 3mo / 6mo / 1y / 2y / 5y"),
):
    """
    株価チャートデータを返す（日次 OHLCV）。
    - candles: 各日の始値・高値・安値・終値・出来高
    - summary: 期間サマリー（最新終値・騰落率・期間高安値）
    """
    try:
        data = fetch_chart(code, period)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")
