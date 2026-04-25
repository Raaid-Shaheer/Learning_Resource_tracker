from sqlalchemy import Column, Integer, String, Text, Enum
from .database import Base
import enum

# --- Enums ---
class Department(str, enum.Enum):
    CS = "CS"
    ECE = "ECE"
    OTHER = "Other"

class ResourceType(str, enum.Enum):
    VIDEO = "Video"
    PLAYLIST = "Playlist"
    WEBSITE = "Website"
    GITHUB = "Github Repo"

# --- Database Model ---
class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    link = Column(String(500), nullable=False)
    department = Column(Enum(Department), nullable=False)    
    resource_type = Column(Enum(ResourceType), nullable=False)
    description = Column(Text)