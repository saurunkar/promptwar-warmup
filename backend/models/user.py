from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class LearningStyle(str, Enum):
    VISUAL = "visual"
    TEXTUAL = "textual"
    MIXED = "mixed"

class Pace(str, Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"

class KnowledgeGraph(BaseModel):
    # Mapping of concept names to proficiency scores (0.0 to 1.0)
    concepts: Dict[str, float] = Field(default_factory=dict)

class UserProfile(BaseModel):
    user_id: str
    learning_style: LearningStyle = LearningStyle.MIXED
    pace: Pace = Pace.MEDIUM
    knowledge_graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    history: List[Dict] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)

class InteractionUpdate(BaseModel):
    user_id: str
    concept: str
    is_correct: bool
    response_time_ms: int
