import sys
import os
import unittest
import json
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from proposals.models import UnifiedProposal, ProposalType, ProposalState, ApprovalRecord
from state.manager import StateManager
from docops.writer import DocWriter

class TestPhase3(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test_phase3")
        if self.workspace.exists():
            import shutil
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        (self.workspace / "documents").mkdir()
        (self.workspace / ".agent_ide").mkdir()
        
        self.state_path = self.workspace / ".agent_ide" / "project_state.json"
        with open(self.state_path, "w") as f:
            json.dump({"schema_version": 1}, f)

        self.manager = StateManager(str(self.workspace))
        self.writer = DocWriter(str(self.workspace))

    def test_unified_workflow_doc(self):
        # 1. Submit Proposal
        payload = {
            "proposal_id": "p_doc_1",
            "actions": [{"type": "CreateDoc", "path": "documents/hello.md", "content": "world"}]
        }
        proposal = UnifiedProposal(
            proposal_id="p_doc_1",
            proposal_type=ProposalType.DOC,
            phase_id="03",
            summary="Create hello file",
            targets=["documents/hello.md"],
            payload=payload
        )
        self.manager.submit_proposal(proposal.dict())
        
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], ProposalState.PROPOSAL_CREATED)

        # 2. Transition to Awaiting Approval
        self.manager.update_proposal_state(ProposalState.AWAITING_APPROVAL)
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], ProposalState.AWAITING_APPROVAL)

        # 3. Approve
        approval = ApprovalRecord(
            proposal_id="p_doc_1",
            phase_id="03",
            gate="A",
            decision="Approved"
        )
        self.manager.record_approval(approval.dict())
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], ProposalState.APPROVED)

        # 4. Execute (simulated by caller logic in main.py)
        # We verify state manager updates after write
        self.manager.record_doc_write("p_doc_1")
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], ProposalState.COMPLETED)

    def test_unified_workflow_rejection(self):
        proposal = UnifiedProposal(
            proposal_id="p_rej_1",
            proposal_type=ProposalType.PATCH,
            phase_id="03",
            summary="Patch",
            targets=["app/main.py"],
            payload={}
        )
        self.manager.submit_proposal(proposal.dict())
        
        approval = ApprovalRecord(
            proposal_id="p_rej_1",
            phase_id="03",
            gate="B",
            decision="Rejected",
            note="Too risky"
        )
        self.manager.record_approval(approval.dict())
        
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], ProposalState.REJECTED)
        self.assertEqual(state["approvals"][0]["note"], "Too risky")

if __name__ == "__main__":
    unittest.main()
