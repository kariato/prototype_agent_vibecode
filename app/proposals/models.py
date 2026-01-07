"""
app/proposals/models.py

Defines the core Pydantic models for the proposal lifecycle.
Includes enumerations for proposal types and states, as well as the unified proposal envelope.
"""

from enum import Enum
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class ProposalType(str, Enum):
    DOC = "doc"
    PATCH = "patch"

class ProposalState(str, Enum):
    IDLE = "Idle"
    PROPOSAL_CREATED = "Proposal_Created"
    PROPOSAL_VALIDATED = "Proposal_Validated"
    AWAITING_APPROVAL = "Awaiting_Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    EXECUTING = "Executing"
    COMPLETED = "Completed"
    FAILED = "Failed"

class UnifiedProposal(BaseModel):
    """
    The envelope that contains either a DocOps or PatchOps payload.
    This is what is tracked in the project state.
    """
    proposal_id: str
    proposal_type: ProposalType
    phase_id: str
    summary: str
    targets: List[str]
    risk_flags: List[str] = []
    payload: Any  # This will hold DocOpsProposal or PatchOpsProposal
    state: ProposalState = ProposalState.PROPOSAL_CREATED
    validation_messages: List[str] = []
    created_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())

class ApprovalRecord(BaseModel):
    proposal_id: str
    phase_id: str
    gate: str  # "A", "B", "C"
    decision: str  # "Approved", "Rejected"
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    note: Optional[str] = None
