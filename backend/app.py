import os
import re
import base64
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from google import genai  

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os



# Local database imports (assuming these files exist in your project structure)
from backend.database import engine, get_db
from backend.models import Base, Domain, ResourceType
from backend import models, schemas

# 1. Load the .env file and initialize Gemini Client
basedir = os.path.abspath(os.path.dirname(__file__))
# Adjust the path to your .env file if necessary
load_dotenv(os.path.join(basedir, '../.env'))

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
print(f"DEBUG: API Key loaded: {api_key is not None}")

# 2. Initialize FastAPI
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Database Setup
# create_all only creates tables that DON'T exist yet
Base.metadata.create_all(bind=engine)

# ── Pydantic Models for Summarizer ────────────────────────────

class SummarizeRequest(BaseModel):
    url: str

# ── EXTRACTION HELPERS (From Flask app) ───────────────────────

def extract_website_text(url: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs])
        return text[:10000] 
    except Exception:
        return ""

def extract_youtube_transcript(url: str) -> str:
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if not video_id_match:
        return ""
    video_id = video_id_match.group(1)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript])
    except Exception:
        return ""

def extract_github_readme(url: str) -> str:
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match: return ""
    username, repo = match.groups()
    try:
        api_url = f"https://api.github.com/repos/{username}/{repo}/readme"
        res = requests.get(api_url)
        content_b64 = res.json()['content']
        return base64.b64decode(content_b64).decode('utf-8')
    except Exception:
        return ""

# ── AI LOGIC ──────────────────────────────────────────────────

def generate_summary(text: str) -> str:
    if not text.strip():
        return "No content found to summarize."
    
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview', 
            contents=f"Summarize this content in 2-3 sentences:\n\n{text}"
        )
        return response.text
    except Exception as e:
        print(f"Error with primary model: {e}")
        return "Error generating summary. Please check model availability."

# ── API ROUTES ────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# ── AI Summarizer Endpoints ───────────────────────────────────

@app.post("/api/summarize")
async def summarize_endpoint(req: SummarizeRequest):
    url = req.url
    
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    # Determine which extractor to use
    if "youtube.com" in url or "youtu.be" in url:
        content = extract_youtube_transcript(url)
    elif "github.com" in url:
        content = extract_github_readme(url)
    else:
        content = extract_website_text(url)

    # Generate and return summary
    summary = generate_summary(content)
    
    return {
        "success": True,
        "summary": summary
    }

# ── Tags Endpoints ────────────────────────────────────────────

@app.get("/tags", response_model=list[schemas.Tag])
def get_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()

@app.post("/tags", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Tag).filter(models.Tag.name == tag.name).first()
    if existing:
        return existing          
    new_tag = models.Tag(name=tag.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

# ── Resource Endpoints ────────────────────────────────────────

@app.post("/resources/", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session = Depends(get_db)):
    db_resource = models.Resource(
        title=resource.title,
        link=resource.link,
        domain=resource.domain,                 
        resource_type=resource.resource_type,
        description=resource.description,
    )
    if resource.tags:
        db_resource.tags = _resolve_tags(resource.tags, db)

    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


@app.get("/resources", response_model=list[schemas.Resource])
def get_resources(
    title: str | None = None,
    domain: Domain | None = None,                
    resource_type: ResourceType | None = None,
    tag: str | None = None,                      
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Resource)

    if title:
        query = query.filter(models.Resource.title.ilike(f"%{title}%"))
    if domain:
        query = query.filter(models.Resource.domain == domain)
    if resource_type:
        query = query.filter(models.Resource.resource_type == resource_type)
    if tag:
        query = query.filter(models.Resource.tags.any(models.Tag.name == tag))

    return query.offset(skip).limit(limit).all()


@app.get("/resources/{resource_id}", response_model=schemas.Resource)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
    return resource


@app.put("/resources/{resource_id}", response_model=schemas.Resource)
def update_resource(resource_id: int, updated: schemas.ResourceUpdate, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    for key, value in updated.dict(exclude_unset=True, exclude={"tags"}).items():
        setattr(resource, key, value)

    if updated.tags is not None:
        resource.tags = _resolve_tags(updated.tags, db)

    db.commit()
    db.refresh(resource)
    return resource


@app.delete("/resources/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
    db.delete(resource)
    db.commit()
    return {"message": f"Resource {resource_id} deleted"}

# ── Helper Functions ──────────────────────────────────────────

def _resolve_tags(tag_names: list[str], db: Session) -> list[models.Tag]:
    tags = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(models.Tag).filter(models.Tag.name == name).first()
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.flush()     
        tags.append(tag)
    return tags

# Run with: uv run uvicorn app.app:app --reload 
