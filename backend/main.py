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