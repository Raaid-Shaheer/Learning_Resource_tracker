from fastapi import FastAPI, Depends, HTTPException
from .database import engine
from .models import Base, Department, ResourceType
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500",  # VS Code Live Server
                   "http://localhost:5500"],   # same, different alias
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Learning Resource Tracker API is running"}

@app.post("/resources/", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session = Depends(get_db)):
    db_resource = models.Resource(
        title=resource.title,
        link=resource.link,
        department=resource.department,          
        resource_type=resource.resource_type,    
        description=resource.description
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

@app.get("/resources", response_model=list[schemas.Resource])
def get_resources(
    title: str | None = None,
    department: Department | None = None,           
    resource_type: ResourceType | None = None,      
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(models.Resource)

    if title:
        query = query.filter(models.Resource.title.ilike(f"%{title}%"))

    if department:
        query = query.filter(models.Resource.department == department)

    if resource_type:
        query = query.filter(models.Resource.resource_type == resource_type)

    return query.offset(skip).limit(limit).all()

@app.get("/resources/{resource_id}", response_model=schemas.Resource)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource with id {resource_id} not found")
    return resource

@app.delete("/resources/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource with id {resource_id} not found")
    db.delete(resource)
    db.commit()
    return {"message": f"Resource with id {resource_id} has been deleted"}

@app.put("/resources/{resource_id}", response_model=schemas.Resource)
def update_resource(resource_id: int, updated_resource: schemas.ResourceUpdate, db: Session = Depends(get_db)):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource with id {resource_id} not found")
    for key, value in updated_resource.dict(exclude_unset=True).items():
        setattr(resource, key, value)
    db.commit()
    db.refresh(resource)
    return resource