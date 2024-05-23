import traceback
from collections.abc import Iterable
from typing import Any, Union

import numpy as np
from icecream import ic

from app.common.core.utils import format_error_message
from app.common.patent.base.sklearn_model import SklearnModel
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError, Success

TECH_VALUE_PRED_MODEL_PATH = "app/common/patent/resources/tech_price_prediction_model.pkl"

TYPE_ERROR_MESSAGE = "입력값은 리스트여야 하며, 리스트의 값은 문자열이어야 합니다."
INPUT_VALUE_ERROR_MESSAGE = "기술명과 기술 개요문의 입력값이 없습니다."
INPUT_LENGTH_ERROR_MESSAGE1 = "기술명과 기술 개요문의 입력 리스트 길이가 일치하지 않습니다."
INPUT_LENGTH_ERROR_MESSAGE2 = "기술명과 기술 개요문의 입력값이 너무 짧습니다. 기술명은 5자 이상, 기술 개요문은 10자 이상이어야 합니다."
INPUT_LENGTH_ERROR_MESSAGE3 = "기술명과 기술 개요문의 입력 리스트 길이가 0입니다."


class TechValuePredictionModel(SklearnModel):
    def validate_input(self, tech_name: list[str], tech_description: list[str]):
        """유효성 검사 함수

        Args:
            tech_name (list[str]): 기술명. 여러개 배치로 입력.
            tech_description (list[str]): 기술 개요문. 여러개 배치로 입력.

        Raises:
            TypeError: 잘못된 타입
            ValueError: 잘못된 값
        """
        if not (
            isinstance(tech_name, list) and isinstance(tech_description, list)
        ) or not (  # list 확인  # 리스트의 값이 str인지 확인
            self._isinstance_for_list(tech_name, str)
            and self._isinstance_for_list(tech_description, str)
        ):
            raise TypeError(TYPE_ERROR_MESSAGE)
        if len(tech_name) != len(tech_description):  # 두 파라미터 길이 확인
            raise ValueError(INPUT_LENGTH_ERROR_MESSAGE1)
        if len(tech_name) == 0 or len(tech_description) == 0:
            raise ValueError(INPUT_LENGTH_ERROR_MESSAGE3)
        if isinstance(tech_name, list) and isinstance(tech_description, list):
            if tech_name[0] == "" or tech_description[0] == "":
                raise ValueError(INPUT_VALUE_ERROR_MESSAGE)
            if len(tech_name[0]) < 5 or len(tech_description[0]) < 10:
                raise ValueError(INPUT_LENGTH_ERROR_MESSAGE2)

    def _isinstance_for_list(self, value, is_type: Union[Any, Iterable[Any]]) -> bool:
        return sum([not isinstance(v, is_type) for v in value]) == 0

    def postprocess(self, tech_name: list[str], tech_description: list[str]):
        """기술 가치 평가 후처리 함수

        Args:
            tech_name (list[str]): 기술명. 여러개 배치로 입력.
            tech_description (list[str]): 기술 개요문. 여러개 배치로 입력.
        """
        try:
            self.validate_input(tech_name, tech_description)
            text_list = [
                f"tech_name: {tn.strip()}\ndescription: {td.strip()}"
                for tn, td in zip(tech_name, tech_description)
            ]
            pred = super().predict(text_list)
            output = np.around(np.expm1(pred), -5)
            output = output.tolist()    # numpy array를 list로 변환 (이루오 추가)
            self.response_model["status"] = "success"
            self.response_model["code"] = Success.SUCCESS["code"]
            self.response_model["message"] = Success.SUCCESS["message"]
            self.response_model["data"]["results"] = output
        except ValueError as e:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ModelExecutionError.INPUT_LENGTH_ERROR["code"]
            self.response_model["message"] = format_error_message(
                ModelExecutionError.INPUT_LENGTH_ERROR
            ) + str(e)
            self.logger.error(format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR))
            ic(format_error_message(ModelExecutionError.INPUT_LENGTH_ERROR))
        except TypeError:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ModelExecutionError.TYPE_ERROR["code"]
            self.response_model["message"] = format_error_message(ModelExecutionError.TYPE_ERROR)
            self.logger.error(format_error_message(ModelExecutionError.TYPE_ERROR))
            ic(format_error_message(ModelExecutionError.TYPE_ERROR))
        except Exception:
            self.response_model['data']['results'] = []
            self.response_model["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            self.response_model["message"] = format_error_message(
                ServiceInternalError.SERVICE_INTERNAL_ERROR
            )
            self.logger.error(format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR))
            ic(format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR))
            ic(traceback.format_exc())


