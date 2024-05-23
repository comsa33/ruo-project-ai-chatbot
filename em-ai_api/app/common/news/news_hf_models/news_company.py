import re
import traceback
from typing import Text

from icecream import ic

from app.config.ai_status_code import Success
from app.common.news.base.hf_model import HuggingFaceModel
from app.common.news.base.hf_model_utils import esg_company_dumps
from app.common.core.utils import format_error_message
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError


class NewsCompanyModel(HuggingFaceModel):
    def __init__(self, model_id="illunex-ai/news-esg-qlora", gpu_id: int = 0):
        """
        Description:
            뉴스 기업명 추출 모델 클래스

        Args:
            model_id : 허깅페이스 모델 아이디 -> default: "illunex-ai/news-esg-qlora"
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
        """뉴스 본문을 입력받아 기업명 분석 결과를 후처리하는 기능

        Args:
            input_content : 뉴스 본문
        """
        try:
            self.validate_input(input_content)
            output = super().predict(input_text=input_content)
            output = esg_company_dumps(output)
            if not output:  # 기업명을 찾을 수 없는 경우
                self.response_model['data']['results'] = []
                self.response_model["code"] = ServiceInternalError.DATA_NOT_FOUND_ERROR["code"]
                self.response_model["message"] = (
                    format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR)
                    + " 해당 기사에서 기업명을 찾을 수 없습니다."
                    )
                self.logger.error(format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR))
                ic(format_error_message(ServiceInternalError.DATA_NOT_FOUND_ERROR))
            else:
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
    from app.common.core.utils import debug_ic, profile_func

    content = """
부산창조경제혁신센터는 삼성증권, 한국벤처투자, 울산·경남창조경제혁신센터와 지역 스타트업이 발전하고 성장할 수 있는 기회를 제공하기 위해 삼성증권 부산기업금융지점에서 VC IR데이(기업설명회)를 지난 23일 개최했다고 24일 밝혔다.

이번 VC IR데이(기업설명회)는 작년에 이어 2번째 개최한 행사다. 지역의 창조경제혁신센터와 함께함으로써 지역 스타트업들의 후속투자 유치를 도모한다. 작년 VC IR데이(기업설명회)에 참여한 기업 중 에듀테크 기업인 산타가 엑센트리벤처스, 경남벤처투자, 삼성증권 등에서 후속 투자유치에 성공한 바 있다.


스타트업 투자에 관심이 많은 벤처캐피탈, 기관투자자, 법인, 삼성증권 고객 등이 이번 IR 행사에 참여했다. 올해도 스타트업 투자단계에 맞춰 씨드머니 혹은 시리즈 A라운드 이상 투자를 받았던 스타트업이 참여했다.

이번 행사에는 △포스코어(철강 부산물을 활용한 자성분말 및 이를 활용한 고효율 모터코어 제조사업) △에이엔제이사이언스(전합성 플랫폼 기술보유, 난치성 감염병 치료제 개발) △앤디소프트 (Language Free Zone 다자간 실시간 통역 플랫폼 개발) △오션스바이오(난치/정신질환 치료용 체내외 미주신경 전기자극 디바이스 전자약) △팀솔루션(대규모 3D CAD 경량화 기술 기반 산업용 디지털 트윈솔루션 △뉴트리인더스트리 (곤충을 활용해 음식물쓰레기를 친환경적으로 리사이클링) △피알지에스앤텍 (PPI기술이 적용된 희귀유전질환 치료제 개발) △스템덴(치아 치수-상아질 재생치료제 개발) △한국정밀소재산업 (방산 및 모빌리티에 사용되는 초경량 복합재 제조업) △피플앤스토리 (웹소설 · 웹툰 제작 및 IP 기반 콘텐츠 유통) △인트인(저출산 문제 중 하나인 난임솔루션 제공) △넷스파(해양 폐기물 재활용을 통한 나일론 및 원료 재생산) △인켐스(차세대 전고체전지용 대기안정형 황화물계 고체전해질과 고에너지밀도 리튬이차전지용 액체전해질 제조) 등 13개 스타트업이 참여했다.

스타트업들의 IR데이 이후에는 투자사와 스타트업이 네트워킹할 수 있는 자리와 더불어 스타트업-투자사의 매칭시 별도의 투자상담회도 마련됐다.

김용우 부산창조경제혁신센터 센터장은 “부산 지역의 스타트업들이 후속투자 유치를 위한 발판을 지속적으로 확대할 계획”이라며 “스타트업들의 성장을 통해 부산의 새로운 경제성장 동력확보를 위한 발판을 만들겠다”라고 덧붙였다.
"""
    model = NewsCompanyModel()
    # profile_func(model.postprocess, input_content=content)
    model.postprocess(input_content=content)
    ic(model.response_model)
