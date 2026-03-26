from fastapi import APIRouter, HTTPException, Path
from services.jquants_service import fetch_financials, NotFoundError
RateLimitError = Exception

router = APIRouter(tags=["financials"])


@router.get("/financials/{code}")
def get_financials(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5)
):
    """
    財務データを返す。
    - performance: 過去3〜5期の売上・営業利益・EPS
    - valuation: PER・PBR・配当利回りなど
    - health: ROE・ROA・自己資本比率・有利子負債など
    """
    try:
        data = fetch_financials(code)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")
