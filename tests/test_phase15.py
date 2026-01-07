import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from app.runtime.docops import execute_docops
from app.state.manager import StateManager
from app.proposals.models import ProposalType, ProposalState

def test_docops_alignment():
    workspace_root = "/tmp/prot_agent_verification_p15"
    if os.path.exists(workspace_root):
        shutil.rmtree(workspace_root)
    os.makedirs(workspace_root)
    
    # Bootstrap
    dirs = ["documents/PHASES", "documents/DECISIONS", "documents/RUN_LOGS", "documents/_archive", ".agent_ide"]
    for d in dirs:
        (Path(workspace_root) / d).mkdir(parents=True, exist_ok=True)
    
    outline_path = Path(workspace_root) / "documents" / "PROJECT_OUTLINE.md"
    with open(outline_path, "w") as f:
        f.write("# Project Outline V1")
    
    state_manager = StateManager(workspace_root)
    
    # Submit Rewrite Proposal
    proposal_data = {
        "proposal_id": "prop_rewrite_outline",
        "proposal_type": "docops",
        "summary": "Updating outline",
        "actions": [
            {
                "action_type": "RewriteDoc",
                "path": "documents/PROJECT_OUTLINE.md",
                "content": "# Project Outline V2"
            }
        ]
    }
    
    # Manual submission to state manager for test
    proposal = {
        "proposal_id": proposal_data["proposal_id"],
        "proposal_type": "docops",
        "phase_id": "01",
        "summary": proposal_data["summary"],
        "state": "awaiting_approval",
        "targets": ["documents/PROJECT_OUTLINE.md"],
        "payload": proposal_data,
        "created_at": datetime.now().isoformat()
    }
    state_manager.submit_proposal(proposal)
    
    # 1. Attempt execute without approval (should fail)
    report = execute_docops(workspace_root, proposal["proposal_id"])
    assert report["success"] is False
    assert "FORBIDDEN" in report["errors"][0]["code"]
    print("Test Passed: Refused non-approved DocOps execution.")
    
    # 2. Approve
    state_manager.record_approval({
        "proposal_id": proposal["proposal_id"],
        "decision": "Approved",
        "note": "Let's go"
    })
    
    # 3. Execute
    report = execute_docops(workspace_root, proposal["proposal_id"])
    assert report["success"] is True
    assert "documents/PROJECT_OUTLINE.md" in report["files_written"]
    assert len(report["files_archived"]) == 1
    archive_path = report["files_archived"][0]
    assert archive_path.startswith("documents/_archive/documents__PROJECT_OUTLINE.md__")
    
    # 4. Verify content
    with open(outline_path, "r") as f:
        assert f.read() == "# Project Outline V2"
        
    abs_archive_path = Path(workspace_root) / archive_path
    assert abs_archive_path.exists()
    with open(abs_archive_path, "r") as f:
        assert f.read() == "# Project Outline V1"
        
    print(f"Test Passed: DocOps executed successfully with archiving: {archive_path}")

if __name__ == "__main__":
    test_docops_alignment()
