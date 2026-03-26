from fastapi import APIRouter, HTTPException, Path
from services.jquants_service import fetch_financials, NotFoundError, AuthError

router = APIRouter(tags=["financials"])


@router.get("/financials/{code}")
def get_financials(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5)
):
    try:
        data = fetch_financials(code)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")
