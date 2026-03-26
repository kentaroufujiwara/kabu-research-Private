from fastapi import APIRouter, HTTPException, Path
from services.news_service import fetch_news, NotFoundError

router = APIRouter(tags=["news"])


@router.get("/news/{code}")
def get_news(
    code: str = Path(..., description="証券コード（例: 7203）", min_length=4, max_length=5),
):
    """
    最新ニュース・適時開示情報を返す。
    Yahoo Finance RSS + EDINET から取得。
    """
    try:
        data = fetch_news(code)
        return {"success": True, "data": data}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ニュース取得エラー: {str(e)}")
