# 📚 SkillForge — Project Documentation

## 🗂️ Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [What's Been Built](#whats-been-built)
5. [What's Coming Next](#whats-coming-next)
6. [Security & Best Practices](#security--best-practices)
7. [Authentication Plan](#authentication-plan)
8. [API Reference](#api-reference)
9. [Database Schema](#database-schema)
10. [Cyber Attack Prevention](#cyber-attack-prevention)
11. [Teaching & Collaboration Approach](#teaching--collaboration-approach)

---

## 📌 Project Overview

A personal Learning Resource Tracker — now branded **SkillForge** — where:
- **You (the owner)** can add, edit, and delete resources
- **Other users** can only view and suggest resources
- Resources are organized by **Domain** (CS / ECE / Other) and **Type** (Video / Playlist / Website / GitHub)
- Resources can be tagged with freeform or preset **tags** (e.g. Python, AI, Machine Learning)
- Built with a FastAPI backend, MySQL database, and a premium SPA frontend
- Includes an **AI summarizer** powered by Gemini that auto-fills descriptions from URLs

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI |
| Database | MySQL (via MySQL Workbench) |
| ORM | SQLAlchemy |
| Data Validation | Pydantic |
| Language | Python 3.12 |
| Virtual Environment | uv |
| AI Summarizer | Google Gemini API (`google-genai`) |
| Web Scraping | BeautifulSoup, youtube-transcript-api, requests |
| Frontend | HTML + CSS + JavaScript (SPA) |
| Fonts | Manrope, Plus Jakarta Sans (Google Fonts) |
| Icons | Material Symbols Outlined |
| Authentication | JWT (planned) |
| Deployment | TBD (Render / Railway) |

---

## 📁 Project Structure

```
skillforge/
├── backend/                  # Previously app/
│   ├── __init__.py
│   ├── app.py               # ✅ MAIN ENTRYPOINT — all routes live here
│   ├── models.py            # SQLAlchemy models + Enums
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # DB connection
│   ├── crud.py              # (empty, planned)
│   └── main.py             # ⚠️ DEAD FILE — safe to delete
├── frontend/
│   ├── index.html           # SPA shell — 3 pages in one file
│   ├── style.css            # Full design system (neumorphic light theme)
│   ├── app.js               # SPA router + API calls + tag system
│   └── Logo.png             # SkillForge logo
├── .env                     # ⚠️ secrets — NEVER commit
├── .gitignore
├── requirements.txt
└── README.md
```

**Run command:**
```bash
uv run uvicorn backend.app:app --reload
```

The frontend is now **served by FastAPI** (not Live Server). Go to `http://127.0.0.1:8000`.

---

## ✅ What's Been Built

### Backend

#### Database Models (`models.py`)
- `Domain` enum: `CS` | `ECE` | `Other` *(renamed from Department)*
- `ResourceType` enum: `Video` | `Playlist` | `Website` | `Github Repo`
- `Resource` table: `id`, `title`, `link`, `domain`, `resource_type`, `description`, + `tags` relationship
- `Tag` table: `id`, `name` (unique, indexed)
- `resource_tags` junction table: many-to-many between Resource and Tag

#### Pydantic Schemas (`schemas.py`)
- `TagCreate` — input: `name`
- `Tag` — output: `id`, `name`
- `ResourceCreate` — input includes `tags: list[str]`
- `Resource` — output includes `tags: list[Tag]`
- `ResourceUpdate` — all fields optional; `tags: None` = untouched, `tags: []` = clear all

#### API Endpoints (`backend/app.py`)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves `frontend/index.html` |
| GET | `/tags` | Get all tags (sorted) |
| POST | `/tags` | Create a tag (idempotent) |
| POST | `/resources/` | Create resource + tags |
| GET | `/resources` | List resources (filter by title, domain, resource_type, tag) |
| GET | `/resources/{id}` | Get one resource |
| PUT | `/resources/{id}` | Update resource + tags |
| DELETE | `/resources/{id}` | Delete resource |
| POST | `/api/summarize` | AI summary from URL (YouTube / GitHub / website) |

#### AI Summarizer
- Accepts a URL via `POST /api/summarize`
- Detects URL type and extracts content:
  - **YouTube** → transcript via `youtube-transcript-api`
  - **GitHub** → README via GitHub API (base64 decoded)
  - **Website** → scraped paragraphs via BeautifulSoup
- Sends extracted text to **Gemini** (`gemini-3-flash-preview`) for a 2–3 sentence summary
- Frontend has an `✨ AI` button next to the Link field — click to auto-fill description

### Frontend (SPA)

#### Pages (all inside `index.html`, swapped by `app.js`)
1. **Home** — hero section + 3 domain cards with live resource counts + Learning Stats
2. **Domain page** — domain hero banner + 4 category chips (Video / Playlist / Website / GitHub) → click chip → filtered resource list
3. **All Resources** — search bar + domain filter + type filter + full list

#### Navigation
- Topnav with brand, global search (Enter → jumps to All Resources), Add button, avatar
- Sidebar with Dashboard / Domains / All Resources / Add Resource links
- Breadcrumb updates on every navigation: `Home › Computer Science › Videos`
- Smooth `fadeUp` page transition animation

#### Resource Cards
- Neumorphic white cards with glassmorphism blur
- **YouTube/Playlist** → auto-fetches thumbnail from `img.youtube.com/vi/{id}/hqdefault.jpg`
- **Website / GitHub** → icon placeholder styled to type
- Type badge + Domain badge per card
- Tag chips displayed below description
- Type-branded Open button: red (YouTube), amber (Playlist), blue (Website), dark (GitHub)
- Edit / Delete icon buttons

#### Tag System
- Modal tag input: type + Enter or comma to add
- Backspace on empty input removes last tag
- Tags shown as removable pills inside the input box
- Preset suggestions loaded from `GET /tags` — click to add instantly
- Already-selected presets greyed out
- On save: unconfirmed text auto-added, `tags: [...]` sent to API

#### Learning Stats (Home Page)
- 4 metric cards: Total Resources, Most Active Domain, Videos & Playlists count, Latest Addition
- Type Breakdown bar: proportional horizontal bar (Video / Playlist / Website / GitHub) with live counts

#### Design System
- **Theme**: Light, neumorphic — white card surfaces on `#eef0f5` base
- **Shadows**: `8px 8px 20px #d1d5e0, -6px -6px 16px #ffffff`
- **Background**: Animated floating blobs (blue, teal, purple)
- **Fonts**: Manrope (headings, display), Plus Jakarta Sans (body)
- **Domain cards**: Deep gradient — navy CS, forest ECE, deep purple Other
- **Category chips**: White neumorphic cards with colored top stripe
- **Responsive**: Sidebar collapses on mobile, grid reflows

---

## 🎯 What's Coming Next

### Phase 2 — Authentication
- [ ] User registration (`POST /auth/register`)
- [ ] User login (`POST /auth/login`)
- [ ] JWT token generation
- [ ] Protected routes (owner only)
- [ ] Role system: `owner` | `viewer` | `contributor`

### Phase 3 — Permissions
- [ ] Owner can approve/reject suggestions
- [ ] Contributors can suggest resources
- [ ] Viewers can only read

### Phase 4 — Deployment
- [ ] Environment variables configured
- [ ] API hosted on Render/Railway
- [ ] Frontend served via FastAPI (already done ✅)
- [ ] Domain configured

### Phase 5 — Enhancements (Optional)
- [ ] Tree view toggle (skill tree visualization)
- [ ] Progress tracking (mark resources as complete)
- [ ] Favorites / bookmarks
- [ ] Filter by tag on All Resources page
- [ ] Tag management page (rename / delete tags)

---

## 🔐 Security & Best Practices

### 1. Environment Variables — Never Hardcode Secrets
```python
# ❌ BAD
DATABASE_URL = "mysql://root:mypassword123@localhost/tracker"

# ✅ GOOD
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

Your `.env` file:
```
DATABASE_URL=mysql://root:mypassword123@localhost/tracker
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=your_gemini_api_key_here
```

> ⚠️ If you accidentally push `.env` to GitHub, treat all secrets as compromised and rotate them immediately.

---

### 2. Authentication with JWT (Planned)
```
User logs in → Server verifies → JWT issued (30 min) → Token sent with every request → Server verifies token
```

**Install:**
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

---

### 3. Password Hashing
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
user.password = pwd_context.hash("mypassword123")
```

---

### 4. Role-Based Access Control (RBAC) — Planned

| Role | View | Suggest | Edit | Delete | Approve |
|---|---|---|---|---|---|
| `owner` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `contributor` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `viewer` | ✅ | ❌ | ❌ | ❌ | ❌ |

---

### 5. Input Validation
```python
from pydantic import BaseModel, HttpUrl, Field

class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    link: HttpUrl
    domain: Domain
    resource_type: ResourceType
    description: str | None = Field(None, max_length=1000)
    tags: list[str] = []
```

---

### 6. CORS Configuration ✅ Done
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> ⚠️ Lock `allow_origins` down to your real domain in production.

---

### 7. Rate Limiting (Planned)
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
def login(...): ...
```

---

### 8. HTTPS Only in Production
Render/Railway handle HTTPS automatically on deploy.

---

## 🛡️ Cyber Attack Prevention

### SQL Injection ✅ Safe
SQLAlchemy uses parameterized queries — raw input never touches SQL strings.

### XSS Prevention
```javascript
// ❌ BAD
element.innerHTML = resource.title;
// ✅ GOOD
element.textContent = resource.title;
```
Tag names are rendered as `textContent` in pills, never as raw HTML.

### CSRF Prevention (Planned)
- JWT in `httpOnly` cookies
- Strict CORS

### Brute Force (Planned)
- Rate limit on `/auth/login`
- Account lockout after repeated failures

### Unauthorized Data Manipulation (Planned)
```python
resource = db.query(models.Resource).filter(
    models.Resource.id == resource_id,
    models.Resource.owner_id == current_user.id
).first()
```

---

## 📖 API Reference

### Base URL
```
Development:  http://127.0.0.1:8000
Production:   https://your-app.render.com (planned)
```

### Tags

#### Get All Tags
```
GET /tags
```

#### Create Tag
```
POST /tags
{ "name": "python" }
```

### Resources

#### Get All Resources
```
GET /resources?title=python&domain=CS&resource_type=Video&tag=machine+learning&skip=0&limit=100
```

#### Get One Resource
```
GET /resources/{id}
```

#### Create Resource
```
POST /resources/
{
  "title": "Python Crash Course",
  "link": "https://youtube.com/watch?v=...",
  "domain": "CS",
  "resource_type": "Video",
  "description": "Great beginner resource",
  "tags": ["python", "beginner"]
}
```

#### Update Resource
```
PUT /resources/{id}
{
  "title": "Updated Title",
  "tags": ["python", "advanced"]
}
```

#### Delete Resource
```
DELETE /resources/{id}
```

#### AI Summarize
```
POST /api/summarize
{ "url": "https://youtube.com/watch?v=..." }
→ { "success": true, "summary": "..." }
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE resources (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    title         VARCHAR(255) NOT NULL,
    link          VARCHAR(500) NOT NULL,
    domain        ENUM('CS', 'ECE', 'Other') NOT NULL,
    resource_type ENUM('Video', 'Playlist', 'Website', 'Github Repo') NOT NULL,
    description   TEXT
);

CREATE TABLE tags (
    id   INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE resource_tags (
    resource_id INT,
    tag_id      INT,
    PRIMARY KEY (resource_id, tag_id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    FOREIGN KEY (tag_id)      REFERENCES tags(id)
);

-- Planned: users table
CREATE TABLE users (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    username      VARCHAR(100) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('owner', 'contributor', 'viewer') DEFAULT 'viewer',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧑‍🏫 Teaching & Collaboration Approach

> This section defines how Claude works with the student on this project.

### Role
Claude joins this project as an **experienced teacher who teaches through projects**. The student is sharp and motivated, but has two specific friction points:
- **Starting from a blank file** — the empty canvas is paralyzing
- **Translating logic into code** — the idea is clear in their head but the syntax feels like a wall

### When a New Topic Comes Up

1. **Analogy first** — plain English using something familiar
2. **Tie it to the project** — where and why it appears in *this* codebase
3. **Then show the code** — only after the mental model is solid

### How Claude Gives Code

- **Skeletons with signposts** — structured comments explain *what goes here* and *why*
- **Reading lessons built in** — teaches how to read code like a developer (function names, parameter types, return types)
- **Fill-in-the-blank progression** — student writes the logic, Claude provides scaffolding

> Example: Before JWT, Claude explains it as a concert wristband — prove identity once at the door, wristband checked from then on.

### Ground Rules

| Situation | What Claude Does |
|---|---|
| New concept appears | Analogy → tie to project → code |
| Student needs to write code | Skeleton with teaching comments |
| Student is stuck on blank file | Claude provides first 5–10 lines to break paralysis |
| Logic → code translation needed | Pseudocode first, then Python mapping |
| Student asks "what does this mean?" | Claude reads the code aloud as a sentence |

---

## 📝 Developer Notes

- Run: `uv run uvicorn backend.app:app --reload`
- API docs: `http://127.0.0.1:8000/docs`
- Frontend served at: `http://127.0.0.1:8000`
- Drop + recreate tables (dev only): add `Base.metadata.drop_all(bind=engine)` before `create_all`, run once, remove immediately
- `backend/main.py` is dead code — safe to delete
- `database.py` has a duplicate `engine` line — remove the first one (the sqlite fallback line)
- Use Alembic migrations in production — never drop tables in prod

---

*Last updated: April 2026*
