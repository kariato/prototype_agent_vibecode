"""
app/runtime/verification.py

Handles the verification stage of the proposal lifecycle.
Records test results and triggers automated repairs if verification fails.
"""

from pathlib import Path
from app.state.manager import StateManager
from app.orchestration.repair_lane import RepairLane

def record_verification(workspace_root: str, proposal_id: str, session_id: str, passed: bool, raw_output: str) -> dict:
    """
    Records the outcome of a verification run (e.g., tests passed/failed).
    If failed, it invokes the RepairLane to propose a fix.
    
    Args:
        workspace_root (str): Workspace root path.
        proposal_id (str): ID of the proposal being verified.
        session_id (str): Active session ID.
        passed (bool): Whether the verification passed.
        raw_output (str): Stdout/stderr from the verification command.
        
    Returns:
        dict: Status object (e.g., "verified_pass" or "repair_proposed").
    """
    state_manager = StateManager(workspace_root)
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    
    if not proposal or proposal["proposal_id"] != proposal_id:
        raise ValueError(f"Proposal {proposal_id} is not current.")
        
    result_str = "PASS" if passed else "FAIL"
    state_manager.record_verification(proposal_id, raw_output, result_str)
    
    if not passed:
        # Repair Log
        log_path = Path(workspace_root) / "documents" / "RUN_LOGS" / f"run_verification_{proposal_id}_fail.md"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            f.write(f"# Verification FAILED\nProposal: {proposal_id}\n\n## Output\n```\n{raw_output}\n```")
            
        # Generate Repair
        repair_lane = RepairLane(workspace_root)
        repair_proposal = repair_lane.generate_repair(proposal_id, raw_output)
        
        # Submit Repair
        from app.proposals.models import UnifiedProposal, ProposalType, ProposalState
        # We need to bridge to handle_proposal_submission logic here or just submit via state manager
        # Using state manager directly for now to avoid circular imports
        p_repair = UnifiedProposal(
            proposal_id=repair_proposal.proposal_id,
            proposal_type=ProposalType.PATCH,
            phase_id=proposal.get("phase_id", "repair"),
            summary=repair_proposal.summary or f"Repair for {proposal_id}",
            payload=repair_proposal.model_dump(),
            state=ProposalState.AWAITING_APPROVAL,
            targets=[f.path for f in repair_proposal.files]
        )
        state_manager.submit_proposal(p_repair.model_dump())
        
        return {"status": "repair_proposed", "repair_id": p_repair.proposal_id}

    return {"status": "verified_pass"}
