from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router as api_router


app = FastAPI(
    title="NLPTrade API",
    description="NLP-driven market event intelligence and stock movement prediction system.",
    version="0.1.0",
)

# Frontend dev origins only.
# Do not use allow_origins=["*"] once deployed with credentials/cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "app": "NLPTrade",
        "status": "running",
        "mvp_ticker": "NVDA",
        "docs": "/docs",
        "api_health": "/api/health",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
