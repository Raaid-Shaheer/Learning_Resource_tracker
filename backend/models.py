from sqlalchemy import Column, Integer, String, Text, Enum, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime,timezone

def utcnow():
    return datetime.now(timezone.utc)

class Domain(str, enum.Enum):    
    CS    = "CS"
    ECE   = "ECE"
    OTHER = "Other"

class ResourceType(str, enum.Enum):
    VIDEO    = "Video"
    PLAYLIST = "Playlist"
    WEBSITE  = "Website"
    GITHUB   = "Github Repo"

class UserRole(str, enum.Enum):
    owner       = "owner"
    contributor = "contributor"
    viewer      = "viewer"

class ResourceStatus(str, enum.Enum):
    NOT_STARTED = "not_started"   
    IN_PROGRESS = "in_progress"
    COMPLETE    = "complete"

resource_tags = Table(
    "resource_tags",
    Base.metadata,
    Column("resource_id", Integer, ForeignKey("resources.id"), primary_key=True),
    Column("tag_id",      Integer, ForeignKey("tags.id"),      primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resources = relationship("Resource", secondary=resource_tags, back_populates="tags")

class Resource(Base):
    __tablename__ = "resources"
    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(255), nullable=False)
    link          = Column(String(500), nullable=False)
    domain        = Column(Enum(Domain), nullable=False)        
    resource_type = Column(Enum(ResourceType), nullable=False)
    description   = Column(Text)
    status        = Column(Enum(ResourceStatus), default=ResourceStatus.NOT_STARTED, nullable=False)
    tags          = relationship("Tag", secondary=resource_tags, back_populates="resources")

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username      = Column(String(100), nullable=False, unique=True)
    email         = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), default=UserRole.viewer)
    created_at    = Column(DateTime(timezone=True), default=utcnow)