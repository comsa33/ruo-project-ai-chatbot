import re
import traceback
from typing import Text

from icecream import ic

from app.config.ai_status_code import Success
from app.common.news.base.hf_model import HuggingFaceModel
from app.common.news.base.hf_model_utils import esg_dumps
from app.common.core.utils import format_error_message
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError
from app.config.custom_errors import DataNotFoundError


class NewsESGModel(HuggingFaceModel):
    def __init__(self, model_id="illunex-ai/news-esg-qlora", gpu_id: int = 1):
        """
        Description:
            뉴스 ESG 분석 모델 클래스

        Args:
            model_id : 허깅페이스 모델 아이디 -> default: "illunex-ai/news-esg-qlora"
            gpu_id : gpu 아이디 -> default: 1

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

    def validate_output(self, output: dict):
        """모델 출력의 유효성을 검사하는 함수

        Args:
            output : 모델 출력
        """
        if not output:
            raise DataNotFoundError('입력하신 기사에 ESG 정보가 없습니다.')
        if isinstance(output, dict):
            if set(output) in [{None}, {'None'}]:
                raise DataNotFoundError('입력하신 기사에 ESG 정보가 없습니다.')

    def postprocess(self, input_content: Text):
        """뉴스 본문을 입력받아 ESG 분석 결과를 후처리하는 기능

        Args:
            input_content : 뉴스 본문
        """
        try:
            self.validate_input(input_content)
            output = super().predict(input_text=input_content)
            output = ''.join(output)
            output = esg_dumps(output)
            self.validate_output(output)

            self.response_model["status"] = "success"
            self.response_model["code"] = Success.SUCCESS["code"]
            self.response_model["message"] = Success.SUCCESS["message"]
            self.response_model["data"]["results"] = [output]
        except DataNotFoundError as e:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
            self.response_model["message"] = format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
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
    from app.common.core.utils import debug_ic, profile_func

    content = """
[파이낸셜뉴스] 이차전지 업종이 올해 들어 약세를 거듭하면서 시가총액이 50조원 가까이 증발한 것으로 나타났다. 이달 들어 주가가 반등하고 있는데 낙폭이 컸던 만큼 수급이 잠시 옮겨온 것이라는 분석도 나온다. 22일 한국거래소에 따르면 코스피·코스닥시장 합산 시가총액 상위 50위 안에 드는 이차전지 8개 종목의 시총 합산은 연초 294조8279억원에서 22일 246조9271억원으로 47조9008억원이 감소했다. 포함된 종목은 LG에너지솔루션, 포스코홀딩스, 삼성SDI, LG화학, 에코프로비엠, 포스코퓨처엠, 에코프로, SK이노베이션이다. 시총 순위(코스·코스닥 합산)도 줄줄이 밀려났다. 포스코홀딩스는 7위에서 9위로, 포스코퓨처엠은 14위에서 19위로 내려앉았다. 에코프로머티의 경우 24위에서 55위로 하락했다. 종목별로 보면 LG에너지솔루션의 시가총액이 연초 100조5000억원대에서 이날 88조3300억원대로 12조원 넘게 증발하면서 타격이 컸다. 에코프로그룹의 상장사 3곳(에코프로비엠·에코프로·에코프로머티)의 시가총액도 연초 58조5151억원에서 지난 22일 45조3928억원으로 약 13조원 감소했다. 이 기간 등락률 하위권 상장지수펀드(ETF)에도 이차전지 관련 상품들이 대거 이름을 올렸다. 'ACE 포스코그룹포커스'(-29.17%), 'KODEX 2차전지핵심소재10Fn'(-20.35%), 'SOL 2차전지소부장Fn'(-19.39%) 등이 크게 하락했다. 전기차 시장의 수요가 감소하면서 주요 배터리 기업들의 실적도 줄줄이 하락하자 투자심리가 위축된 것으로 풀이된다. 다올투자증권에 따르면 테슬라 주가는 2023년 초 기록했던 저점(101달러)까지 하락한 이후 재차 신저가에 근접하고 있다. 전기차 판매량 감소, 경쟁 심화에 따라 테슬라는 최근 미국과 중국에 이어 유럽, 중동, 아프리카에서도 잇따라 전기차 가격 인하 조치에 나섰다. 이안나 유안타증권 연구원은 \"이차전지 기업 실적은 지난해 4분기에 이어 올 1분기에도 셀, 양극재 등 수요 부진으로 대부분 외형 감소 및 어닝쇼크(실적충격)가 예상된다\"며 \"이차전지 수요의 유의미한 반등은 올해 4·4분기로 예상하는데, GM과 테슬라의 수요가 11월 미국 대선 이후 본격 확대될 것으로 전망되기 때문\"이라고 말했다.다만 이차전지 업종 주가는 이달 중순부터 재차 반등 중이다. 이달 18일부터 이날까지 에코프로비엠(11.63%), 포스코퓨처엠(11.24%), 삼성SDI(9.20%), 포스코홀딩스(6.47%) 등이 상승했는데, 다만 이는 추세 전환 보다는 기술적 반등이라는 것이 전문가들 의견이다. 이차전지 업종을 전담하는 한 증권사 연구원은 \"여전히 전방 수요가 회복되지 않고 있는 상황에서 2·4분기 수요가 점진적으로 개선될 것 같다는 기대감에 더해 최근 낙폭이 과대했던 만큼 다른 섹터에서의 수급이 옮겨온 것으로 보인다\"고 전했다.nodelay@fnnews.com 박지연 기자
"""
    model = NewsESGModel()
    profile_func(model.postprocess, input_content=content)
    # model.postprocess(input_content=content)
    ic(model.response_model)
