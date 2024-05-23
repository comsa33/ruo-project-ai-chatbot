import os
import traceback
import subprocess
from typing import Text
from abc import ABC, abstractmethod

import torch
import requests
from peft import PeftModel, PeftConfig
from huggingface_hub.utils._errors import RepositoryNotFoundError
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, BitsAndBytesConfig

from app.config.settings import FILE_PATHS, HF_TOKEN
from app.common.log.log_config import setup_logger
from app.common.news.base.hf_model_utils import seed_everything, processing
from app.common.core.utils import get_current_datetime, make_dir, format_error_message
from app.config.ai_status_code import ModelExecutionError, ResourceError, ServiceInternalError

# 상수 정의
MAX_LIMIT = 4000
INPUT_MAX_LENGTH = 1024
OUTPUT_MAX_LENGTH = 512

# HuggingFace CLI 로그인
subprocess.run(["huggingface-cli", "login", "--token", HF_TOKEN])

os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

class HuggingFaceModel(ABC):
    """HuggingFace 모델 추상 클래스"""

    def __init__(self, model_id: Text, gpu_id: int = 0):
        # 로거 설정
        model_name = model_id.split("/")[-1]
        file_path = FILE_PATHS["log"] + model_name
        make_dir(file_path)
        file_path += f"/{get_current_datetime()}.log"
        self.logger = setup_logger(model_name, file_path)

        self.gpu_id = gpu_id
        self.max_limit = MAX_LIMIT
        self.input_max_length = INPUT_MAX_LENGTH
        self.output_max_length = OUTPUT_MAX_LENGTH
        self.response_model = {
            "status": "fail",
            "code": ServiceInternalError.SERVICE_INTERNAL_ERROR["code"],
            "message": format_error_message(ServiceInternalError.SERVICE_INTERNAL_ERROR),
            "data": {"results": []},
        }
        try:
            self.peft_model_name = model_id
            self.peft_config = PeftConfig.from_pretrained(self.peft_model_name)
            self.qunat_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.peft_config.base_model_name_or_path,
            )
            self.hf_model = AutoModelForSeq2SeqLM.from_pretrained(
                self.peft_config.base_model_name_or_path,
                torch_dtype=torch.bfloat16,
                device_map={"": self.gpu_id},
                quantization_config=self.qunat_config,
            )
            self.model = PeftModel.from_pretrained(
                model=self.hf_model,
                model_id=self.peft_model_name,
                device_map={"": self.gpu_id},
            )
        # 모델 로드 중 에러 발생 시
        except RepositoryNotFoundError as repoerror:
            self.response_model["code"] = ModelExecutionError.MODEL_NOT_FOUND_ERROR["code"]
            self.response_model["message"] = format_error_message(
                ModelExecutionError.MODEL_NOT_FOUND_ERROR
            )
            self.logger.error(f"Repository Not Found Error : {repoerror}")
            print(f"Repository Not Found Error : {traceback.format_exc()}")
        # API 연결 중 에러 발생 시
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 401:
                self.response_model["code"] = ModelExecutionError.AUTHENTICATION_ERROR["code"]
                self.response_model["message"] = format_error_message(
                    ModelExecutionError.AUTHENTICATION_ERROR
                )
            else:
                self.response_model["code"] = ModelExecutionError.API_CONNECTION_ERROR["code"]
                self.response_model["message"] = format_error_message(
                    ModelExecutionError.API_CONNECTION_ERROR
                )
            self.logger.error(f"HTTP Error : {http_err}")
            print(f"HTTP Error : {traceback.format_exc()}")

    def predict(self, input_text: Text):
        """뉴스 본문과 제목을 입력받아 각 task별 분류 및 분석 결과를 출력

        Args:
            input_text : 사용자 입력 텍스트
            model_name : 모델 이름
        """
        input_text = processing(input_text)
        
        input_text = f"summary : {input_text}"
        with torch.no_grad():
            try:
                tokenized_test = self.tokenizer(
                    input_text,
                    max_length=self.input_max_length,
                    truncation=True,
                    padding="max_length",
                    return_tensors="pt",
                ).input_ids.cuda()
                seed_everything(42)
                tok_result = (
                    self.model.generate(input_ids=tokenized_test, max_length=self.output_max_length)
                    .cpu()
                    .numpy()
                )
                outputs = self.tokenizer.batch_decode(tok_result[0], skip_special_tokens=True)
                return outputs
            except OSError as oserror:
                self.response_model["code"] = ModelExecutionError.MODEL_PREDICTION_ERROR["code"]
                self.response_model["message"] = format_error_message(
                    ModelExecutionError.MODEL_PREDICTION_ERROR
                )
                self.logger.error(f"OS Error : {oserror}")
                print(f"OS Error : {traceback.format_exc()}")
            except RuntimeError as runtimeerror:
                if "CUDA out of memory" in str(runtimeerror) or isinstance(
                    runtimeerror, torch.cuda.OutOfMemoryError
                ):
                    self.response_model["code"] = ResourceError.GPU_OOM_ERROR["code"]
                    self.response_model["message"] = format_error_message(
                        ResourceError.GPU_OOM_ERROR
                    )
                else:
                    self.response_model["code"] = ModelExecutionError.MODEL_PREDICTION_ERROR["code"]
                    self.response_model["message"] = format_error_message(
                        ModelExecutionError.MODEL_PREDICTION_ERROR
                    )
                self.logger.error(f"Runtime Error : {runtimeerror}")
                print(f"Runtime Error : {traceback.format_exc()}")
            except Exception as e:
                self.response_model["code"] = ServiceInternalError.SERVICE_INTERNAL_ERROR["code"]
                self.response_model["message"] = format_error_message(
                    ServiceInternalError.SERVICE_INTERNAL_ERROR
                )
                self.logger.error(f"Exception : {e}")
                print(f"Exception : {e}\n{traceback.format_exc()}")

    @abstractmethod
    def validate_input(self, input_title: Text = None, input_content: Text = None):
        """입력 텍스트의 유효성을 검사하는 함수

        Args:
            input_title : 뉴스 제목
            input_content : 뉴스 본문
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
