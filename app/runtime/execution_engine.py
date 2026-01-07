import json
from pathlib import Path
from app.patchops.engine import PatchEngine
from app.proposals.patchops import PatchOpsProposal
from app.proposals.models import ProposalType, ProposalState

def execute_patch_proposal(workspace_root: str, proposal_id: str, session_id: str) -> dict:
    from app.state.manager import StateManager
    state_manager = StateManager(workspace_root)
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    
    if not proposal or proposal["proposal_id"] != proposal_id:
        raise ValueError(f"Proposal {proposal_id} is not the current active proposal.")
        
    if proposal["state"] != ProposalState.APPROVED:
        raise ValueError("Proposal must be approved first.")
        
    state_manager.update_proposal_state(ProposalState.EXECUTING)
    
    patch_engine = PatchEngine(workspace_root)
    p_patch = PatchOpsProposal(**proposal["payload"])
    results = patch_engine.apply_proposal(p_patch)
    
    state_manager.update_proposal_state("Awaiting_Verification")
    
    # Run Log
    log_content = f"# Patch Apply Report\nProposal: {proposal_id}\n\n"
    for r in results:
        log_content += f"- {r['operation']} {r['path']}: {r['status']}\n"
    
    log_path = Path(workspace_root) / "documents" / "RUN_LOGS" / f"run_patch_{proposal_id}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(log_content)
        
    return {"status": "success", "stage": "committed", "results": results}
