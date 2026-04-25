from pydantic import BaseModel
from app.models import Department, ResourceType

class ResourceCreate(BaseModel):
    title: str
    link: str
    department: Department         
    resource_type: ResourceType     
    description: str | None = None

class Resource(ResourceCreate):
    id: int

    class Config:
        from_attributes = True

class ResourceUpdate(BaseModel):
    title: str | None = None
    link: str | None = None
    department: Department | None = None
    resource_type: ResourceType | None = None
    description: str | None = None