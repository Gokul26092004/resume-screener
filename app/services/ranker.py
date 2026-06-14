import os
import logging
import json
from typing import Optional
import chromadb
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_chroma_client: Optional[chromadb.ClientAPI] = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        persist_path = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
        _chroma_client = chromadb.PersistentClient(path=persist_path)
        logger.info(f"ChromaDB initialised at {persist_path}")
    return _chroma_client


def get_collection() -> chromadb.Collection:
    return get_chroma_client().get_or_create_collection(
        name="resumes",
        metadata={"hnsw:space": "cosine"},
    )


def embed_text(text: str) -> list[float]:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"))
    return model.encode(text, normalize_embeddings=True).tolist()


def build_resume_text(resume) -> str:
    """Convert your Resume SQLAlchemy model into plain text for embedding."""
    skills = json.loads(resume.skills or "[]")
    experience = json.loads(resume.experience or "[]")
    education = json.loads(resume.education or "[]")

    return f"""
Name: {resume.name or ''}
Email: {resume.email or ''}
Phone: {resume.phone or ''}
Skills: {', '.join(skills) if isinstance(skills, list) else str(skills)}
Experience: {' | '.join(experience) if isinstance(experience, list) else str(experience)}
Education: {' | '.join(education) if isinstance(education, list) else str(education)}
""".strip()


def upsert_resume(resume) -> None:
    """Index a Resume model object into ChromaDB. Call this after db.commit()."""
    text = build_resume_text(resume)
    embedding = embed_text(text)

    get_collection().upsert(
        ids=[str(resume.id)],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "name": str(resume.name or ""),
            "email": str(resume.email or ""),
            "filename": str(resume.filename or ""),
        }],
    )
    logger.info(f"Indexed resume id={resume.id} ({resume.name}) into ChromaDB")


def rank_resumes(job_description: str, top_k: int = 10, min_score: float = 0.0) -> list[dict]:
    """Rank all indexed resumes against a job description."""
    collection = get_collection()
    total = collection.count()

    if total == 0:
        return []

    query_embedding = embed_text(job_description)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, total),
        include=["metadatas", "distances", "documents"],
    )

    ranked = []
    for rid, dist, meta, doc in zip(
        results["ids"][0],
        results["distances"][0],
        results["metadatas"][0],
        results["documents"][0],
    ):
        score = round(1.0 - dist, 4)
        if score < min_score:
            continue
        ranked.append({
            "resume_id": int(rid),
            "score": score,
            "name": meta.get("name", ""),
            "email": meta.get("email", ""),
            "filename": meta.get("filename", ""),
            "snippet": doc[:300] + ("…" if len(doc) > 300 else ""),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def delete_from_chromadb(resume_id: int) -> None:
    get_collection().delete(ids=[str(resume_id)])
    logger.info(f"Deleted resume id={resume_id} from ChromaDB")


def get_stats() -> dict:
    return {"total_indexed": get_collection().count()}