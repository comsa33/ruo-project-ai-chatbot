import re
import ast
import traceback
from typing import Text

from icecream import ic

from app.config.ai_status_code import Success
from app.common.news.base.hf_model import HuggingFaceModel
from app.common.news.base.hf_model_utils import text_normalize
from app.common.core.utils import format_error_message, snake_to_camel
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError
from app.config.custom_errors import DataNotFoundError


class NewsInvestmentModel(HuggingFaceModel):
    def __init__(self, model_id="illunex-ai/news_investment_extract", gpu_id: int = 1):
        """
        Description:
            뉴스 투자 분석 모델 클래스

        Args:
            model_id : 허깅페이스 모델 아이디 -> default: "illunex-ai/news_investment_extract"
            gpu_id : gpu 아이디 -> default: 1

        """
        super().__init__(model_id, gpu_id)

    def validate_input(self, input_title: Text, input_content: Text):
        """입력 텍스트의 유효성을 검사하는 함수

        Args:
            input_title : 뉴스 제목
            input_content : 뉴스 본문
        """
        # 입력 텍스트가 4000자를 초과하는 경우
        if len(input_title) + len(input_content) > self.max_limit:
            raise ValueError
        # 입력 텍스트가 text가 아닌 경우
        elif not isinstance(input_title, str) or not isinstance(input_content, str):
            raise TypeError
        # 입력 텍스트를 전달하지 않은 경우
        elif not input_title or not input_content:
            raise KeyError
        elif input_title and len(re.sub(r"\s+", "", input_title)) < 5:
            raise ValueError
        elif input_content and len(re.sub(r"\s+", "", input_content)) < 10:
            raise ValueError
        else:
            pass

    def validate_output(self, output: dict):
        """모델 출력의 유효성을 검사하는 함수

        Args:
            output : 모델 출력
        """
        if not output:
            raise DataNotFoundError('입력하신 기사에 투자 정보가 없습니다.')
        if not isinstance(output, dict):
            raise DataNotFoundError('입력하신 기사에 투자 정보가 없습니다.')
        if isinstance(output, dict):
            if not any(output.values()):
                raise DataNotFoundError('입력하신 기사에 투자 정보가 없습니다.')

    def postprocess(self, input_title: Text, input_content: Text):
        """뉴스 본문과 제목을 입력받아 투자 분석 결과를 후처리하는 기능

        Args:
            input_title : 뉴스 제목
            input_content : 뉴스 본문
        """
        try:
            self.validate_input(input_title, input_content)
            input_text = "title: {}\ncontent: {}".format(
                text_normalize(input_title), text_normalize(input_content)
            )

            output = super().predict(input_text=input_text)
            print("output ck : \n","".join(output))
            output = ast.literal_eval("".join(output))

            self.validate_output(output)
            self.response_model["data"]["results"] = [output]
            # data>results 안에 있는 key를 snake_case를 camelCase로 변환
            self.response_model["data"]["results"] = [
                {snake_to_camel(key): value for key, value in result.items()}
                for result in self.response_model["data"]["results"]
            ]
            self.response_model["status"] = "success"
            self.response_model["code"] = Success.SUCCESS["code"]
            self.response_model["message"] = Success.SUCCESS["message"]
        except SyntaxError as syn_error:
            # SyntaxError는 데이터 구조 생성 실패로 간주
            ic(f"Syntax Error 발생 {syn_error}")
            ic(traceback.format_exc())
            self.response_model["data"]["results"] = []
            self.response_model["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
            self.response_model["message"] = (
                format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                + " 해당 기사에서 투자 정보를 찾을 수 없습니다."
            )
            self.logger.error(format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR))
            ic(format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR))
        except DataNotFoundError:
            self.response_model["data"]["results"] = []
            self.response_model["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
            self.response_model["message"] = (
                format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                + " 해당 기사에서 투자 정보를 찾을 수 없습니다."
            )
            self.logger.error(format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR))
            ic(format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR))
        except ValueError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ModelExecutionError.INPUT_LENGTH_ERROR["code"]
            self.response_model["message"] = (
                format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR))
            self.logger.error(format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR))
            ic(format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR))
        except TypeError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ModelExecutionError.TYPE_ERROR["code"]
            self.response_model["message"] = format_error_message(ModelExecutionError.TYPE_ERROR)
            self.logger.error(format_error_message(ModelExecutionError.TYPE_ERROR))
            ic(format_error_message(ModelExecutionError.TYPE_ERROR))
        except KeyError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ModelExecutionError.MISSING_PARAMETER_ERROR["code"]
            self.response_model["message"] = (
                format_error_message(ModelExecutionError.MISSING_PARAMETER_ERROR))
            self.logger.error(format_error_message(ModelExecutionError.MISSING_PARAMETER_ERROR))
            ic(format_error_message(ModelExecutionError.MISSING_PARAMETER_ERROR))
        except Exception as e:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            self.response_model["message"] = (
                format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR))
            self.logger.error(format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR))
            ic(format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR))
            ic(traceback.format_exc())
            ic(e)


if __name__ == "__main__":
    title = "헤이딜러, 450억원 시리즈D 투자 유치"
    content = """
중고차 플랫폼 헤이딜러를 운영하는 스타트업 피알앤디컴퍼니가 450억 원에 이르는 외부 투자를 유치했다고 5일 알렸다.

이번 투자는 산업은행, 에이티넘인베스트먼트, IMM인베스트먼트 등 다수 기관이 참여했다. 이들 기관은 최근 출시한 ‘중고차 숨은이력 찾기’와 같은 신규 서비스의 성장성을 높이 평가했다. 중고차 정보의 투명화가 중고차 시장을 확대시킬 것으로 투자사들에게 인정받았는 것이다.

한 투자사 측은 “헤이딜러 제로 등 쉽고 편하게 중고차를 판매할 수 있는 서비스로 단기간에 회사가 성장했다”고 말했다. 헤이딜러 측은 “이번 투자 유치로 중고차 시장의 문제를 해결하는데 더 집중할 계획"이라고 밝혔다.

2014년 설립된 헤이딜러는 고객 중심 사용자인터페이스(UI)와 효율적인 마케팅에 힘입어 빠르게 성장했다. 2024년 1월 기준 헤이딜러의 누적 가입자는 1300만 명이며 누적 거래액은 10조 원을 돌파했다.

"""
    model = NewsInvestmentModel()
    model.postprocess(input_title=title, input_content=content)
    ic(model.response_model)
