class Success:
    SUCCESS = {"code": 777, "message": "성공"}


class ModelExecutionError:
    TYPE_ERROR = {
        "code": 800,
        "message": "모델 실행 중 타입 에러가 발생했습니다. 입력하신 데이터가 텍스트인지 확인해주세요.",
        "type": "TypeError",
    }
    DATA_FORMAT_ERROR = {
        "code": 810,
        "message": "모델 실행 중 데이터 포맷 에러가 발생했습니다.",
        "type": "DataFormatError",
    }
    INPUT_LENGTH_ERROR = {
        "code": 820,
        "message": "모델 실행 중 입력 길이 에러가 발생했습니다. 제목과 본문은 각각 최소 10자 이상, 도합 최대 4000자 이하로 입력해주세요.",
        "type": "InputLengthError",
    }
    MODEL_PREDICTION_ERROR = {
        "code": 830,
        "message": "모델 실행 중 예측 에러가 발생했습니다.",
        "type": "ModelPredictionError",
    }
    MODEL_NOT_FOUND_ERROR = {
        "code": 840,
        "message": "지정된 AI 모델을 찾을 수 없습니다. 담당자에게 문의해주세요.",
        "type": "ModelNotFoundError",
    }
    MISSING_PARAMETER_ERROR = {
        "code": 850,
        "message": "모델 실행 중 필수 입력 값이 누락되었습니다. 입력하신 데이터를 확인해주세요.",
        "type": "MissingParameterError",
    }
    TIMEOUT_ERROR = {
        "code": 860,
        "message": "모델 실행 중 시간이 지연되었습니다. 다시 시도해주세요.",
        "type": "TimeoutError",
    }
    API_CONNECTION_ERROR = {
        "code": 870,
        "message": "모델 실행 중 API 연결 에러가 발생했습니다. 서버의 인터넷 연결을 확인해주세요.",
        "type": "APIConnectionError",
    }
    AUTHENTICATION_ERROR = {
        "code": 890,
        "message": "모델 실행 중 인증 에러가 발생했습니다. 허깅페이스 혹은 OpenAI 토큰을 확인하거나, 담당자에게 문의해주세요.",
        "type": "AuthenticationError",
    }


class ResourceError:
    GPU_OOM_ERROR = {
        "code": 900,
        "message": "GPU 메모리 부족 에러가 발생했습니다. 다시 시도해주세요.",
        "type": "GPUOOMError",
    }
    GPU_OCCUPIED_ERROR = {
        "code": 910,
        "message": "GPU가 현재 사용 중입니다. 잠시 후 다시 시도해주세요.",
        "type": "GPUOccupiedError",
    }
    CPU_OOM_ERROR = {
        "code": 920,
        "message": "CPU 메모리 부족 에러가 발생했습니다.",
        "type": "CPUOOMError",
    }
    DISK_FULL_ERROR = {
        "code": 930,
        "message": "디스크 용량이 부족합니다.",
        "type": "DiskFullError",
    }
    NETWORK_ERROR = {
        "code": 940,
        "message": "네트워크 연결 에러가 발생했습니다.",
        "type": "NetworkError",
    }
    HW_FAILURE_ERROR = {
        "code": 950,
        "message": "하드웨어 장애가 발생했습니다.",
        "type": "HardwareFailureError",
    }
    OTHER_GPU_ERROR = {
        "code": 999,
        "message": "기타 GPU 장애가 발생했습니다.",
        "type": "OtherGPUError",
    }


class ServiceInternalError:
    DATA_NOT_FOUND_ERROR = {
        "code": 600,
        "message": "데이터를 찾을 수 없습니다. 담당자에게 문의해주세요.",
        "type": "DataNotFoundError",
    }

    SERVICE_INTERNAL_ERROR = {
        "code": 666,
        "message": "서비스 내부 에러가 발생했습니다. 담당자에게 문의해주세요.",
        "type": "ServiceInternalError",
    }
