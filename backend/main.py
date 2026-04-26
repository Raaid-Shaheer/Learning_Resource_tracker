from fastapi import FastAPI, Depends, HTTPException
from .database import engine
from .models import Base, Domain, ResourceType          # ← Domain replaces Department
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500",
                   "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 READ: create_all only creates tables that DON'T exist yet
#    It will now also create the new `tags` and `resource_tags` tables
#    The existing `resources` table is left completely untouched

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Learning Resource Tracker API is running"}


# ── Tags endpoints ────────────────────────────────────────────

@app.get("/tags", response_model=list[schemas.Tag])
def get_tags(db: Session = Depends(get_db)):
    # 🔍 READ: returns every tag in the database
    #    the frontend uses this to show preset suggestions
    return db.query(models.Tag).order_by(models.Tag.name).all()

@app.post("/tags", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    # 🔍 READ: check if tag already exists before creating
    #    unique=True on the column would raise a DB error without this check
    existing = db.query(models.Tag).filter(models.Tag.name == tag.name).first()
    if existing:
        return existing          # return it rather than error — idempotent
    new_tag = models.Tag(name=tag.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


# ── Resource endpoints ────────────────────────────────────────

@app.post("/resources/", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session = Depends(get_db)):
    db_resource = models.Resource(
        title=resource.title,
        link=resource.link,
        domain=resource.domain,                  # ← renamed from department
        resource_type=resource.resource_type,
        description=resource.description,
    )
    # 🔍 READ: tags need special handling — they're not a plain column
    #    we fetch or create each Tag object, then assign the whole list
    if resource.tags:
        db_resource.tags = _resolve_tags(resource.tags, db)

    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource


@app.get("/resources", response_model=list[schemas.Resource])
def get_resources(
    title: str | None = None,
    domain: Domain | None = None,                # ← renamed from department
    resource_type: ResourceType | None = None,
    tag: str | None = None,                      # ← new: filter by tag name
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
        # 🔍 READ: .any() checks if at least one tag in the relationship matches
        #    without this you'd have to write a manual JOIN
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

    # Update plain fields
    for key, value in updated.dict(exclude_unset=True, exclude={"tags"}).items():
        setattr(resource, key, value)

    # 🔍 READ: tags get replaced entirely — the new list overwrites the old one
    #    SQLAlchemy handles the junction table inserts/deletes automatically
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


# ── Helper ────────────────────────────────────────────────────

def _resolve_tags(tag_names: list[str], db: Session) -> list[models.Tag]:
    # 🔍 READ: for each tag name, either fetch the existing Tag row
    #    or create a new one. Returns a list of Tag objects.
    #    This is what lets users type new tags and reuse existing ones.
    tags = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(models.Tag).filter(models.Tag.name == name).first()
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.flush()      # gets the new tag an ID without full commit
        tags.append(tag)
    return tags