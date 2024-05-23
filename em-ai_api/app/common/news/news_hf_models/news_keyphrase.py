import re
import traceback
from typing import Text

from icecream import ic

from app.config.ai_status_code import Success
from app.common.news.base.hf_model import HuggingFaceModel
from app.common.news.base.hf_model_utils import keyphrase_dumps, postprocess_keyphrase
from app.common.core.utils import format_error_message
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError
from app.config.custom_errors import DataNotFoundError


class NewsKeyphraseModel(HuggingFaceModel):
    def __init__(
        self, model_id="illunex-ai/news-keyphrase-large", gpu_id: int = 0
    ):
        """
        Description:
            뉴스 키워드 추출 모델 클래스

        Args:
            model_id : 허깅페이스 모델 아이디
                        -> default: "illunex-ai/news-keyphrase-large"
            gpu_id : gpu 아이디 -> default: 0
        """
        super().__init__(model_id, gpu_id)

    def validate_input(self, input_content: Text):
        """입력 텍스트의 유효성을 검사하는 함수

        Args:
            input_content : 사용자 입력 텍스트
        """
        # 입력 텍스트가 4000자를 초과하는 경우
        if len(input_content) > self.max_limit:
            raise ValueError
        # 입력 텍스트가 text가 아닌 경우
        elif not isinstance(input_content, str):
            raise TypeError
        # 입력 텍스트를 전달하지 않은 경우
        elif not input_content:
            raise KeyError
        elif input_content and len(re.sub(r"\s+", "", input_content)) < 10:
            raise ValueError
        else:
            pass

    def validate_output(self, output: list):
        """모델 출력의 유효성을 검사하는 함수

        Args:
            output : 모델 출력
        """
        if not output:
            raise DataNotFoundError('입력하신 기사에 추출된 키워드가 없습니다.')
        if isinstance(output, list):
            if set(output) in [{None}, {'None'}]:
                raise DataNotFoundError('입력하신 기사에 추출된 키워드가 없습니다.')


    def postprocess(self, input_content: Text):
        """뉴스 본문을 입력받아 키워드 추출 결과를 후처리하는 기능

        Args:
            input_content : 뉴스 본문
        """
        try:
            self.validate_input(input_content)
            output = super().predict(input_text=input_content)
            output = keyphrase_dumps(output)
            self.validate_output(output)
            output = postprocess_keyphrase(output)

            self.response_model["status"] = "success"
            self.response_model["code"] = Success.SUCCESS["code"]
            self.response_model["message"] = Success.SUCCESS["message"]
            self.response_model["data"]["results"] = output
        except DataNotFoundError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = (
                ServiceInternalError.DATA_NOT_FOUND_ERROR["code"])
            self.response_model["message"] = (
                format_error_message(
                    ServiceInternalError.DATA_NOT_FOUND_ERROR)
                + " 해당 기사에서 키워드를 찾을 수 없습니다."
            )
            self.logger.error(format_error_message(
                ServiceInternalError.DATA_NOT_FOUND_ERROR))
            ic(format_error_message(
                ServiceInternalError.DATA_NOT_FOUND_ERROR))
        except ValueError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = (
                ModelExecutionError.INPUT_LENGTH_ERROR["code"])
            self.response_model["message"] = format_error_message(
                ModelExecutionError.INPUT_LENGTH_ERROR)
            self.logger.error(format_error_message(
                ModelExecutionError.INPUT_LENGTH_ERROR))
            ic(format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR))
        except TypeError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = (
                ModelExecutionError.TYPE_ERROR["code"])
            self.response_model["message"] = format_error_message(
                ModelExecutionError.TYPE_ERROR)
            self.logger.error(
                format_error_message(ModelExecutionError.TYPE_ERROR))
            ic(format_error_message(ModelExecutionError.TYPE_ERROR))
        except KeyError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = (
                ModelExecutionError.MISSING_PARAMETER_ERROR["code"])
            self.response_model["message"] = format_error_message(
                ModelExecutionError.MISSING_PARAMETER_ERROR)
            self.logger.error(format_error_message(
                ModelExecutionError.MISSING_PARAMETER_ERROR))
            ic(format_error_message(
                ModelExecutionError.MISSING_PARAMETER_ERROR))
        except Exception as e:
            self.response_model['data']['results'] = []
            self.response_model["code"] = (
                ServiceInternalError.SERVICE_INTERNAL_ERROR["code"])
            self.response_model["message"] = format_error_message(
                ServiceInternalError.SERVICE_INTERNAL_ERROR)
            self.logger.error(format_error_message(
                ServiceInternalError.SERVICE_INTERNAL_ERROR))
            ic(format_error_message(
                ServiceInternalError.SERVICE_INTERNAL_ERROR))
            ic(traceback.format_exc())
            ic(e)


if __name__ == "__main__":
    content = """
(지디넷코리아=이정현 미디어연구소)애플이 올해 혼합현실 헤드셋 ‘비전 프로’의 출하량을 대폭 줄였다는 소식이 나왔다.

IT매체 맥루머스는 23일(현지시간) 애플 전문 분석가 궈밍치의 전망을 인용해 애플이 올해 비전 프로 헤드셋의 출하량을 40만~45만대로 낮춰 잡았다고 보도했다.

이 같은 수치는 기존 전망치인 70만~80만 대에 비해 크게 줄어든 것이다. 이 같은 변화로 인해 애플은 헤드셋 제품 로드맵을 재검토하고 있는 것으로 알려졌다. 때문에 예전에 2세대 비전 프로가 내년에 출시될 것으로 전망했으나 더 이상 그렇지 않을 수 있다고 궈밍치는 밝혔다.

그는 “애플이 헤드마운트디스플레이(HMD) 제품 로드맵을 검토 및 조정하고 있어 2025년에 새 비전 프로 모델이 없을 수 있다. 애플은 비전 프로 출하량이 2025년에 전년 대비 감소할 것으로 예상하고 있다”고 밝혔다.


또 그는 미국의 비전 프로 수요가 기대 이상으로 낮아 애플이 해외 출시에 대해 다소 보수적인 접근 방식을 취하게 될 것으로 예상했다.

예전에 궈밍치는 애플이 오는 6월 개최되는 WWDC24 행사 이전에 다른 나라에서 비전 프로를 출시할 것이라고 전망한 바 있다.

궈밍치는 애플의 비전 프로가 사용자 경험에 영향을 주지 않으면서 핵심 애플리케이션, 가격, 편의성의 부족을 해결하기 위해 노력해야 한다고 밝히며, 예상보다 줄어든 비전 프로 판매량은 팬케이크 렌즈의 성장과 소형 가전제품의 마이크로OLED 디스플레이 기술 채택에 영향을 미칠 것으로 예상된다고 설명했다.

이정현 미디어연구소(jh7253@zdnet.co.kr)
"""
    model = NewsKeyphraseModel()
    model.postprocess(input_content=content)
    ic(model.response_model)