if __name__ == "__main__":
    tech_price_test_cases = [
        ("웨어러블 건강 모니터링 장치", "사용자의 건강 상태를 지속적으로 모니터링하고 분석하는 스마트 웨어러블 기기."),
        ("가상 현실 기반 교육 플랫폼", "학생들에게 실감 나는 학습 경험을 제공하는 VR 기술을 활용한 교육용 소프트웨어."),
        ("3D 프린팅을 이용한 맞춤형 의료 기기 제작", "환자 맞춤형 의료 장비 및 보조 기구를 3D 프린팅으로 제작하는 기술.")
        ]
    tech_price_real_cases = [
        (
            "교통안전을 위한 제설장치",
            ("본 발명은 겨울철에 폭설로 인하여 산간지역의 도로에 쌓이는 눈을"
             " 온풍을 불어서 작업자 없이도 제설이 가능하여 교통 안전을 도모하도록"
             " 구성되는 교통 안전을 위한 제설장치에 관한 발명이다."),
            2000000
        ),
        (
            "거리측정센서와 스프링휠로프 에너지하베스팅 기능을 가진 IOT 스마트 쓰레기 통 장치",
            ("쓰레기통 내부에서 쓰레기가 얼마나 쌓여있는지 레이다, 광학 혹은 초음파 신호를 전송하고 전송한 상기 신호가"
             "물체 표면에서 반사되어 다시 수신되기까지의 시간을 이용하여 거리를 측정하는 거리측정센서를 사용하여 쓰레"
             "기통 뚜껑 내부에서 쓰레기가 어디까지 쌓여 있는지 감지하여 정확한 쓰레기통 비우기 관리 시점을 관리자에게"
             "알려 줄 수 있고, 스프링 휠로프 운동에너지 전기 변환부를 통해 지속적으로 동작에 필요한 전기에너지를 공급"
             "받을 수 있어서 배터리 교체가 불필요하고, 종래의 쓰레기통에 부착형으로 부착하여 기존의 일반적인 쓰레기통"
             "을 IOT 스마트 쓰레기통으로 동작할 수 있게 해줌으로써 적은 비용으로 IOT 스마트 쓰레기통 기능을 제공할 수"
             "있다"),
            3000000
        ),
        (
            "외국어 교육용 인공지능 기능을 구비한 사용자 기기 및 외국어 교육 방법",
            ("본 발명은 외국어 교육용 인공지능 기능을 구비하여 사용자 음성의 문법 오류/발음 오류에 따른 음성 반응을 제"
             "공하는 사용자 기기, 및 사용자 기기의 온라인 접속을 통해 외국어 교육을 제공하는 방법에 대한 것이다."),
            7500000
        ),
        (
            "터널 컵",
            ("액체를 마실 때 사용하는 일반적인 컵의 기술과 액체를 마실 때 사용하는 일반적인 빨대의 기술:"
             "원래의 일반적인 컵의 내부에 컵 바닥에서 액체가 빨려들어올 만큼의 약간의 개방적인 틈을 만들고"
             "터널처럼 이어지는 빨대가 컵 입구까지만 존재하게 해서 컵입구 밖으로 돌출되어 있는 액체를 마시는 흡입구가 없게 한다."),
            1000000000
        )
    ]
    model_path = TECH_VALUE_PRED_MODEL_PATH
    model = TechValuePredictionModel(model_path)
    model.postprocess(
        tech_name=[tech_price_test_cases[2][0]],
        tech_description=[tech_price_test_cases[2][1]]
        )
    ic(model.response_model)
