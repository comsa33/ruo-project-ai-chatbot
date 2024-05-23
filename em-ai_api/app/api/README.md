# EM-AI API 명세서
| 작성자 | 작성일 | 수정일 | 버전 | 업무 이메일 |
|--------|--------|-----|------|--------|
| 이루오 | 2024.04.03 | 2024.04.05 | 1.0 | ruo@illunex.com |

## 1. API 엔드포인트 명세서
- method : `POST`
- 도메인 : `http://220.118.147.58:38222`

### 1.1. 뉴스 관련 API 명세서

| 엔드포인트         | 메소드 | 경로              | 요청 모델             | 응답 모델       | 설명                           |
|-------------------|--------|-------------------|----------------------|----------------|--------------------------------|
| 카테고리 분석 | POST   | `/api/v1/news/categories`     | NewsCategoryRequest | NewsResponse   | 특정 카테고리에 관한 뉴스 데이터 반환 |
| 회사 분석     | POST   | `/api/v1/news/companies`      | NewsCompanyRequest  | NewsResponse   | 특정 회사와 관련된 뉴스 데이터 반환  |
| 핵심 구문 분석       | POST   | `/api/v1/news/keyphrases`     | NewsKeyphraseRequest| NewsResponse   | 뉴스에서 핵심 구문 추출           |
| ESG 감정 분석       | POST   | `/api/v1/news/esg-sentiments` | NewsESGRequest      | NewsResponse   | ESG 관련 뉴스의 감정 분석         |
| 투자 관련 뉴스 가져오기 | POST   | `/api/v1/news/investments`    | NewsInvestmentRequest | NewsResponse | 투자와 관련된 뉴스 처리          |


### 1.2. 특허 관련 API 명세서


| 엔드포인트| 메소드 | 경로| 요청 모델| 응답 모델| 설명|
|---------|--------|-----------|----------|-----------|-------------------|
| 특허 초안 생성| POST| `/api/v1/patent/generation`| PatentGenerationRequest| PatentGenerationResponse |사용자의 입력에 기반하여 특허 초안을 생성 |
| 잠재적 구매자 정보 | POST   | `/api/v1/patent/potential-buyers`        | PotentialBuyersRequest                 | PatentResponse          | 특정 특허와 유사한 특허를 보유한 기업 정보 반환 |
| 유사 특허 정보 | POST   | `/api/v1/patent/similar-patents`         | SimilarPatentsRequest                  | PatentResponse          | 사용자 입력과 유사한 특허 정보 반환      |
| 키워드 기반 IPC 네트워크 조회| POST   | `/api/v1/patent/ipc-network-kw`          | SimilarPatentIPCNetworKeywordRequest   | PatentResponse          | 주어진 키워드와 관련된 IPC 네트워크 검색  |
| 문장 기반 IPC 네트워크 조회| POST   | `/api/v1/patent/ipc-network-nl`          | SimilarPatentIPCNetworNLRequest        | PatentResponse          | 주어진 문장과 관련된 IPC 네트워크 검색    |
| 특허 가격 예측| POST   | `/api/v1/patent/price-pred`              | TechValueRequest| PatentResponse          | 특허의 가격을 예측                       |


## 2. 요청 모델 명세서

### 2.1. 뉴스 관련 요청 모델 명세서

| 모델명                   | 필드     | 타입            | 설명                               | 필수 여부 |
|-------------------------|----------|-----------------|-----------------------------------|-----------|
| NewsCategoryRequest     | content  | str \| None     | 분석할 뉴스 컨텐츠                | O         |
| NewsCompanyRequest      | content  | str \| None     | 분석할 뉴스 컨텐츠                | O         |
| NewsKeyphraseRequest    | content  | str \| None     | 분석할 뉴스 컨텐츠                | O         |
| NewsESGRequest          | content  | str \| None     | 분석할 뉴스 컨텐츠                | O         |
| NewsInvestmentRequest   | title    | str \| None     | 뉴스 제목                         | O         |
| NewsInvestmentRequest   | content  | str \| None     | 분석할 뉴스 컨텐츠                | O         |

### 2.2. 특허 관련 요청 모델 명세서

