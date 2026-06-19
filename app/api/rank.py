from app.models.shortlist import Shortlist
from app.services.ranker import extract_skills_from_jd, calculate_skill_match, build_resume_text
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


class ShortlistRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    min_score: float = Field(0.4, ge=0.0, le=1.0, description="Minimum combined score to shortlist")


@router.post("/shortlist")
def shortlist_candidates(body: ShortlistRequest, db: Session = Depends(get_db)):
    """
    Smart shortlisting:
    1. Extract required skills from JD using Groq
    2. Rank all resumes by semantic similarity
    3. Calculate skill match %
    4. Combine both scores
    5. Save results to PostgreSQL
    6. Return shortlisted candidates
    """
    try:
        # Step 1: Extract skills from JD
        required_skills = extract_skills_from_jd(body.job_description)

        # Step 2: Rank semantically
        semantic_results = rank_resumes(body.job_description, top_k=100, min_score=0.0)

        all_candidates = []
        shortlisted = []

        # Step 3-5: Calculate combined score for each resume
        for result in semantic_results:
            resume_id = int(result["resume_id"])  # Convert to int
            semantic_score = result["score"]

            # Get full resume text for skill matching
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            print(f"DEBUG: Looking for resume_id={resume_id}, found={resume is not None}")  # DEBUG
            if not resume:
                continue

            resume_text = build_resume_text(resume)
            matched_skills, missing_skills, skill_match_score = calculate_skill_match(
                resume_text, required_skills
            )

            # Combine scores: 60% semantic + 40% skill match
            combined_score = round((semantic_score * 0.6) + (skill_match_score * 0.4), 4)

            candidate_data = {
                "resume_id": resume_id,
                "name": resume.name,
                "email": resume.email,
                "combined_score": combined_score,
                "semantic_score": semantic_score,
                "skill_match_score": skill_match_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "required_skills": required_skills,
            }
            all_candidates.append(candidate_data)

            # Only shortlist if above threshold
            if combined_score >= body.min_score:
                shortlist_record = Shortlist(
                    resume_id=resume_id,
                    candidate_name=resume.name,
                    jd_text=body.job_description,
                    score=combined_score,
                    semantic_score=semantic_score,
                    skill_match_score=skill_match_score,
                    required_skills=required_skills,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    status="shortlisted",
                )
                db.add(shortlist_record)
                db.commit()
                shortlisted.append(candidate_data)

        # Sort by combined score descending
        all_candidates.sort(key=lambda x: x["combined_score"], reverse=True)
        shortlisted.sort(key=lambda x: x["combined_score"], reverse=True)

        return {
            "total_shortlisted": len(shortlisted),
            "total_candidates_evaluated": len(all_candidates),
            "min_score_threshold": body.min_score,
            "required_skills": required_skills,
            "all_candidates": all_candidates,  # Show ALL with scores
            "shortlisted": shortlisted,  # Show only above threshold
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shortlist/history")
def get_shortlist_history(db: Session = Depends(get_db)):
    """View all past shortlisting decisions."""
    try:
        records = db.query(Shortlist).order_by(Shortlist.created_at.desc()).all()
        return {
            "total_records": len(records),
            "shortlists": [
                {
                    "id": r.id,
                    "resume_id": r.resume_id,
                    "candidate_name": r.candidate_name,
                    "score": r.score,
                    "status": r.status,
                    "created_at": r.created_at,
                }
                for r in records
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))