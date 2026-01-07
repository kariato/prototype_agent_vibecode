import unittest
import json
import os
import shutil
from pathlib import Path
from app.state.manager import StateManager
from app.runtime.execution_engine import execute_patch_proposal
from app.runtime.verification import record_verification
from app.proposals.models import ProposalState

class TestAcceptanceSmoke(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_smoke_test")
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        
        # Initialize state manager
        self.state_manager = StateManager(str(self.workspace))
        
        # Scaffold
        from app.tools.scaffold_phase07 import scaffold_phase07_workspace
        scaffold_phase07_workspace(str(self.workspace))

    def tearDown(self):
        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_full_repair_loop(self):
        from app.utils.hashing import calculate_content_hash
        pre_content = "def add(a, b):\n    return a + b\n"
        post_content = "def add(a, b):\n    return a + b + 1\n"
        
        buggy_patch = {
            "proposal_id": "test_bug",
            "phase_id": "10",
            "summary": "Introduce bug",
            "files": [{
                "path": "adder.py",
                "operation": "update",
                "content": post_content,
                "pre_hash": calculate_content_hash(pre_content),
                "post_hash": calculate_content_hash(post_content)
            }]
        }
        
        # Submit (mocked UI behavior)
        from app.main import handle_proposal_submission
        # Temporarily mock internal workspace root if needed, but here we'll just use the APIs
        
        # Actually, let's use the runtime APIs directly to avoid Gradio dependencies
        from app.proposals.models import UnifiedProposal, ProposalType
        p = UnifiedProposal(
            proposal_id="test_bug",
            proposal_type=ProposalType.PATCH,
            phase_id="10",
            summary="Introduce bug",
            payload=buggy_patch,
            state=ProposalState.APPROVED, # Pre-approve for test
            targets=["adder.py"]
        )
        self.state_manager.submit_proposal(p.model_dump())
        
        # 2. Execute
        results = execute_patch_proposal(str(self.workspace), "test_bug", "smoke_session")
        self.assertEqual(results["stage"], "committed")
        
        # 3. Verify FAIL
        v_results = record_verification(str(self.workspace), "test_bug", "smoke_session", False, "Failing test output")
        self.assertEqual(v_results["status"], "repair_proposed")
        
        # 4. Confirm repair proposal exists
        state = self.state_manager.get_state()
        repair_proposal = state["current_proposal"]
        self.assertTrue(repair_proposal["proposal_id"].startswith("repair_"))
        
        # 5. Approve & Execute Repair (Mocked)
        self.state_manager.update_proposal_state(ProposalState.APPROVED)
        results_2 = execute_patch_proposal(str(self.workspace), repair_proposal["proposal_id"], "smoke_session")
        self.assertEqual(results_2["stage"], "committed")
        
        # 6. Verify PASS
        v_results_2 = record_verification(str(self.workspace), repair_proposal["proposal_id"], "smoke_session", True, "Passing tests")
        self.assertEqual(v_results_2["status"], "verified_pass")

if __name__ == "__main__":
    unittest.main()
