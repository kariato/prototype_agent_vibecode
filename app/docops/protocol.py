import json
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
import os

class ActionType(str, Enum):
    CREATE_DOC = "CreateDoc"
    REWRITE_DOC = "RewriteDoc"
    APPEND_LOG = "AppendLog"
    CREATE_PHASE_DOC = "CreatePhaseDoc"
    CREATE_ADR = "CreateADR"

class DocOpsAction(BaseModel):
    type: ActionType
    path: Optional[str] = None
    content: str
    archive: Optional[bool] = None
    phase_id: Optional[str] = None
    adr_id: Optional[str] = None
    slug: Optional[str] = None

    @validator("path")
    def validate_path(cls, v, values):
        if "type" in values and values["type"] in [ActionType.CREATE_DOC, ActionType.REWRITE_DOC, ActionType.APPEND_LOG]:
            if not v:
                raise ValueError("path is required for this action type")
            if not v.startswith("documents/"):
                raise ValueError("path must start with 'documents/'")
            if ".." in v or v.startswith("/") or ":" in v:
                raise ValueError("path must be relative and within 'documents/'")
        return v

    @validator("archive")
    def validate_archive(cls, v, values):
        if "type" in values and values["type"] == ActionType.REWRITE_DOC:
            if v is not True:
                raise ValueError("archive must be true for RewriteDoc")
        return v

class DocOpsProposal(BaseModel):
    version: int = Field(default=1)
    proposal_id: str
    summary: str
    actions: List[DocOpsAction]

    @validator("version")
    def validate_version(cls, v):
        if v != 1:
            raise ValueError("version must be 1")
        return v

    @validator("actions")
    def validate_actions_count(cls, v):
        if not (1 <= len(v) <= 3):
            raise ValueError("actions count must be between 1 and 3")
        return v

def parse_docops(json_str: str) -> DocOpsProposal:
    try:
        data = json.loads(json_str)
        return DocOpsProposal(**data)
    except Exception as e:
        raise ValueError(f"Invalid DocOps proposal: {str(e)}")

def expand_action(action: DocOpsAction) -> DocOpsAction:
    if action.type == ActionType.CREATE_PHASE_DOC:
        if not action.phase_id or not action.slug:
            raise ValueError("phase_id and slug are required for CreatePhaseDoc")
        new_path = f"documents/PHASES/phase_{action.phase_id}_{action.slug}.md"
        return DocOpsAction(type=ActionType.CREATE_DOC, path=new_path, content=action.content)
    
    if action.type == ActionType.CREATE_ADR:
        if not action.adr_id or not action.slug:
            raise ValueError("adr_id and slug are required for CreateADR")
        new_path = f"documents/DECISIONS/ADR_{action.adr_id}_{action.slug}.md"
        return DocOpsAction(type=ActionType.CREATE_DOC, path=new_path, content=action.content)
    
    return action