| 모델명                          | 필드        | 타입            | 설명                   | 필수 여부 |
|--------------------------------|-------------|-----------------|-----------------------|-----------|
| PatentGenerationRequest        | userText    | str             | 특허 초안을 위한 사용자 입력 | O         |
| PotentialBuyersRequest         | patentId    | str             | 조회하고자 하는 특허 ID  | O         |
| PotentialBuyersRequest         | topK        | int             | 반환할 기업 수         | O         |
| SimilarPatentsRequest          | userText    | str             | 유사 특허 검색을 위한 사용자 입력 | O         |
| SimilarPatentIPCNetworKeywordRequest | keyword | str             | IPC 네트워크 검색을 위한 키워드 | O         |
| SimilarPatentIPCNetworKeywordRequest | size    | int             | 반환할 특허 수         | O         |
| SimilarPatentIPCNetworNLRequest| userText    | str             | IPC 네트워크 검색을 위한 문장 | O         |
| SimilarPatentIPCNetworNLRequest| size        | int             | 반환할 특허 수         | O         |
| TechValueRequest             | techName | str | 기술 가격 예측을 위한 기술명 | O         |
| TechValueRequest             | techDescription | str | 기술 가격 예측을 위한 상세 설명 | O         |


## 3. 응답 모델 명세서 (공통)
- 내부 성공 코드 : `777`

| 필드     | 타입                       | 설명                                |
|----------|----------------------------|------------------------------------|
| status   | str                        | 요청 상태 ("success", "fail")  |
| code     | int                        | 응답 코드  (HTTP 상태코드 + AI 내부코드) |
| message  | str                        | 응답 메시지                         |
| data     | Dict[str, Any] \| None     | 요청 결과 데이터                    |

## 4. 오류 처리 명세서

| 오류 상황               | HTTP 상태 코드 | 반환 메시지                    | 설명                             |
|-----------------------|----------------|------------------------------|----------------------------------|
| ExpiredSignatureError | 401            | 인증 토큰 만료 관련 메시지     | 제공된 토큰이 만료되었음을 나타냄 |
| 일반 예외 처리          | 500            | 서버 내부 오류 관련 메시지     | 서버 내부에서 발생한 예외 처리    |
| ai 내부 코드       | 600 ~ 900            | AI 서비스 내부 오류 관련 메시지 | AI 서비스 내부에서 발생한 오류    |

### 4.1. 상세 에러 코드 명세서

#### 4.1.1. 모델 실행 에러

| 에러 타입              | 코드 | 메시지                                                         | 타입                     |
|----------------------|------|--------------------------------------------------------------|--------------------------|
| TYPE_ERROR           | 800  | 모델 실행 중 타입 에러 발생                                    | TypeError                |
| DATA_FORMAT_ERROR    | 810  | 모델 실행 중 데이터 포맷 에러 발생                             | DataFormatError          |
| INPUT_LENGTH_ERROR   | 820  | 모델 실행 중 입력 길이 에러 발생                               | InputLengthError         |
| MODEL_PREDICTION_ERROR| 830 | 모델 실행 중 예측 에러 발생                                    | ModelPredictionError     |
| MODEL_NOT_FOUND_ERROR| 840  | 지정된 AI 모델을 찾을 수 없음                                  | ModelNotFoundError       |
| MISSING_PARAMETER_ERROR| 850| 모델 실행 중 필수 입력 값 누락                                 | MissingParameterError    |
| TIMEOUT_ERROR        | 860  | 모델 실행 중 시간 지연 발생                                    | TimeoutError             |
| API_CONNECTION_ERROR | 870  | 모델 실행 중 API 연결 에러 발생                                | APIConnectionError       |
| AUTHENTICATION_ERROR | 890  | 모델 실행 중 인증 에러 발생                                    | AuthenticationError      |

#### 4.1.2. 리소스 에러

| 에러 타입             | 코드 | 메시지                                      | 타입                    |
|---------------------|------|--------------------------------------------|-------------------------|
| GPU_OOM_ERROR       | 900  | GPU 메모리 부족 에러 발생                   | GPUOOMError             |
| GPU_OCCUPIED_ERROR  | 910  | GPU 사용 중 에러 발생                        | GPUOccupiedError        |
| CPU_OOM_ERROR       | 920  | CPU 메모리 부족 에러 발생                   | CPUOOMError             |
| DISK_FULL_ERROR     | 930  | 디스크 용량 부족 에러 발생                   | DiskFullError           |
| NETWORK_ERROR       | 940  | 네트워크 연결 에러 발생                      | NetworkError            |
| HW_FAILURE_ERROR    | 950  | 하드웨어 장애 발생                           | HardwareFailureError    |
| OTHER_GPU_ERROR     | 999  | 기타 GPU 장애 발생                           | OtherGPUError           |

#### 4.1.3. 서비스 내부 에러

| 에러 타입              | 코드 | 메시지                               | 타입                   |
|----------------------|------|-------------------------------------|------------------------|
| DATA_NOT_FOUND_ERROR | 600  | 데이터를 찾을 수 없음                 | DataNotFoundError      |
| SERVICE_INTERNAL_ERROR | 666 | 서비스 내부 에러 발생                | ServiceInternalError   |




