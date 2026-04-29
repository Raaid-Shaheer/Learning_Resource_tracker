from sqlalchemy import Column, Integer, String, Text, Enum, Table, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import enum
from datetime import datetime,timezone



# ── Helper Functions ────────────────────────────────────────────────────
def utcnow():
    return datetime.now(timezone.utc)

# ── Enums ────────────────────────────────────────────────────

class Domain(str, enum.Enum):    
    CS    = "CS"
    ECE   = "ECE"
    OTHER = "Other"

class ResourceType(str, enum.Enum):
    VIDEO    = "Video"
    PLAYLIST = "Playlist"
    WEBSITE  = "Website"
    GITHUB   = "Github Repo"

class UserRole(str,enum.Enum):
    owner = "owner"
    contributor = "contributor"
    viewer = "viewer"

# ── Association Table ─────────────────────────────────────────
# this is NOT a class — it's a plain Table object
#    It has no columns of its own except the two foreign keys
#    SQLAlchemy uses it silently whenever you access resource.tags

resource_tags = Table(
    "resource_tags",
    Base.metadata,
    Column("resource_id", Integer, ForeignKey("resources.id"), primary_key=True),
    Column("tag_id",      Integer, ForeignKey("tags.id"),      primary_key=True),
)


# ── Tag Model ─────────────────────────────────────────────────

#    The relationship line gives you tag.resources → list of Resource objects

class Tag(Base):
    __tablename__ = "tags"

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    # The other side of the relationship — Tag knows its resources
    resources = relationship("Resource", secondary=resource_tags, back_populates="tags")


# ── Resource Model ────────────────────────────────────────────


class Resource(Base):
    __tablename__ = "resources"

    id            = Column(Integer, primary_key=True, index=True)
    title         = Column(String(255), nullable=False)
    link          = Column(String(500), nullable=False)
    domain        = Column(Enum(Domain), nullable=False)        
    resource_type = Column(Enum(ResourceType), nullable=False)
    description   = Column(Text)

    # SQLAlchemy will automatically join through the resource_tags table for you
    tags = relationship("Tag", secondary=resource_tags, back_populates="resources")

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer,primary_key=True,index= True, autoincrement=True)
    username        = Column(String(100), nullable=False,unique=True)
    email           = Column(String(255), nullable=False, unique=True)
    password_hash   = Column(String(255), nullable=False)
    role            = Column(Enum(UserRole),default=UserRole.viewer)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
