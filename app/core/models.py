from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    technical = "technical"
    business = "business"
    scoring = "scoring"
    format = "format"
    other = "other"


class SourceSpan(BaseModel):
    paragraph_id: Optional[str] = None
    quote: Optional[str] = None


class RequirementItem(BaseModel):
    req_id: str
    title: str
    content: str
    requirement_type: RequirementType
    priority: int
    mandatory: bool = False
    source: SourceSpan


class OutlineSection(BaseModel):
    section_id: str
    title: str
    objective: str
    related_requirements: List[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    evidence_id: str
    source_name: str
    snippet: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChapterDraft(BaseModel):
    section_id: str
    title: str
    content: str
    evidence_ids: List[str] = Field(default_factory=list)


class ResponseMatrixRow(BaseModel):
    req_id: str
    requirement_summary: str
    response_section: str
    response_text: str
    evidence_ids: List[str] = Field(default_factory=list)
