import json

import requests
import plantuml

from app.common.core.utils import format_error_message
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError


def call_patent_api(url: str, data: dict, time_out: int = 60):
    """특허 API 호출

    Args:
        url (str): 호출할 API URL
        data (dict): 호출할 API에 전달할 데이터
        time_out (int, optional): API 호출 시간 초과 설정. Defaults to 60.

    Returns:
        dict: API 호출 결과
    """
    headers = {
        "Content-type": "accept: application/json",
        "Accept": "application/json",
        "charset": "utf-8",
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=time_out)
        if response.ok:
            return True, response.json()
        else:
            print(response.text)
            raise Exception
    except requests.exceptions.Timeout:
        print("API 호출 시간 초과")
        return False, format_error_message(ModelExecutionError.TIMEOUT_ERROR)
    except requests.exceptions.HTTPError:
        print("API 호출 오류")
        return False, format_error_message(ModelExecutionError.API_CONNECTION_ERROR)
    except Exception:
        print("API 호출 오류")
        return False, format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR)


def generate_plantuml_url(plantuml_code):
    # PlantUML 서버 설정
    pl = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')  # 이미지를 반환하는 서버 URL 설정

    # 코드를 이미지 URL로 변환
    url = pl.get_url(plantuml_code)
    return url
