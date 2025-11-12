"""
Database Schemas for the Resume Builder

Each Pydantic model represents a MongoDB collection (lowercased class name).
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, EmailStr

# Core resume data captured/produced by the app
class ExperienceItem(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None  # Keep as string for flexible formats
    end_date: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    school: str
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    details: Optional[str] = None

class CertificationItem(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None

class Resume(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    target_role: Optional[str] = None

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    preferences: Dict[str, Any] = Field(default_factory=dict)

class Template(BaseModel):
    key: str
    name: str
    style: Literal["clean","minimal","bold","classic","creative"]
    preview_html: Optional[str] = None
