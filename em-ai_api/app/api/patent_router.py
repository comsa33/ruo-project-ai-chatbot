import traceback

from fastapi import APIRouter, Depends
from jwt import ExpiredSignatureError
from fastapi.exceptions import ResponseValidationError

from app.config.auth import verify_token
from app.config.settings import FILE_PATHS
from app.common.log.log_config import setup_logger
from app.common.core.utils import get_current_datetime, make_dir
from app.common.patent.patent_utils.patent_generation_utils import PatentGenerationUtils
from app.common.patent.patent_utils.potential_buyer_info_utils import PatentBuyerInfoUtils
from app.common.patent.patent_utils.tech_price_pred_utils import (
    TechValuePredictionModel,
    TECH_VALUE_PRED_MODEL_PATH
)
from app.common.patent.patent_utils.patent_search_utils import (
    PatentSearchUtils,
    COLUMN_NAMES1,
    COLUMN_NAMES2
)
from app.models.patent_models import (
    PatentGenerationRequest,
    PatentGenerationResponse,
    PotentialBuyersRequest,
    SimilarPatentsRequest,
    SimilarPatentIPCNetworKeywordRequest,
    SimilarPatentIPCNetworNLRequest,
    TechValueRequest,
    PatentResponse,
)

router = APIRouter()

# Initialize logger
file_path = FILE_PATHS["log"] + "patent"
make_dir(file_path)
file_path += f"/patent_{get_current_datetime()}.log"
logger = setup_logger("patent", file_path)

# Initialize utils
patent_gen_utils = PatentGenerationUtils()
patent_buyer_info_utils = PatentBuyerInfoUtils()
patent_search_utils = PatentSearchUtils()
tech_value_pred_utils = TechValuePredictionModel(TECH_VALUE_PRED_MODEL_PATH)


@router.post("/generation", response_model=PatentGenerationResponse)
async def generate_patent_draft(
    request: PatentGenerationRequest, token: str = Depends(verify_token)
):
    """특허 초안을 생성합니다.

    Args:
        request: 특허 초안 생성 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 생성된 특허 초안
    """
    try:
        result = await patent_gen_utils.generate_patent(request.userText)
        return result
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


@router.post("/potential-buyers", response_model=PatentResponse)
async def get_potential_buyers_info(
    request: PotentialBuyersRequest, token: str = Depends(verify_token)
):
    """특허에 대한 잠재적 구매자 정보를 조회합니다.

    Args:
        request: 잠재적 구매자 정보 조회 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 특허에 대한 잠재적 구매자 정보
    """
    try:
        result = patent_buyer_info_utils.get_corp_with_similar_patent(
            request.patentId, request.topK
            )
        return result
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


@router.post("/similar-patents", response_model=PatentResponse)
async def get_similar_patents_info(
    request: SimilarPatentsRequest, token: str = Depends(verify_token)
):
    """특허에 대한 유사 특허 정보를 조회합니다.

    Args:
        request: 유사 특허 정보 조회 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 특허에 대한 유사 특허 정보
    """
    try:
        async with patent_search_utils.get_es_client() as es:
            result = await patent_search_utils.search_es_patent_vector(
                es,
                query=request.userText,
                size=request.size,
                mode="nl",
                column_names=COLUMN_NAMES1
            )
            return result
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


@router.post("/ipc-network-kw", response_model=PatentResponse)
async def get_similar_patent_ipcs_by_keyword(
    request: SimilarPatentIPCNetworKeywordRequest, token: str = Depends(verify_token)
):
    """특허에 대한 IPC 네트워크 정보를 조회합니다.

    Args:
        request: IPC 네트워크 정보 조회 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 특허에 대한 IPC 네트워크 정보
    """
    try:
        async with patent_search_utils.get_es_client() as es:
            result = await patent_search_utils.search_es_patent_vector(
                es,
                query=request.keyword,
                size=request.size,
                mode="keyword",
                column_names=COLUMN_NAMES2,
            )
            return result
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


@router.post("/ipc-network-nl", response_model=PatentResponse)
async def get_similar_patent_ipcs_by_sentence(
    request: SimilarPatentIPCNetworNLRequest, token: str = Depends(verify_token)
):
    """특허에 대한 IPC 네트워크 정보를 조회합니다.

    Args:
        request: IPC 네트워크 정보 조회 요청 데이터
        token: 사용자 인증 토큰

    Returns:
        dict: 특허에 대한 IPC 네트워크 정보
    """
    try:
        async with patent_search_utils.get_es_client() as es:
            result = await patent_search_utils.search_es_patent_vector(
                es, query=request.userText, size=request.size, mode="nl", column_names=COLUMN_NAMES2
            )
            return result
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


@router.post("/price-pred", response_model=PatentResponse)
async def predict_tech_value(request: TechValueRequest, token: str = Depends(verify_token)):
    """기술에 대한 가격을 예측합니다."""
    try:
        tech_value_pred_utils.postprocess(
            tech_name=[request.techName],
            tech_description=[request.techDescription]
        )
        return tech_value_pred_utils.response_model
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
