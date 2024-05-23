import json
import pickle
import traceback
from abc import ABC, abstractmethod
from typing import Text

import numpy as np
import requests
from app.config.settings import FILE_PATHS, API_ADDRESS
from app.common.log.log_config import setup_logger
from app.common.core.utils import format_error_message, get_current_datetime, make_dir
from app.config.ai_status_code import ModelExecutionError, ServiceInternalError

# 상수 정의
EMBEDDING_URL = API_ADDRESS["embedding"]


class SklearnModel(ABC):
    """sklearn 모델 추상 클래스"""

    def __init__(self, model_path: Text):
        # 로거 설정
        # TODO: 파일명 집어넣는거라 수정 필요
        model_name = model_path.split("/")[-1].replace(".pkl", "")  # 파일명 추출 (이루오 추가)
        file_path = FILE_PATHS["log"] + model_name
        make_dir(file_path)
        file_path += f"/{get_current_datetime()}.log"
        self.logger = setup_logger(model_path, file_path)

        # 응답 모델 설정
        self.response_model = {
            "status": "fail",
            "code": ServiceInternalError.SERVICE_INTERNAL_ERROR["code"],
            "message": format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR),
            "data": {"results": []},
        }

        try:
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
        except FileNotFoundError:
            self.response_model["code"] = ModelExecutionError.MODEL_NOT_FOUND_ERROR["code"]
            self.response_model["message"] = format_error_message(
                ModelExecutionError.MODEL_NOT_FOUND_ERROR
            )

    def predict(self, text_list: list[str]) -> list[int]:
        """모델 추론 진행

        Args:
            text_list (list[str]): 입력 문장

        Returns:
            list[int]: 추론 결과
        """
        try:
            embedding = self.get_embedding(text_list)
        except requests.exceptions.ConnectTimeout as e:
            self.response_model["code"] = ModelExecutionError.TIMEOUT_ERROR["code"]
            self.response_model["message"] = format_error_message(ModelExecutionError.TIMEOUT_ERROR)
            self.logger.error(f"Exception : {e}")
            print(f"Exception : {e}\n{traceback.format_exc()}")

        try:
            pred = self.model.predict(np.asarray(embedding))
            return pred
        except Exception as e:
            self.response_model["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
            self.response_model["message"] = format_error_message(
                ServiceInternalError.SERVICE_INTERNAL_ERROR
            )
            self.logger.error(f"Exception : {e}")
            print(f"Exception : {e}\n{traceback.format_exc()}")

    def get_embedding(self, text_list: list[str]) -> np.ndarray:
        embedding = requests.post(EMBEDDING_URL, json={"query_message": text_list})
        embedding = json.loads(embedding.text)["embedding_vector"]
        return np.asarray(embedding)

    @abstractmethod
    def validate_input(self, text_list: list[str]):
        """입력 텍스트의 유효성을 검사하는 함수

        Args:
            tech_name : 뉴스 제목
            tech_description : 뉴스 본문
        """
        pass

    @abstractmethod
    def postprocess(self, input_title: Text = None, input_content: Text = None):
        """뉴스 본문과 제목을 입력받아 각 task별 분류 및 분석 결과를 후처리

        Args:
            input_title : 뉴스 제목
            input_content : 뉴스 본문
        """
        pass
