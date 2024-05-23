import json
from typing import Any, List, Optional, Sequence, Tuple, Union

from langchain_core.prompts import BasePromptTemplate
from langchain_core.prompts.few_shot import FewShotPromptTemplate
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.chains.query_constructor.ir import (
    Comparator,
    Operator,
)
from langchain.chains.query_constructor.prompt import (
    DEFAULT_EXAMPLES,
    DEFAULT_PREFIX,
    DEFAULT_SCHEMA_PROMPT,
    DEFAULT_SUFFIX,
    EXAMPLE_PROMPT,
    EXAMPLES_WITH_LIMIT,
    PREFIX_WITH_DATA_SOURCE,
    SCHEMA_WITH_LIMIT_PROMPT,
    SUFFIX_WITHOUT_DATA_SOURCE,
    USER_SPECIFIED_EXAMPLE_PROMPT,
)


def _format_attribute_info(info: Sequence[Union[AttributeInfo, dict]]) -> str:
    """attribute_info를 json 형식으로 변환.

    Args:
        info: 문서의 속성 정보.

    Returns:
        json 형식의 attribute_info
    """
    info_dicts = {}
    for i in info:
        i_dict = dict(i)
        info_dicts[i_dict.pop("name")] = i_dict
    return (
        json.dumps(info_dicts, indent=4, ensure_ascii=False)
        .replace("{", "{{")
        .replace("}", "}}")
    )


def construct_examples(input_output_pairs: Sequence[Tuple[str, dict]]) -> List[dict]:
    """input_output_pairs를 example 형식으로 변환.

    Args:
        input_output_pairs: input과 output의 쌍.

    Returns:
        List of examples.
    """
    examples = []
    for i, (_input, output) in enumerate(input_output_pairs):
        structured_request = (
            json.dumps(output, indent=4, ensure_ascii=False)
            .replace("{", "{{")
            .replace("}", "}}")
        )  # ensure_ascii=False example 한글 안 깨지게 옵션 변경
        example = {
            "i": i + 1,
            "user_query": _input,
            "structured_request": structured_request,
        }
        examples.append(example)
    return examples


def get_query_constructor_prompt_test(
    document_contents: str,
    attribute_info: Sequence[Union[AttributeInfo, dict]],
    *,
    examples: Optional[Sequence] = None,
    allowed_comparators: Sequence[Comparator] = tuple(Comparator),
    allowed_operators: Sequence[Operator] = tuple(Operator),
    enable_limit: bool = False,
    schema_prompt: Optional[BasePromptTemplate] = None,
    **kwargs: Any,
) -> BasePromptTemplate:
    """쿼리 생성을 위한 prompt template 생성.

    Args:
        document_contents: 쿠리 생성을 위한 문서 내용.
        attribute_info: 문서의 속성 정보.
        examples: 예시들.
        allowed_comparators: 허용되는 비교자.
        allowed_operators: 허용되는 연산자.
        enable_limit: limit 활성화 여부.
        schema_prompt: schema prompt.
        kwargs: 기타 설정.

    Returns:
        쿼리 생성을 위한 prompt template.
    """
    default_schema_prompt = (
        SCHEMA_WITH_LIMIT_PROMPT if enable_limit else DEFAULT_SCHEMA_PROMPT
    )
    schema_prompt = schema_prompt or default_schema_prompt
    attribute_str = _format_attribute_info(attribute_info)
    schema = schema_prompt.format(
        allowed_comparators=" | ".join(allowed_comparators),
        allowed_operators=" | ".join(allowed_operators),
    )
    if examples and isinstance(examples[0], tuple):
        examples = construct_examples(examples)
        example_prompt = USER_SPECIFIED_EXAMPLE_PROMPT
        prefix = PREFIX_WITH_DATA_SOURCE.format(
            schema=schema, content=document_contents, attributes=attribute_str
        )
        suffix = SUFFIX_WITHOUT_DATA_SOURCE.format(i=len(examples) + 1)
    else:
        examples = examples or (
            EXAMPLES_WITH_LIMIT if enable_limit else DEFAULT_EXAMPLES
        )
        example_prompt = EXAMPLE_PROMPT
        prefix = DEFAULT_PREFIX.format(schema=schema)
        suffix = DEFAULT_SUFFIX.format(
            i=len(examples) + 1, content=document_contents, attributes=attribute_str
        )
    return FewShotPromptTemplate(
        examples=list(examples),
        example_prompt=example_prompt,
        input_variables=["query"],
        suffix=suffix,
        prefix=prefix,
        **kwargs,
    )
