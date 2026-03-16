from fastapi import FastAPI, Depends,HTTPException
from .database import engine
from .models import Base
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db


app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Learning Resource Tracker API is running"}

@app.post("/resources/", response_model=schemas.Resource)
def create_resource(resource: schemas.ResourceCreate, db: Session= Depends(get_db)):

    db_resource = models.Resource(
        title = resource.title,
        link = resource.link,
        category = resource.category,
        description = resource.description
    )

    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)

    return db_resource

@app.get("/resources", response_model=list[schemas.Resource])
def get_resources(db: Session = Depends(get_db)):

    resources = db.query(models.Resource).all()

    return resources

@app.get("/resources/{resource_id}", response_model=schemas.Resource)
def get_resource(resource_id: int, db: Session = Depends(get_db)):

    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()

    return resource

@app.delete("/resources/{resource_id}", response_model=dict)

def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()

    #if no resource 

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
        setattr(resource, key, value)  # dynamic update
    
    db.commit()
    db.refresh(resource)
    
    return resource