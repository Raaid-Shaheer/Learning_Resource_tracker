from pydantic import BaseModel

class ResourceCreate(BaseModel):
  title: str
  link: str
  category: str
  description: str | None = None

class Resource(ResourceCreate):
  id: int

  class Config:
    from_attributes = True

class Resource(BaseModel):
  id: int
  title: str
  link: str
  category: str
  description: str

  class config:
    orm_mode = True

class ResourceUpdate(BaseModel):
  title: str | None = None
  link: str | None = None
  category: str | None = None
  description: str | None = None

  