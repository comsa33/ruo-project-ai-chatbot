from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel


# 특허 작성 API
class PatentGenerationRequest(BaseModel):
    userText: str


class PatentGenerationResult(BaseModel):
    title: Optional[str] | None = ""    # 특허명
    abstract: Optional[str] | None = ""   # 특허 요약(개요)
    target: Optional[str] | None = ""   # 해결하고자 하는 과제
    method: Optional[str] | None = ""   # 과제의 해결 수단
    effect: Optional[str] | None = ""   # 과제 해결 수단의 효과
    tech: Optional[str] | None = ""     # 기술 분야
    ipc: Optional[List[str]] | None = []    # IPC
    priorArt: Optional[str] | None = ""    # 기존 연구
    patentClaim: Optional[str] | None = ""   # 특허 청구항
    diagramUrl: Optional[str] | None = ""    # 특허 기능 분석도 URL
    keywords: Optional[List[str]] | None = []   # 특허 키워드


class PatentGenerationData(BaseModel):
    results: List[PatentGenerationResult] = []


class PatentGenerationResponse(BaseModel):
    status: str
    code: int
    message: str
    data: PatentGenerationData


# 유사 특허 검색 API
class SimilarPatentsRequest(BaseModel):
    userText: str
    size: int


# 유사 특허 보유 기업 검색 API
class PotentialBuyersRequest(BaseModel):
    patentId: str
    topK: int


# 특허 IPC 네트워크 검색 API - 키워드 형태
class SimilarPatentIPCNetworKeywordRequest(BaseModel):
    keyword: str  # 특허기술 키워드
    size: int  # 검색수량
    # hsCode: str # HS코드


# 특허 IPC 네트워크 검색 API - 질의문 형태
class SimilarPatentIPCNetworNLRequest(BaseModel):
    userText: str
    size: int
    # hsCode: str


# 특허 가격 조회 API
class TechValueRequest(BaseModel):
    techName: str  # 특허명
    techDescription: str  # 특허 세부사항


# 공통 응답
class PatentResponse(BaseModel):
    status: str
    code: int
    message: str
    data: Union[Dict[str, Any], None] = None
