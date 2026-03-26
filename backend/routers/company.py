from fastapi import APIRouter, HTTPException, Path
from services.jquants_service import fetch_company_info, NotFoundError, AuthError

router = APIRouter(tags=["company"])


@router.get("/company/{code}")
def get_company(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5)
):
    try:
        data = fetch_company_info(code)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")
