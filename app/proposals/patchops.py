"""
app/proposals/patchops.py

Defines the schema for Code Implementation proposals (PatchOps).
Includes the atomic actions (create/update/delete) and hash validation fields.
"""

from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class PatchActionType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class PatchAction(BaseModel):
    path: str
    operation: PatchActionType
    pre_hash: Optional[str] = None
    post_hash: Optional[str] = None
    content: Optional[str] = None

class PatchOpsProposal(BaseModel):
    """
    A proposal to mutate the codebase.
    Contains a list of ordered atomic file operations.
    """
    version: int = 1
    proposal_id: str
    phase_id: str
    summary: str
    files: List[PatchAction]
