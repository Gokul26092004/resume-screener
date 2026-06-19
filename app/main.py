from fastapi import FastAPI
from app.api.resume import router as resume_router
from app.api.rank import router as rank_router
from app.database import engine
from fastapi.middleware.cors import CORSMiddleware
from app.models import resume as resume_model
from app.models import shortlist as shortlist_model

resume_model.Base.metadata.create_all(bind=engine)
shortlist_model.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Resume Screener", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router, prefix="/resume", tags=["Resume"])
app.include_router(rank_router, prefix="/resume", tags=["Ranking"])

@app.get("/")
def home():
    return {"message": "AI Resume Screener is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}