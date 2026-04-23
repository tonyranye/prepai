from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import io

from llm import get_interview_prep, parse_sections
from parser import parse_resume



'''
What it does

Three endpoints:

POST /api/analyze/text - takes resume text + JD as JSON, returns all 10 parsed sections this is what vue will call
                        when the user pasts ther resume.

POST /api/analyze/file - takes a file uploaded + JD as form data, parses the pdf/Docx first then runs the analysis.

POST /api/parse - just parses a file and returns the text, no analysis. Useful for hsowing a preview of what was extracted

CORS middleware - allows your vue server at localhost: 5173 to talk to FastAPI at localhost:8000

'''

# App setup
app = FastAPI(
    title="PrepAI",
    description="Ai-powered resume and interview coaching backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vue dev server
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Requests
class AnalyzeTextRequest(BaseModel):
    resume_text: str
    jd_text: str

class AnalyzeResponse(BaseModel):
    sections: dict
    raw: str


# Routes
@app.get("/")
def root():
    return {"status": "PrepAI is running"}

@app.get("/health")
def health():
    return {"Status": "ok"}

# ── Analyze with pasted text ──────────────────────────────────────────────────
@app.post("/api/analyze/text")
async def analyze_text(request: AnalyzeTextRequest):
    """
    Analyze a resume provided as plain text against a job description.
    Returns all 10 parsed sections.
    """
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")
    if not request.jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description is required")

    try:
        raw = get_interview_prep(request.resume_text, request.jd_text)
        sections = parse_sections(raw)
        return {"sections": sections, "raw": raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ── Analyze with file upload ──────────────────────────────────────────────────
@app.post("/api/analyze/file")
async def analyze_file(
        file: UploadFile = File(...),
        jd_text: str = Form(...)
):
    """
    Analyze a resume uploaded as PDF or DOCX against a job description.
    Returns all 10 parsed sections.
    """
    if not jd_text.strip():
        raise HTTPException(status_code=400, detail="Job description is required")

    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    try:
        contents = await file.read()
        file_like = io.BytesIO(contents)
        file_like.name = file.filename
        resume_text = parse_resume(file_like)

        if not resume_text or resume_text.startswith("Error"):
            raise HTTPException(status_code=400, detail="Could not parse resume file")

        raw = get_interview_prep(resume_text, jd_text)
        sections = parse_sections(raw)
        return {"sections": sections, "raw": raw}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ── Parse resume file only (no analysis) ─────────────────────────────────────
@app.post("/api/parse")
async def parse_file(file: UploadFile = File(...)):
    """
    Parse a resume file and return the extracted text.
    Useful for previewing what was extracted before running analysis.
    """
    try:
        contents = await file.read()
        file_like = io.BytesIO(contents)
        file_like.name = file.filename
        resume_text = parse_resume(file_like)

        if not resume_text or resume_text.startswith("Error"):
            raise HTTPException(status_code=400, detail="Could not parse resume file")

        return {"text": resume_text, "filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse failed: {str(e)}")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
