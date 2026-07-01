from pydantic import BaseModel
from typing import Optional, Literal


class FHx_Object(BaseModel):
    reasoning: str
    FamilyMember: Optional[str] = None
    AgeofOnset: Optional[int] = None
    Observation: Optional[str] = None
    SideoftheFamily: Optional[Literal["Maternal", "Paternal", "Unknown"]] = None
    LivingStatus: Optional[Literal["Alive", "Dead", "Unknown"]] = None
    Age: Optional[int] = None
    AgeofDeath: Optional[int] = None
    CauseofDeath: Optional[bool] = None
    CUI: Optional[str] = None
    Negated: Optional[bool] = None


class FamilyHistory(BaseModel):
    full_history: list[FHx_Object]


JSON_SCHEMA = FamilyHistory.model_json_schema()