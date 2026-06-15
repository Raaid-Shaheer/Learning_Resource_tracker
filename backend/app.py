import os
import re
import base64
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
from google import genai  
import json

from fastapi import FastAPI, Depends, HTTPException, Body, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend import models, schemas
from backend.database import engine, get_db
from backend.models import Base, Domain, ResourceType,ResourceStatus,User, UserRole,ApplicationStatus, ContributorApplication
from backend.schemas import UserCreate, UserOut, Token, ApplicationCreate, ApplicationOut, ApplicationCreated
from fastapi.security import OAuth2PasswordRequestForm
from backend.auth import hash_password, verify_password, create_access_token, decode_access_token, set_auth_cookie



# 1. Load .env and initialize Gemini
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


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
Base.metadata.create_all(bind=engine)

# ── Pydantic Models ───────────────────────────────────────────

class SummarizeRequest(BaseModel):
    url: str

# ── Extraction Helpers ────────────────────────────────────────

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

    # Try transcript first
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        return " ".join([item['text'] for item in transcript])
    except Exception:
        print(f"No transcript for {video_id}, trying yt-dlp")

    # Fallback: 
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        res = requests.get(oembed_url, timeout=10)
        if res.ok:
            data = res.json()
            title = data.get("title", "")
            author = data.get("author_name", "")
            print(f"oEmbed title: {title}")
            return f"{title} by {author}"
        else:
            print(f"oEmbed failed: {res.status_code}")
            return ""
    except Exception as e:
        print(f"oEmbed fallback failed: {e}")
        return ""

def extract_github_readme(url: str) -> str:
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return ""
    username, repo = match.groups()
    try:
        github_token = os.getenv("GITHUB_TOKEN", "")
        headers = {'User-Agent': 'skillforge-app'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        api_url = f"https://api.github.com/repos/{username}/{repo}/readme"
        res = requests.get(api_url, headers=headers, timeout=10)
        if not res.ok:
            return ""
        content_b64 = res.json()['content']
        return base64.b64decode(content_b64).decode('utf-8')
    except Exception as e:
        print(f"GitHub readme fetch failed: {e}")
        return ""

# ── AI Logic ──────────────────────────────────────────────────

def generate_summary(text: str) -> str:
    if not text.strip():
        return {"title": "", "summary": "No content found to summarize."}
    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=f"""
You are analyzing the following content extracted from a learning resource.

Return a JSON object with exactly two keys:
- "title": a clean, human-readable title (use the actual page/video title if present in the content, then polish it — remove site names, pipes, dashes at the end)
- "summary": 2-3 sentences describing what this resource teaches and who it's for

Content:
{text[:3000]}

Return ONLY raw JSON. No markdown, no backticks, no explanation.
"""
        )
        raw = response.text.strip()
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        print(f"Error with primary model: {e}")
        return {"title": "", "summary": "Error generating summary."}

def get_current_user(access_token: str = Cookie(default=None), db: Session = Depends(get_db)) -> models.User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Not Authenticated")
    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(*allowed_roles):
    def checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return checker

# ── API Routes ────────────────────────────────────────────────

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Username already exists")
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already exists")
    hashed_password = hash_password(plain=user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/auth/me", response_model=UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/auth/me/statuses")
