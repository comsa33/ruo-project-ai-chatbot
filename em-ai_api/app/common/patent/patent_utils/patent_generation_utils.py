import os
import re
import json
import httpx
import asyncio
import traceback

from dotenv import dotenv_values
from icecream import ic
from openai import AsyncAzureOpenAI, APIConnectionError, AsyncOpenAI

from app.common.patent.base.patent_utils import call_patent_api, generate_plantuml_url
from app.common.patent.base.prompts import PATENT_GEN_INST_PROMPT
from app.common.core.utils import format_error_message, snake_to_camel
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError, Success
from app.config.settings import API_ADDRESS
from app.config.custom_errors import ModelPredictionError


MIN_INPUT_LENGTH = 10

PATENT_CLAIM_GEN_FAIL_MSG = "특허 청구항 생성에 실패했습니다."
DIAGRAM_GEN_FAIL_MSG = "특허 기능 분석도 생성에 실패했습니다."
TYPE_ERROR_MESSAGE = "입력값은 문자열이어야 합니다."
NO_INPUT_ERROR_MESSAGE = "입력값이 없습니다."
INPUT_LENGTH_ERROR_MESSAGE = f"입력값이 너무 짧습니다. {MIN_INPUT_LENGTH}자 이상이어야 합니다."


class PatentGenerationUtils:
    def __init__(self):
        self.config = dotenv_values(".env")
        self.openai_mode = os.getenv("OPENAI_MODE")

    async def call_gpt_and_generate_patent_draft(self, question: str) -> dict:
        """GPT-4를 호출하여 특허 초안을 생성합니다.

        Args:
            question: 프롬프트 및 질의 내용

        Returns:
            dict: 생성된 특허 초안
        """

        if self.openai_mode == "openai":
            client = AsyncOpenAI(
                api_key=self.config["OPENAI_API_KEY"],
            )
            model_name = self.config["OPENAI_MODEL"]
        elif self.openai_mode == "azure":
            client = AsyncAzureOpenAI(
                azure_endpoint=self.config["AZURE_OPENAI_ENDPOINT"],
                api_key=self.config["AZURE_OPENAI_API_KEY"],
                api_version=self.config["AZURE_OPENAI_API_VERSION"],
            )
            model_name = self.config["AZURE_OPENAI_MODEL"]

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Act like an expert in patent. your result is like this. "
                    + PATENT_GEN_INST_PROMPT,
                },
                {"role": "user", "content": "아이디어를 입력하면 특허 초안을 만들어 주시겠어요."},
                {"role": "assistant", "content": "아이디어를 입력하시면 초안을 만들어 드리겠습니다."},
                {
                    "role": "user",
                    "content": "아래 아이디어를 차분히 잘 읽고 양식에 맞춰 초안을 만들어줘.\n"
                    + question,
                },
            ],
            temperature=0,
        )
        json_text = re.search(r"{.*}", response.choices[0].message.content, re.DOTALL).group(0)
        return json.loads(json_text)

    async def call_gen_claim_api(self, text: str) -> dict:
        """특허 청구항 생성 API를 호출합니다.

        Args:
            text: 특허 청구항 생성에 사용할 텍스트

        Returns:
            dict: 생성된 특허 청구항
        """
        patent_claim = ""
        endpoint = API_ADDRESS["patent_claim_gen"]
        ok, result = call_patent_api(endpoint, {"inputs": [text]})
        if not ok:
            return {"patent_claim": PATENT_CLAIM_GEN_FAIL_MSG}
        if result["status"] == 0:
            patent_claim = result["result"][0]
        else:
            error_message = result["message"]
            ic(error_message)
        return {"patent_claim": patent_claim}

    async def call_gen_diagram_api(self, text: str) -> dict:
        """특허 기능 분석도 생성 API를 호출합니다.

        Args:
            text: 특허 기능 분석도 생성에 사용할 텍스트

        Returns:
            dict: 생성된 특허 기능 분석도
        """
        endpoint = API_ADDRESS["patent_function_diagram"]
        ok, result = call_patent_api(endpoint, {"content": [text]})
        if not ok:
            return {"diagramUrl": DIAGRAM_GEN_FAIL_MSG, "keywords": []}
        result = json.loads(result).get("result")
        if not result:
            return {"diagramUrl": "", "keywords": []}
        if ok:
            plantuml_code = result.pop("dialogues")
            result["diagramUrl"] = generate_plantuml_url(plantuml_code)
        return result

    def validate_input(self, question: str):
        """특허 초안 생성 입력값 유효성 검사

        Args:
            question: 질의 내용

        Raises:
            TypeError: 입력값이 문자열이 아닌 경우
            ValueError: 입력값이 없는 경우
        """
        if not isinstance(question, str):
            raise TypeError(TYPE_ERROR_MESSAGE)
        if question == "":
            raise ValueError(NO_INPUT_ERROR_MESSAGE)
        if len(question) < MIN_INPUT_LENGTH:
            raise ValueError(INPUT_LENGTH_ERROR_MESSAGE)

    async def generate_patent(self, question: str) -> dict:
        """특허 초안을 생성합니다.

        Args:
            question: 프롬프트 및 질의 내용

        Returns:
            dict: 생성된 특허 초안
        """
        response = {
            "status": "fail",
            "code": 666,
            "message": "특허 초안 생성에 실패했습니다.",
            "data": {"results": []},
        }
        try:
            self.validate_input(question)

            gpt_resp = await self.call_gpt_and_generate_patent_draft(question)
            gen_abstract = gpt_resp.get('abstract', None)
            if not gen_abstract:
                raise ModelPredictionError("GPT-4 API에서 반환된 결과가 없습니다.")
            claim_resp, diagram_resp = await asyncio.gather(
                self.call_gen_claim_api(gen_abstract),
                self.call_gen_diagram_api(gen_abstract)
            )
            
            response["data"]["results"] = [{}]
            response["data"]["results"][0].update(gpt_resp)
            response["data"]["results"][0].update(claim_resp)
            response["data"]["results"][0].update(diagram_resp)
            # data>results 안에 있는 key를 snake_case를 camelCase로 변환
            response["data"]["results"][0] = {
                snake_to_camel(key): value
                for key, value in response["data"]["results"][0].items()
            }
            response["status"] = "success"
            response["message"] = Success.SUCCESS["message"]
            response["code"] = Success.SUCCESS["code"]
        except ValueError as e:
            response["data"]["results"] = [{}]
            response["message"] = format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR) + str(e)
            response["code"] = ModelExecutionError.INPUT_LENGTH_ERROR["code"]
        except ModelPredictionError as e:
            response["data"]["results"] = [{}]
            response["message"] = format_error_message(ModelExecutionError.MODEL_PREDICTION_ERROR) + str(e)
            response["code"] = ModelExecutionError.MODEL_PREDICTION_ERROR["code"]
        except json.JSONDecodeError:
            response["data"]["results"] = [{}]
            response["message"] = format_error_message(ModelExecutionError.MODEL_PREDICTION_ERROR)
            response["code"] = ModelExecutionError.MODEL_PREDICTION_ERROR["code"]
        except APIConnectionError:
            response["data"]["results"] = [{}]
            response["message"] = format_error_message(ModelExecutionError.API_CONNECTION_ERROR)
            response["code"] = ModelExecutionError.API_CONNECTION_ERROR["code"]
        except httpx.ConnectError:
            response["data"]["results"] = [{}]
            response["message"] = format_error_message(ModelExecutionError.API_CONNECTION_ERROR)
            response["code"] = ModelExecutionError.API_CONNECTION_ERROR["code"]
        except httpx.HTTPStatusError as http_err:
            if http_err.response.status_code == 401:
                response["data"]["results"] = [{}]
                response["message"] = format_error_message(ModelExecutionError.AUTHENTICATION_ERROR)
                response["code"] = ModelExecutionError.AUTHENTICATION_ERROR["code"]
            else:
                response["data"]["results"] = [{}]
                response["message"] = format_error_message(ModelExecutionError.API_CONNECTION_ERROR)
                response["code"] = ModelExecutionError.API_CONNECTION_ERROR["code"]
            ic(f"HTTP Error : {http_err}")
            ic(f"HTTP Error : {traceback.format_exc()}")
        except Exception as e:
            response["data"]["results"] = [{}]
            response["message"] = format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR)
            response["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            ic(e)
            ic(traceback.format_exc())
        return response


if __name__ == "__main__":
    from app.common.core.utils import profile_async_func

    os.environ["OPENAI_MODE"] = "azure"

    question = (
        "뚜껑을 선회시켜 점화하는 라이타에 관한 발명으로, 본체 내부에 가스통과 점화를 위한 압전장치를 구비,"
        "뚜껑을 피봇축을 중심으로 선회시켜 점화된다. 회전식 뚜껑으로 다양한 디자인이 가능하다."
    )
    patent_gen = PatentGenerationUtils()
    # response = profile_async_func(patent_gen.generate_patent, question)
    response = asyncio.run(patent_gen.generate_patent(question))
    ic(response)
