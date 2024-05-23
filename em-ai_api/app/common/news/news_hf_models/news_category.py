import re
import traceback
from typing import Text

from icecream import ic

from app.config.ai_status_code import Success
from app.common.news.base.hf_model import HuggingFaceModel
from app.common.news.base.hf_model_utils import category_dumps
from app.common.core.utils import format_error_message
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError


class NewsCategoryModel(HuggingFaceModel):
    def __init__(self, model_id="illunex-ai/news-category-add", gpu_id: int = 0):
        """
        Description:
            뉴스 카테고리 분류 모델 클래스

        Args:
            model_id : 허깅페이스 모델 아이디 -> default: "illunex-ai/news-category-add"
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

    def postprocess(self, input_content: Text):
        """뉴스 본문을 입력받아 카테고리 분류를 결과를 후처리하는 기능

        Args:
            input_content : 뉴스 본문
        """
        try:
            self.validate_input(input_content)
            output = super().predict(input_text=input_content)
            output = category_dumps(output)
            self.response_model["status"] = "success"
            self.response_model["code"] = Success.SUCCESS["code"]
            self.response_model["message"] = Success.SUCCESS["message"]
            self.response_model["data"]["results"] = output
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
    content = """지난해 국내 4대 그룹(삼성·현대차·LG·SK그룹)의 영업이익이 전년 대비 65％ 넘게 폭락한 것으로 나타났다. 지난해 반도체·디스플레이 업황 부진이 전체 실적 악화로 연결된 모습이다. 현대차그룹은 삼성그룹을 제치고 합산 영업이익 1위에 올랐다.

기업분석 전문업체 한국CXO연구소는 이 같은 내용의 국내 4대 그룹 주요 계열사 영업이익 변동 현황 결과를 24일 발표했다. 지난해 이들 그룹이 공정거래위원회에 제출한 국내 계열사 현황 중 지난 19일까지 감사보고서나 사업보고서를 제출한 306개 업체가 대상이다. 영업이익은 별도 기준으로 취합됐다.

자료=한국CXO연구소

자료=한국CXO연구소

306개 업체의 작년 영업이익 총액은 24조5180억원이었다. 71조9182억원이었던 전년 대비 65.9％ 감소했다. 그룹별로는 삼성의 감소액이 가장 컸다. 조사 대상 계열사 59곳의 작년 영업이익은 2조8363억원에 그쳤다. 전년(38조7465억원) 대비 92.7％ 줄었다. 11조5262억원을 기록한 삼성전자의 작년 영업손실이 영향을 미쳤다. 같은 기간 영업이익이 흑자로 돌아선 삼성중공업, 영업이익이 1조2041억원을 기록해 1조원을 넘긴 삼성바이오로직스가 일부 실적을 방어했다.


SK그룹 계열사 135곳의 작년 영업이익 총액은 3조9162억원이다. 전년(19조1461억원) 대비 79.5％ 꺾였다. 작년 SK하이닉스가 4조6721억원의 영업적자를 기록했고, SK에너지도 영업이익이 2조원 넘게 줄어든 여파다. LG그룹은 지난해 영업이익 총액이 적자였다. 계열사 48곳의 합산 영업적자는 2707억원이다. LG전자가 5767억원으로 호실적을 기록했지만 LG디스플레이와 LG화학이 3조8841억원, 1091억원씩 적자를 기록했다.

현대차그룹은 유일하게 영업이익이 증가했다. 50개 계열사가 18조362억원을 벌어 전년(12조5827억원) 대비 43.3％ 늘었다. 이 중 현대자동차는 작년 영업이익이 6조6710억원을 기록해 조사 대상 기업 중 1위였다. 기아는 6조3056억원으로 뒤를 이었다. 두 회사 모두 3조원이 넘는 영업이익 증가가 있었다. 현대제철과 현대글로비스 영업이익이 각각 8143억원, 5391억원씩 줄었지만 현대자동차와 기아 덕분에 영향은 미미했다.

오일선 한국CXO연구소장은 "삼성과 SK, LG의 영업이익이 동반 하락하면서 위기감이 커지고 있다"며 "반도체 의존에서 탈피해 새로운 산업 장르를 개척하는 것이 중요해졌다"고 강조했다.

이시은 기자 see@hankyung.com"""
    model = NewsCategoryModel()
    model.postprocess(input_content=content)
    ic(model.response_model)