def get_my_statuses(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = db.query(models.UserResourceStatus).filter(
        models.UserResourceStatus.user_id == current_user.id
    ).all()
    return {str(row.resource_id): row.status for row in rows}

@app.post("/auth/login")
def login(credentials: OAuth2PasswordRequestForm = Depends(), response: Response = None, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not existing_user:
        raise HTTPException(status_code=401, detail="No such username found")
    if not verify_password(credentials.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = create_access_token({"user_id": existing_user.id, "role": existing_user.role.value})
    set_auth_cookie(response, token)
    return {"message": "Logged in", "role": existing_user.role.value, "username": existing_user.username}

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

@app.post("/auth/apply", response_model=ApplicationCreated)
def apply_to_contribute(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    existing = db.query(models.ContributorApplication).filter(
        models.ContributorApplication.user_id == current_user.id,
        models.ContributorApplication.status.in_([
            models.ApplicationStatus.PENDING,
            models.ApplicationStatus.APPROVED
        ])
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already has an active application")
    new_application = models.ContributorApplication(
        user_id=current_user.id,
        message=body.message
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    return new_application

@app.get("/auth/applications", response_model=list[ApplicationOut])
def list_applications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.owner))
):
    applications = db.query(models.ContributorApplication).filter(
        models.ContributorApplication.status == models.ApplicationStatus.PENDING
    ).all()
    for app in applications:
        user = db.query(models.User).filter(models.User.id == app.user_id).first()
        app.username = user.username if user else "Unknown"
    return applications

@app.put("/auth/applications/{id}/approve", response_model=ApplicationOut)
def approve_application(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.owner))
):
    application = db.query(models.ContributorApplication).filter(
        models.ContributorApplication.id == id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {id} not found")
    application.status = models.ApplicationStatus.APPROVED
    applicant_user = db.query(models.User).filter(
        models.User.id == application.user_id
    ).first()
    applicant_user.role = models.UserRole.contributor
    application.username = applicant_user.username
    db.commit()
    db.refresh(application)
    return application

@app.put("/auth/applications/{id}/reject", response_model=ApplicationOut)
def reject_application(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(models.UserRole.owner))
):
    application = db.query(models.ContributorApplication).filter(
        models.ContributorApplication.id == id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {id} not found")
    application.status = models.ApplicationStatus.REJECTED
    user = db.query(models.User).filter(models.User.id == application.user_id).first()
    application.username = user.username if user else "Unknown"
    db.commit()
    db.refresh(application)
    return application

@app.post("/api/summarize")
async def summarize_endpoint(req: SummarizeRequest):
    url = req.url
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")
    if "youtube.com" in url or "youtu.be" in url:
        content = extract_youtube_transcript(url)
    elif "github.com" in url:
        content = extract_github_readme(url)
    else:
        content = extract_website_text(url)
    result = generate_summary(content)
    return {"success": True, **result}

@app.get("/tags", response_model=list[schemas.Tag])
def get_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()

@app.post("/tags", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(UserRole.owner, UserRole.contributor))):
    existing = db.query(models.Tag).filter(models.Tag.name == tag.name).first()
    if existing:
        return existing
    new_tag = models.Tag(name=tag.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

@app.post("/resources/", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(UserRole.owner, UserRole.contributor))):
    existing = db.query(models.Resource).filter(models.Resource.link == resource.link).first()
    if existing:
        raise HTTPException(status_code=409, detail="A resource with this link already exists.")
    db_resource = models.Resource(
        title=resource.title,
        link=resource.link,
        domain=resource.domain,
        resource_type=resource.resource_type,
        description=resource.description,
        status=resource.status
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
    status: ResourceStatus | None = None,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(models.Resource)
    if title:
        query = query.filter(models.Resource.title.ilike(f"%{title}%"))
    if domain:
        query = query.filter(models.Resource.domain == domain)
    if resource_type:
        query = query.filter(models.Resource.resource_type == resource_type)
    if status:
        query = query.filter(models.Resource.status == status)
    if tag:
        query = query.filter(models.Resource.tags.any(models.Tag.name == tag))
    return query.all()

@app.get("/resources/{resource_id}", response_model=schemas.Resource)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
    return resource

@app.put("/resources/{resource_id}", response_model=schemas.Resource)
def update_resource(resource_id: int, updated: schemas.ResourceUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(UserRole.owner))):
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
def delete_resource(resource_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(UserRole.owner))):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
    db.delete(resource)
    db.commit()
    return {"message": f"Resource {resource_id} deleted"}

@app.post("/resources/{id}/status")
def set_resource_status(
    id: int,
    body: schemas.StatusUpdate = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.UserResourceStatus).filter(
        models.UserResourceStatus.user_id == current_user.id,
        models.UserResourceStatus.resource_id == id
    ).first()
    if existing:
        existing.status = body.status
    else:
        new_status = models.UserResourceStatus(
            user_id=current_user.id,
            resource_id=id,
            status=body.status
        )
        db.add(new_status)
    db.commit()
    return {"message": "Status updated"}

@app.get("/resources/{id}/status")
def get_resource_status(
    id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.UserResourceStatus).filter(
        models.UserResourceStatus.user_id == current_user.id,
        models.UserResourceStatus.resource_id == id
    ).first()
    if not existing:
        return {"status": models.ResourceStatus.NOT_STARTED}
    return {"status": existing.status}

# ── Helpers ───────────────────────────────────────────────────

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


# ── Static Files ──────────────────────────────────────────────
# MUST be last — mounted at /static so it never intercepts API routes.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")