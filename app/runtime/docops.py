"""
app/runtime/docops.py

The runtime module for executing DocOps proposals.
Responsible for validation, gate enforcement (checking APPROVED state), and invoking the DocWriter tool.
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any
from .docops_schema import DocOpsPayload, DocActionType
from app.tools.doc_writer import apply_docops_actions
from app.state.manager import StateManager
from app.proposals.models import ProposalState

def validate_docops_payload(payload: Dict[str, Any], workspace_root: str) -> Tuple[bool, List[str]]:
    """
    Validates a DocOps payload for safety and integrity.
    """
    errors = []
    try:
        data = DocOpsPayload(**payload)
        root = Path(workspace_root).absolute()
        
        for action in data.actions:
            rel_path = action.path
            abs_path = (root / rel_path).absolute()
            
            # 1. Boundary check
            if not str(abs_path).startswith(str(root)):
                errors.append(f"Forbidden path (outside root): {rel_path}")
                continue
                
            # 2. Scope check (DocOps only under documents/)
            if not rel_path.startswith("documents/"):
                errors.append(f"DocOps restricted to documents/: {rel_path}")
                continue

            # 3. Path safety (no .agent_ide, no .env)
            if ".agent_ide" in rel_path or rel_path == ".env":
                errors.append(f"Forbidden directory: {rel_path}")
                continue

            # 4. Action integrity
            if action.action_type in [DocActionType.REWRITE_DOC, DocActionType.APPEND_DOC]:
                if not abs_path.exists():
                    errors.append(f"File not found for {action.action_type}: {rel_path}")

            if action.action_type == DocActionType.CREATE_DOC:
                if abs_path.exists() and not action.mode == "overwrite":
                    errors.append(f"File exists: {rel_path}")

    except Exception as e:
        errors.append(f"Schema validation failed: {str(e)}")

    return (len(errors) == 0, errors)

def execute_docops(workspace_root: str, proposal_id: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Executes an approved DocOps proposal.
    
    1. Fetches the proposal from state.
    2. Enforces Gate A (must be APPROVED).
    3. Validates the payload against DocOpsSchema.
    4. Calls app.tools.doc_writer to perform the write.
    5. Updates the state with the result.
    
    Args:
        workspace_root (str): The active workspace root.
        proposal_id (str): ID of the proposal to execute.
        session_id (str): The active user session.
        
    Returns:
        Dict: An execution report.
    """
    state_manager = StateManager(workspace_root)
    proposal_data = state_manager.get_proposal(proposal_id)
    
    if not proposal_data:
        return {"success": False, "errors": [{"code": "NOT_FOUND", "message": f"Proposal {proposal_id} not found"}]}

    # Enforce Gate A: DocApproval (must be in APPROVED state)
    if proposal_data["state"] != ProposalState.APPROVED:
        return {
            "success": False, 
            "errors": [{"code": "FORBIDDEN", "message": f"DocOps execution requires APPROVED state. Current: {proposal_data['state']}"}]
        }

    # Extract actions from payload
    payload = proposal_data.get("payload", {})
    actions = payload.get("actions", [])
    
    # Final validation before write
    ok, errors = validate_docops_payload(payload, workspace_root)
    if not ok:
        return {"success": False, "errors": [{"code": "VALIDATION_FAILED", "message": e} for e in errors]}

    # Call the tool (side-effect)
    report = apply_docops_actions(workspace_root, proposal_id, actions)
    
    if report["success"]:
        # Update proposal state to EXECUTED
        state_manager.record_doc_write(proposal_id, report["files_written"])
        
    return report
