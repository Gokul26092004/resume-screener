from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class Shortlist(Base):
    __tablename__ = "shortlists"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, index=True)
    candidate_name = Column(String, nullable=True)
    jd_text = Column(Text)  # Store the full JD for reference
    score = Column(Float)  # Semantic + skill match combined (0-1)
    semantic_score = Column(Float, default=0.0)  # Pure embedding score
    skill_match_score = Column(Float, default=0.0)  # Skill overlap %
    required_skills = Column(JSON)  # Extracted by Groq: ["Python", "FastAPI", ...]
    matched_skills = Column(JSON)  # Skills candidate has: ["Python", "FastAPI"]
    missing_skills = Column(JSON)  # Skills candidate lacks
    status = Column(String, default="shortlisted")  # shortlisted / rejected / pending
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Shortlist resume_id={self.resume_id} score={self.score}>"