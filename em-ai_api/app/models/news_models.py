from pydantic import BaseModel
from typing import Dict, Any, Union


class NewsCategoryRequest(BaseModel):
    content: str | None = None

    class Config:
        from_attributes = True


class NewsCompanyRequest(BaseModel):
    content: str | None = None

    class Config:
        from_attributes = True


class NewsKeyphraseRequest(BaseModel):
    content: str | None = None

    class Config:
        from_attributes = True


class NewsESGRequest(BaseModel):
    content: str | None = None

    class Config:
        from_attributes = True


class NewsInvestmentRequest(BaseModel):
    title: str | None = None
    content: str | None = None

    class Config:
        from_attributes = True


class NewsResponse(BaseModel):
    status: str
    code: int
    message: str
    data: Union[Dict[str, Any], None] = None
