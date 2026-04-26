from pydantic import BaseModel, Field
from .models import Domain, ResourceType    


# ── Tag schemas ───────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)

class Tag(BaseModel):
    id:   int
    name: str

    class Config:
        from_attributes = True


# ── Resource schemas ──────────────────────────────────────────

class ResourceCreate(BaseModel):
    title:         str
    link:          str
    domain:        Domain          
    resource_type: ResourceType
    description:   str | None = None
    tags:          list[str] = []      

class Resource(BaseModel):
    # this is the OUTPUT schema — what the API sends back
    #    tags here is a list of Tag objects, not plain strings
    #    Pydantic will use from_attributes to read them off the SQLAlchemy model
    id:            int
    title:         str
    link:          str
    domain:        Domain
    resource_type: ResourceType
    description:   str | None = None
    tags:          list[Tag] = []           # ← list of Tag objects on the way out

    class Config:
        from_attributes = True

class ResourceUpdate(BaseModel):
    #every field is optional here — you only send what you want to change
    #    tags: None means "don't touch tags", tags: [] means "remove all tags"
    title:         str | None = None
    link:          str | None = None
    domain:        Domain | None = None
    resource_type: ResourceType | None = None
    description:   str | None = None
    tags:          list[str] | None = None  # ← None = untouched, [] = cleared