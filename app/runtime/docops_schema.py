from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from enum import Enum

class DocActionType(str, Enum):
    CREATE_DOC = "CreateDoc"
    REWRITE_DOC = "RewriteDoc"
    APPEND_DOC = "AppendDoc"
    CREATE_PHASE_DOC = "CreatePhaseDoc"

class DocAction(BaseModel):
    action_type: DocActionType
    path: str
    content: str
    mode: Optional[str] = None

class DocOpsPayload(BaseModel):
    actions: List[DocAction]

    @validator("actions")
    def validate_bundle_size(cls, v):
        # We'll use the default of 3 unless we want to inject settings here
        # But for the schema level, 3 is the hard limit from the spec.
        if len(v) > 3:
            raise ValueError("Too many actions in one bundle (max 3)")
        return v
