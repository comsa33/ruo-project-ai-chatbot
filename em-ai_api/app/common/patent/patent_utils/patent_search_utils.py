import traceback
from contextlib import asynccontextmanager

from icecream import ic
from FlagEmbedding import BGEM3FlagModel
from elasticsearch import (
    AsyncElasticsearch,
    ApiError,
    NotFoundError,
    ConnectionError,
    ConnectionTimeout,
    AuthenticationException,
    AuthorizationException,
)

from app.common.core.utils import debug_ic, snake_to_camel
from app.config.settings import ES_CLOUD_ID, ES_API_KEY
from app.config.custom_errors import ModelPredictionError
from app.common.patent.base.patent_query_generator import generate_es_query_from_nl_query
from app.config.custom_errors import DataNotFoundError
from app.config.ai_status_code import (
    ModelExecutionError,
    ServiceInternalError,
    Success,
)

# 상수 정의
INDEX_NAME = "em_ai_patent_vector_index_v1"
VECTOR_FIELD = "embedding"
TEXT_FIELD = "text"
COLUMN_NAMES1 = [
    "applicate_number",
    "applicate_date",
    "applicate_nation",
    "invention_title",
    "ipcs",
    "register_number",
    "lrh_name",
]
COLUMN_NAMES2 = ["applicate_number", "invention_title", "ipcs"]
SEARCH_SIZE = 10

NOT_STRING_ERROR_MSG = "입력값이 문자열이 아닙니다."
NO_INPUT_ERROR_MSG = "입력값이 없습니다."
QUERY_GENERATION_FAIL_MSG = " AI가 쿼리 생성에 실패했습니다. 다시 시도해주세요."
ES_API_ERROR_MSG = "Elasticsearch API 에러가 발생했습니다."
ES_NOT_FOUND_MSG = "검색 결과가 없습니다."
ES_CONNECTION_ERROR_MSG = "Elasticsearch 연결 에러가 발생했습니다."
ES_TIMEOUT_ERROR_MSG = "Elasticsearch 연결 시간이 초과되었습니다."
ES_AUTH_ERROR_MSG = "Elasticsearch 인증 에러가 발생했습니다."
ES_AUTHZ_ERROR_MSG = "Elasticsearch 권한 에러가 발생했습니다."
ES_DATA_NOT_FOUND_MSG = "검색 결과가 없습니다."


def _get_embedding_model(model_name):
    return BGEM3FlagModel(model_name, use_fp16=False, device="cpu")


