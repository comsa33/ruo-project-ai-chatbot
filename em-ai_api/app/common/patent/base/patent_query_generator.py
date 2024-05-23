import os
import traceback

from dotenv import dotenv_values
from icecream import ic
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.retrievers.self_query.elasticsearch import ElasticsearchTranslator
from langchain.chains.query_constructor.base import AttributeInfo, StructuredQueryOutputParser

from app.config.custom_errors import DataNotFoundError
from app.common.patent.base.query_generator_utils import get_query_constructor_prompt_test
from app.common.patent.base.prompts import (
    PATENT_META_FIELD_INFO,
    PATENT_QUERY_FEW_SHOT_EXAMPLES,
    PATENT_DOC_CONTENT_DESC,
)


config = dotenv_values(".env")

# 특허 문서의 메타데이터 필드 정보
metadata_field_info = [
    AttributeInfo(name=field["name"], description=field["description"], type=field["type"])
    for field in PATENT_META_FIELD_INFO
]

# 프롬프트 : 구조화된 쿼리 생성을 위한 프롬프트 생성
prompt = get_query_constructor_prompt_test(
    document_contents=PATENT_DOC_CONTENT_DESC,
    attribute_info=metadata_field_info,
    examples=PATENT_QUERY_FEW_SHOT_EXAMPLES,
)

openai_mode = os.getenv("OPENAI_MODE")
if openai_mode == "azure":
    # Azure Chat OpenAI : Azure Chat OpenAI 모델을 사용하여 구조화된 쿼리 생성
    llm = AzureChatOpenAI(
        azure_deployment=config["AZURE_OPENAI_MODEL"],
        azure_endpoint=config["AZURE_OPENAI_ENDPOINT"],
        api_key=config["AZURE_OPENAI_API_KEY"],
        api_version=config["AZURE_OPENAI_API_VERSION"],
        temperature=0,
    )
elif openai_mode == "openai":
    # Chat OpenAI : Chat OpenAI 모델을 사용하여 구조화된 쿼리 생성
    llm = ChatOpenAI(
        api_key=config["OPENAI_API_KEY"],
        model=config["OPENAI_MODEL"],
        temperature=0,
    )

# 파서 : 구조화된 쿼리 출력을 파싱
output_parser = StructuredQueryOutputParser.from_components()

# 체인 : 프롬프트 -> Azure Chat OpenAI -> 파서 순으로 체인을 구성
query_constructor = prompt | llm | output_parser


def generate_es_query_from_nl_query(nl_query: str) -> dict:
    """자연어 질의를 Elasticsearch query로 변환.

    Args:
        nl_query (str): 자연어 질의

    Returns:
        dict: Elasticsearch query
    """
    try:
        structured_query = query_constructor.invoke(
            {"query": nl_query}, config={"fix_invalid": True}
        )
        # Elasticsearch Translator : 구조화된 쿼리를 Elasticsearch 쿼리로 변환
        translator = ElasticsearchTranslator()
        es_translated_query = translator.visit_structured_query(structured_query)
        return {"status": "success", "filter": es_translated_query[1]["filter"], "keywords": es_translated_query[0]}
    except KeyError:
        raise DataNotFoundError(" 검색 결과가 없습니다. 다른 검색어로 시도해주세요.")
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        return {"status": "fail", "filter": None, "keywords": None}


if __name__ == "__main__":
    nl_query = (
        "2023년에 출원된 2차전지 관련된 특허를 찾아줘"
    )
    result = generate_es_query_from_nl_query(nl_query)
    ic(result)
