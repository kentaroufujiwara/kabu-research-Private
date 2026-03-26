from fastapi import APIRouter, HTTPException, Path
from services.yfinance_service import fetch_company_info, NotFoundError, RateLimitError

router = APIRouter(tags=["company"])


@router.get("/company/{code}")
def get_company(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5)
):
    """
    企業概要を返す。
    - 社名・業種・市場・本社所在地・事業内容・現在株価など
    """
    try:
        data = fetch_company_info(code)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データ取得エラー: {str(e)}")