class PatentSearchUtils:
    def __init__(self):
        self.model = _get_embedding_model("BAAI/bge-m3")

    @asynccontextmanager
    async def get_es_client(self):
        """Elasticsearch 클라이언트를 생성하는 context manager.

        Yields:
            AsyncElasticsearch: Elasticsearch 클라이언트
        """
        es = AsyncElasticsearch(
            cloud_id=ES_CLOUD_ID,
            api_key=ES_API_KEY,
            request_timeout=60,
            retry_on_timeout=True,
            max_retries=3,
        )
        try:
            yield es
        finally:
            await es.close()

    def _get_knn(self, vector: list, query: str, size: int) -> dict:
        return {
            "field": VECTOR_FIELD,
            "query_vector": vector,
            "k": size,
            "num_candidates": max(100, size * 5),
            "filter": {"match": {"text": query}},
        }

    def filter_search_result(self, hits: list, results: list, column_names: list) -> list:
        """검색 결과 필터링

        Args:
            hits (list): 검색 결과
            results (list): 결과 리스트
            column_names (list): 결과 필드명

        Returns:
            list: 필터링된 결과 리스트
        """
        for hit in hits:
            data = {}
            score = round(hit["_score"], 4) * 100
            data["score"] = format(score, ".2f")  # 소수점 이하 두 자리로 포맷
            metadata = hit["_source"]["metadata"]
            for column in column_names:
                data[column] = metadata[column]
            results.append(data)
        return results

    def validate_input(self, query: str):
        """검색 질의 유효성 검사

        Args:
            query (str): 검색 질의

        Raises:
            TypeError: 입력값이 문자열이 아닌 경우
            ValueError: 입력값이 없는 경우
        """
        if not isinstance(query, str):
            raise TypeError(NOT_STRING_ERROR_MSG)
        if query == "":
            raise ValueError(NO_INPUT_ERROR_MSG)

    async def search_es_patent_vector(
        self,
        es: AsyncElasticsearch,
        query: str,
        size: int = SEARCH_SIZE,
        mode: str = "keyword",  # 'keyword' or 'nl'
        column_names: list = COLUMN_NAMES1,
    ) -> dict:
        """knn 검색과 텍스트 검색을 혼합하여 수행합니다.

        Args:
            es (AsyncElasticsearch): Elasticsearch 클라이언트
            query (str): 검색 질의
            size (int, optional): 검색 결과 수. Defaults to SEARCH_SIZE.
            mode (str, optional): 검색 모드. Defaults to "keyword". 'keyword' or 'nl'
            column_names (list, optional): 결과 필드명. Defaults to COLUMN_NAMES1. COLUMN_NAMES1 or COLUMN_NAMES2
        Returns:
            dict: 검색 결과
        """
        response = {
            "status": "fail",
            "code": 666,
            "message": "검색에 실패했습니다.",
            "data": {"results": []},
        }
        try:
            self.validate_input(query)
            if mode == "nl":
                result = generate_es_query_from_nl_query(query)
                if result["status"] == "success":
                    es_filter_gen = result["filter"][0]
                    es_keyword_gen = result["keywords"]
                    query_vector = self.model.encode(result["keywords"])["dense_vecs"]
                    es_knn = self._get_knn(query_vector, es_keyword_gen, size)
                    if es_filter_gen["bool"].get("must"):
                        es_filter_gen["bool"]["must"].append({"match": {"text": es_keyword_gen}})
                    else:
                        es_filter_gen["bool"]["must"] = [{"match": {"text": es_keyword_gen}}]
                    es_knn["filter"] = es_filter_gen
                    debug_ic(es_knn)
                else:
                    raise ModelPredictionError(QUERY_GENERATION_FAIL_MSG)
            elif mode == "keyword":
                query_vector = self.model.encode(query)["dense_vecs"]
                es_knn = self._get_knn(query_vector, query, size)

            es_result = await es.search(
                index=INDEX_NAME,
                knn=es_knn,
                size=size
            )
            hits = es_result["hits"]["hits"]
            response["data"]["results"] = self.filter_search_result(
                hits, response["data"]["results"], column_names
            )
            if not response["data"]["results"]:
                raise DataNotFoundError(ES_DATA_NOT_FOUND_MSG)
            # data>results 안에 있는 key를 snake_case를 camelCase로 변환
            response["data"]["results"] = [
                {snake_to_camel(key): value for key, value in result.items()}
                for result in response["data"]["results"]
            ]
            response["status"] = "success"
            response["code"] = Success.SUCCESS["code"]
            response["message"] = "검색에 성공했습니다."
        except DataNotFoundError as e:
            response["data"]["results"] = []
            response["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
            response["message"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["message"] + str(e)
        except ModelPredictionError as e:
            response["data"]["results"] = []
            response["code"] = ModelExecutionError.MODEL_PREDICTION_ERROR["code"]
            response["message"] = ModelExecutionError.MODEL_PREDICTION_ERROR["message"] + str(e)
        except ValueError as e:
            response["data"]["results"] = []
            response["message"] = ModelExecutionError.INPUT_LENGTH_ERROR["message"] + str(e)
            response["code"] = ModelExecutionError.INPUT_LENGTH_ERROR["code"]
        except TypeError as e:
            response["data"]["results"] = []
            response["code"] = ModelExecutionError.TYPE_ERROR["code"]
            response["message"] = ModelExecutionError.TYPE_ERROR["message"] + str(e)
        except ApiError as e:
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            response["message"] = ES_API_ERROR_MSG + f" {e}"
        except NotFoundError as e:
            response["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
            response["message"] = ES_NOT_FOUND_MSG + f" {e}"
        except ConnectionError as e:
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            response["message"] = ES_CONNECTION_ERROR_MSG + f" {e}"
        except ConnectionTimeout as e:
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            response["message"] = ES_TIMEOUT_ERROR_MSG + f" {e}"
        except AuthenticationException as e:
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            response["message"] = ES_AUTH_ERROR_MSG + f" {e}"
        except AuthorizationException as e:
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            response["message"] = ES_AUTHZ_ERROR_MSG + f" {e}"
        except Exception as e:
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            response["message"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["message"] + f" {e}"
            ic(traceback.format_exc())
        return response


if __name__ == "__main__":
    import asyncio

    patent_search_utils = PatentSearchUtils()

    async def main(query, mode, size=SEARCH_SIZE):
        async with patent_search_utils.get_es_client() as es:
            es_result = await patent_search_utils.search_es_patent_vector(
                es, query, mode=mode, size=size
                )
            ic(es_result)

    size = 10
    modes = ["nl", "keyword"]
    nl_test_cases = [
            (
                "뚜껑을 선회시켜 점화하는 라이타에 관한 발명으로, 본체 내부에"
                "가스통과 점화를 위한 압전장치를 구비, 뚜껑을 피봇축을 중심으로 선회시켜 점화된다."
                "회전식 뚜껑으로 다양한 디자인이 가능하다."
            ),
            "2010년 이후 나온 사용자의 건강 상태를 지속적으로 모니터링하고 분석하는 스마트 웨어러블 기기",
            "최근 5년 이내 반도체 검사용 초음파 장치 관련 특허를 보여줘",
            "출원된 이차전지 관련된 특허중 2023년에 출원된 것들을 찾아줘",
            "2010년 상반기에 출원된 2차전지 관련 특허를 찾아줘",
            "2020년과 2023년에 출원된 이차전지 관련 특허를 찾아줘",
            "aaa"
        ]
    kw_test_cases = [
        "뚜껑 선회 라이터",
        "스마트 웨어러블 기기",
        "반도체 검사용 초음파 장치",
        ]
    asyncio.run(main(nl_test_cases[-1], modes[0], size))
