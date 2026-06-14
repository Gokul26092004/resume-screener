from app.services.ranker import upsert_resume
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.parser import parse_resume
from app.database import get_db
from app.models.resume import Resume
import shutil
import os
import json
import re

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_path = f"{UPLOAD_DIR}/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = parse_resume(file_path)
        ai_text = result["ai_response"]

        # Extract JSON from response
        try:
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {}
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            parsed = {}

        # Safe string conversion
        name = str(parsed.get("name") or "")
        email = str(parsed.get("email") or "")
        phone = str(parsed.get("phone") or "")
        skills = json.dumps(parsed.get("skills") or [])
        experience = json.dumps(parsed.get("experience") or [])
        education = json.dumps(parsed.get("education") or [])
        raw_text = str(result.get("raw_text") or "")

        print(f"Saving: name={name}, email={email}")

        resume = Resume(
            filename=str(file.filename),
            name=name,
            email=email,
            phone=phone,
            skills=skills,
            experience=experience,
            education=education,
            raw_text=raw_text
        )

        db.add(resume)
        db.commit()
        db.refresh(resume)

        try:
            upsert_resume(resume)
        except Exception as e:
            print(f"ChromaDB indexing warning: {e}")

        return {
            "message": "Resume uploaded, parsed and saved!",
            "id": resume.id,
            "name": resume.name,
            "email": resume.email,
            "skills": parsed.get("skills", []),
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", [])
        }

    except Exception as e:
        db.rollback()
        print(f"FULL ERROR: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")