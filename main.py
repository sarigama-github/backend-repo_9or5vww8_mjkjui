import os
from typing import List, Optional, Literal
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from database import db, create_document
from schemas import Resume
import io

app = FastAPI(title="AI Resume Builder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BasicInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    education: List[dict] = []
    experience: List[dict] = []
    skills: List[str] = []
    certifications: List[dict] = []
    achievements: List[str] = []
    target_role: Optional[str] = None

class GenerateOptions(BaseModel):
    region: Literal["United States","Canada","United Kingdom","Australia","Dubai (UAE)","Singapore","Hong Kong","India","Europe (EU Standard CV)"] = "United States"
    resume_type: Literal["Chronological","Functional","Combination","Infographic","Profile","Targeted","Nontraditional","Mini-Resume"] = "Chronological"
    tone: Literal["Formal","Concise","Creative","Executive"] = "Formal"

class GenerateFromBasicRequest(BaseModel):
    basic: BasicInfo
    options: GenerateOptions

class OptimizeRequest(BaseModel):
    resume: Resume
    options: GenerateOptions

@app.get("/")
def root():
    return {"message": "Resume Builder API running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Very light parsers for input documents

def parse_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except Exception:
        try:
            return content.decode("latin-1")
        except Exception:
            return ""

# Placeholder simple extractors (heuristic). In a full version, integrate robust parsers & LLMs.

def heuristic_extract(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name = lines[0] if lines else ""
    email = next((l for l in lines if "@" in l and "." in l), "user@example.com")
    phone = next((l for l in lines if (any(ch.isdigit() for ch in l) and "+" in l) or l.replace(" ", "").isdigit()), None)
    skills = []
    for l in lines:
        if l.lower().startswith("skills") or "skills:" in l.lower():
            parts = l.split(":", 1)
            if len(parts) == 2:
                skills = [s.strip() for s in parts[1].replace("|", ",").split(",") if s.strip()]
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "summary": None,
        "education": [],
        "experience": [],
        "skills": skills,
        "certifications": [],
        "achievements": []
    }

@app.post("/api/parse-upload")
async def parse_upload(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    content = await file.read()
    extracted = {}

    if filename.endswith(".txt"):
        text = parse_txt(content)
        extracted = heuristic_extract(text)
    elif filename.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF (optional)
            with io.BytesIO(content) as f:
                doc = fitz.open(stream=f.read(), filetype="pdf")
                full_text = "\n".join(page.get_text() for page in doc)
            extracted = heuristic_extract(full_text)
        except Exception:
            extracted = heuristic_extract("")
    elif filename.endswith(".docx"):
        try:
            from docx import Document  # optional python-docx
            with io.BytesIO(content) as f:
                document = Document(f)
                text = "\n".join(p.text for p in document.paragraphs)
            extracted = heuristic_extract(text)
        except Exception:
            extracted = heuristic_extract("")
    else:
        extracted = heuristic_extract("")

    try:
        create_document("resume", extracted)
    except Exception:
        pass

    return {"extracted": extracted}

# AI-like rewrite stub (no external LLM). For demo we just format cleanly.

def rewrite_content(resume: dict, tone: str) -> dict:
    out = resume.copy()
    if resume.get("summary") and tone == "Concise":
        s = resume["summary"]
        out["summary"] = (s[:220] + ("…" if len(s) > 220 else ""))
    return out

# Region/type adaptation (structure & minor phrasing)

def adapt_by_region_and_type(resume: dict, region: str, rtype: str) -> dict:
    out = resume.copy()
    if rtype == "Functional":
        out["_layout"] = "skills-first"
    elif rtype == "Chronological":
        out["_layout"] = "experience-first"
    elif rtype == "Mini-Resume":
        out["experience"] = out.get("experience", [])[:3]
        out["education"] = out.get("education", [])[:1]
        out["skills"] = out.get("skills", [])[:10]
    return out

@app.post("/api/generate-from-basic")
async def generate_from_basic(payload: GenerateFromBasicRequest):
    basic = payload.basic
    options = payload.options
    resume_dict = basic.model_dump()
    resume_dict = rewrite_content(resume_dict, options.tone)
    resume_dict = adapt_by_region_and_type(resume_dict, options.region, options.resume_type)
    try:
        create_document("resume", resume_dict)
    except Exception:
        pass
    return {"resume": resume_dict, "ats_score": 78}

@app.post("/api/optimize")
async def optimize_resume(payload: OptimizeRequest):
    data = payload.resume.model_dump()
    options = payload.options
    data = rewrite_content(data, options.tone)
    data = adapt_by_region_and_type(data, options.region, options.resume_type)
    score = 80
    if len(data.get("skills", [])) >= 8:
        score += 5
    if data.get("summary"):
        score += 3
    score = min(score, 95)
    try:
        create_document("resume", data)
    except Exception:
        pass
    return {"resume": data, "ats_score": score}

@app.get("/api/templates")
async def list_templates():
    templates = [
        {"key": "clean", "name": "Clean", "style": "clean"},
        {"key": "minimal", "name": "Minimal", "style": "minimal"},
        {"key": "bold", "name": "Bold", "style": "bold"},
        {"key": "classic", "name": "Classic", "style": "classic"},
        {"key": "creative", "name": "Creative", "style": "creative"}
    ]
    return {"templates": templates}
