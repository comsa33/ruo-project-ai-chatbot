from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import CORS_ALLOW_ORIGINS
from app.api.news_router import router as news_router
from app.api.patent_router import router as patent_router

app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[*CORS_ALLOW_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드를 허용
    allow_headers=["*"],  # 모든 헤더를 허용
)

app.include_router(news_router, prefix="/api/v1/news", tags=["em-ai_news"])
app.include_router(patent_router, prefix="/api/v1/patent", tags=["em-ai_patent"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
