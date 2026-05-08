# SkillForge 🌱

A personal learning resource tracker that helps you organise, discover, and manage your academic journey. Built with FastAPI, vanilla JavaScript, and MySQL — with AI-powered summarisation via Google Gemini.

![SkillForge Dashboard](https://img.shields.io/badge/status-live-brightgreen) ![Python](https://img.shields.io/badge/python-3.12-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal) ![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)

---

## Screenshots

### Dashboard
![Dashboard](docs/Home_no_login.png)

### Resource Cards
![Resource Cards](docs/categories.png)

### Login
![Login](docs/login.png)

### Register
![Login](docs/Register.png)

### Add Resource
![Add Resource](docs/Add_Resource.png)

### Resource Cards
![Youtube Resource](docs/Youtube_Resources.png)




## Features

**Resource Management**
- Add, edit, and delete learning resources (YouTube videos, playlists, websites, GitHub repos)
- Auto-generate title and summary from any URL using Google Gemini AI
- Tag resources and filter by tag, domain, type, or status
- Duplicate link detection

**Progress Tracking**
- Mark resources as Not Started / In Progress / Complete
- Filter the full library by status

**Authentication & Roles**
- JWT-based login stored in memory (clears on refresh by design)
- Three roles: `owner`, `contributor`, `viewer`
- RBAC enforced on all mutating endpoints

**Frontend**
- Single-page app — no framework, vanilla HTML/CSS/JS
- Neumorphic light theme with animated background
- YouTube thumbnails auto-fetched
- Responsive design

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy (Python 3.12) |
| Database | MySQL 8 |
| Frontend | Vanilla HTML + CSS + JS |
| AI | Google Gemini API (`gemini-3-flash-preview`) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Package manager | `uv` |
| Deployment | Railway |

---

## Project Structure

```
skillforge/
├── backend/
│   ├── app.py        ← all routes and API logic
│   ├── models.py     ← SQLAlchemy models + Enums
│   ├── schemas.py    ← Pydantic request/response schemas
│   ├── database.py   ← DB engine + session
│   ├── auth.py       ← JWT + bcrypt utilities
│   └── seed.py       ← one-time script to promote first user to owner
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── Logo.png
├── .env              ← secrets (never commit this)
└── pyproject.toml
```

---

## Getting Started

### Prerequisites
- Python 3.12+
- MySQL 8
- [`uv`](https://github.com/astral-sh/uv) package manager
- Google Gemini API key

### 1. Clone the repo

```bash
git clone https://github.com/your-username/skillforge.git
cd skillforge
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/skillforge
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_random_secret_key_here
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Run the app

```bash
uv run uvicorn backend.app:app --reload
```

Visit `http://127.0.0.1:8000`



This promotes the first registered user to `owner` role.

---

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/resources` | — | List resources (filterable) |
| `POST` | `/resources/` | owner / contributor | Add a resource |
| `PUT` | `/resources/{id}` | owner | Update a resource |
| `DELETE` | `/resources/{id}` | owner | Delete a resource |
| `POST` | `/api/summarize` | — | AI summarise a URL |
| `GET` | `/tags` | — | List all tags |
| `POST` | `/tags` | owner / contributor | Create a tag |
| `POST` | `/auth/register` | — | Register a new user |
| `POST` | `/auth/login` | — | Login, returns JWT |
| `GET` | `/auth/me` | any logged-in | Get current user |

Full interactive docs available at `/docs` when running locally.

---

## RBAC

| Action | Owner | Contributor | Viewer |
|--------|-------|-------------|--------|
| View resources | ✅ | ✅ | ✅ |
| Add resources | ✅ | ✅ | ❌ |
| Edit resources | ✅ | ❌ | ❌ |
| Delete resources | ✅ | ❌ | ❌ |

---

## Important Notes

- **bcrypt** must stay pinned to `4.0.1` — newer versions break `passlib`
- **Static files** are mounted at `/static` and must be last in `app.py`
- **JWT** is stored in a JS variable — it clears on page refresh by design (no localStorage)
- **Railway deployment**: MySQL enum columns use UPPERCASE values (`NOT_STARTED`, `VIDEO`, etc.) — do not change enum string values without a matching `ALTER TABLE` migration

---

## Roadmap

-  Per-user progress tracking (junction table replacing global status)
- Contributor application flow with owner approval
-  Persistent login via httpOnly cookie
-  Tag filter on Domain page
- Favorites / bookmarks
- Skill tree visualisation
- Alembic migrations

---

## License

MIT