from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.resume import Resume
from app.services.ranker import rank_resumes, upsert_resume, delete_from_chromadb, get_stats

router = APIRouter()


class RankRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    top_k: int = Field(10, ge=1, le=100)
    min_score: float = Field(0.0, ge=0.0, le=1.0)


@router.post("/rank")
def rank_endpoint(body: RankRequest):
    """Rank all indexed resumes against a job description."""
    try:
        results = rank_resumes(body.job_description, body.top_k, body.min_score)
        return {
            "total_results": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/{resume_id}")
def index_single_resume(resume_id: int, db: Session = Depends(get_db)):
    """Manually index one resume from PostgreSQL into ChromaDB by its ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found")
    try:
        upsert_resume(resume)
        return {"status": "indexed", "resume_id": resume_id, "name": resume.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/all")
def index_all_resumes(db: Session = Depends(get_db)):
    """Bulk index all resumes from PostgreSQL into ChromaDB."""
    resumes = db.query(Resume).all()
    if not resumes:
        return {"status": "nothing to index", "total": 0}

    success, failed = 0, []
    for r in resumes:
        try:
            upsert_resume(r)
            success += 1
        except Exception as e:
            failed.append({"id": r.id, "error": str(e)})

    return {"status": "done", "indexed": success, "failed": failed}


@router.delete("/index/{resume_id}")
def remove_from_index(resume_id: int):
    """Remove a resume from ChromaDB index."""
    try:
        delete_from_chromadb(resume_id)
        return {"status": "deleted", "resume_id": resume_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def chroma_stats():
    """How many resumes are currently indexed in ChromaDB."""
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))