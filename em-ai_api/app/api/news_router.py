import traceback

from fastapi import APIRouter, Depends
from jwt import ExpiredSignatureError
from fastapi.exceptions import ResponseValidationError

from app.config.auth import verify_token
from app.config.settings import FILE_PATHS
from app.common.log.log_config import setup_logger
from app.common.core.utils import get_current_datetime, make_dir
from app.common.news.news_hf_models.news_category import NewsCategoryModel
from app.common.news.news_hf_models.news_company import NewsCompanyModel
from app.common.news.news_hf_models.news_esg import NewsESGModel
from app.common.news.news_hf_models.news_keyphrase import NewsKeyphraseModel
from app.common.news.news_hf_models.news_investment import NewsInvestmentModel
from app.models.news_models import (
    NewsCategoryRequest,
    NewsCompanyRequest,
    NewsKeyphraseRequest,
    NewsESGRequest,
    NewsInvestmentRequest,
    NewsResponse,
)

router = APIRouter()

file_path = FILE_PATHS["log"] + "news"
make_dir(file_path)
file_path += f"/news_{get_current_datetime()}.log"
logger = setup_logger("news", file_path)

# 각 모델별 객체 생성
news_category_model = NewsCategoryModel()
news_company_model = NewsCompanyModel()
news_esg_model = NewsESGModel()
news_keyphrase_model = NewsKeyphraseModel()
news_investment_model = NewsInvestmentModel()


@router.post("/categories", response_model=NewsResponse)
async def get_news_category(request: NewsCategoryRequest, token: str = Depends(verify_token)):
    """뉴스 카테고리를 분류합니다.

    Args:
        request: 뉴스 카테고리 분류 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 분류된 뉴스 카테고리
    """
    try:
        news_category_model.postprocess(request.content)
        return news_category_model.response_model
    except ExpiredSignatureError:
        msg = "토근이 만료되었습니다. 담당자에게 문의하거나 토큰을 재발급 받으세요."
        logger.error(msg)
        return {"status": "error", "code": 401, "message": f"[UNAUTHORIZED] {msg}"}
    except ResponseValidationError as e:
        msg = f"생성된 응답의 키 값이 잘못되었습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 400, "message": f"[BAD REQUEST] {msg}"}
    except Exception as e:
        msg = f"API 호출 중 에러가 발생했습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 500, "message": f"[INTERNAL SERVER ERROR] {msg}"}


@router.post("/companies", response_model=NewsResponse)
async def get_news_company(request: NewsCompanyRequest, token: str = Depends(verify_token)):
    """뉴스 기업을 분류합니다.

    Args:
        request: 뉴스 기업 분류 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 분류된 뉴스 기업
    """
    try:
        news_company_model.postprocess(request.content)
        return news_company_model.response_model
    except ExpiredSignatureError:
        msg = "토근이 만료되었습니다. 담당자에게 문의하거나 토큰을 재발급 받으세요."
        logger.error(msg)
        return {"status": "error", "code": 401, "message": f"[UNAUTHORIZED] {msg}"}
    except ResponseValidationError as e:
        msg = f"생성된 응답의 키 값이 잘못되었습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 400, "message": f"[BAD REQUEST] {msg}"}
    except Exception as e:
        msg = f"API 호출 중 에러가 발생했습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 500, "message": f"[INTERNAL SERVER ERROR] {msg}"}


@router.post("/keyphrases", response_model=NewsResponse)
async def get_news_keyphrase(request: NewsKeyphraseRequest, token: str = Depends(verify_token)):
    """뉴스 키워드를 추출합니다.

    Args:
        request: 뉴스 키워드 추출 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 추출된 뉴스 키워드
    """
    try:
        news_keyphrase_model.postprocess(request.content)
        return news_keyphrase_model.response_model
    except ExpiredSignatureError:
        msg = "토근이 만료되었습니다. 담당자에게 문의하거나 토큰을 재발급 받으세요."
        logger.error(msg)
        return {"status": "error", "code": 401, "message": f"[UNAUTHORIZED] {msg}"}
    except ResponseValidationError as e:
        msg = f"생성된 응답의 키 값이 잘못되었습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 400, "message": f"[BAD REQUEST] {msg}"}
    except Exception as e:
        msg = f"API 호출 중 에러가 발생했습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 500, "message": f"[INTERNAL SERVER ERROR] {msg}"}


@router.post("/esg-sentiments", response_model=NewsResponse)
async def get_news_esg_sentiment(request: NewsESGRequest, token: str = Depends(verify_token)):
    """뉴스 ESG 감성을 분류합니다.

    Args:
        request: 뉴스 ESG 감성 분류 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 분류된 뉴스 ESG 감성
    """
    try:
        news_esg_model.postprocess(request.content)
        return news_esg_model.response_model
    except ExpiredSignatureError:
        msg = "토근이 만료되었습니다. 담당자에게 문의하거나 토큰을 재발급 받으세요."
        logger.error(msg)
        return {"status": "error", "code": 401, "message": f"[UNAUTHORIZED] {msg}"}
    except ResponseValidationError as e:
        msg = f"생성된 응답의 키 값이 잘못되었습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 400, "message": f"[BAD REQUEST] {msg}"}
    except Exception as e:
        msg = f"API 호출 중 에러가 발생했습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 500, "message": f"[INTERNAL SERVER ERROR] {msg}"}


@router.post("/investments", response_model=NewsResponse)
async def get_news_investment(request: NewsInvestmentRequest, token: str = Depends(verify_token)):
    """뉴스 투자 정보를 분류합니다.

    Args:
        request: 뉴스 투자 정보 분류 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 분류된 뉴스 투자 정보
    """
    try:
        news_investment_model.postprocess(request.title, request.content)
        return news_investment_model.response_model
    except ExpiredSignatureError:
        msg = "토근이 만료되었습니다. 담당자에게 문의하거나 토큰을 재발급 받으세요."
        logger.error(msg)
        return {"status": "error", "code": 401, "message": f"[UNAUTHORIZED] {msg}"}
    except ResponseValidationError as e:
        msg = f"생성된 응답의 키 값이 잘못되었습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 400, "message": f"[BAD REQUEST] {msg}"}
    except Exception as e:
        msg = f"API 호출 중 에러가 발생했습니다: {e}"
        logger.error(msg)
        logger.error(traceback.format_exc())
        return {"status": "error", "code": 500, "message": f"[INTERNAL SERVER ERROR] {msg}"}
