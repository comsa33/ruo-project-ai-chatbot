class DataNotFoundError(Exception):
    def __init__(self, message="데이터를 찾을 수 없습니다"):
        # 예외가 발생할 때 출력할 메시지 설정
        self.message = message
        super().__init__(self.message)


class ModelPredictionError(Exception):
    def __init__(self, message="모델 예측 중 오류가 발생했습니다"):
        self.message = message
        super().__init__(self.message)
