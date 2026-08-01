from fastapi import FastAPI

app = FastAPI(
    title= "NLPTrade API",
    description="NLP-driven market event intelligence and stock movement prediction system.",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "app": "NLPTrade",
        "status": "running",
        "mvp_ticker": "NVDA"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}