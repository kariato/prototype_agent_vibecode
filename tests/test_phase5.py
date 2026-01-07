import unittest
import json
import shutil
from pathlib import Path

from app.proposals.patchops import PatchOpsProposal, PatchAction, PatchActionType
from app.patchops.engine import PatchEngine
from app.state.manager import StateManager
from app.utils.hashing import calculate_content_hash

class TestPhase5(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test_phase5")
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        (self.workspace / "documents" / "RUN_LOGS").mkdir(parents=True)
        
        self.engine = PatchEngine(str(self.workspace))
        self.manager = StateManager(str(self.workspace))

    def test_atomic_apply_success(self):
        # 1. Create a file
        p1 = PatchOpsProposal(
            proposal_id="p1", phase_id="05", summary="s",
            files=[PatchAction(path="test.py", operation=PatchActionType.CREATE, content="print(1)", post_hash=calculate_content_hash("print(1)"))]
        )
        self.engine.apply_proposal(p1)
        self.assertTrue((self.workspace / "test.py").exists())

        # 2. Update it
        old_hash = calculate_content_hash("print(1)")
        p2 = PatchOpsProposal(
            proposal_id="p2", phase_id="05", summary="s",
            files=[PatchAction(path="test.py", operation=PatchActionType.UPDATE, content="print(2)", pre_hash=old_hash, post_hash=calculate_content_hash("print(2)"))]
        )
        self.engine.apply_proposal(p2)
        with open(self.workspace / "test.py", "r") as f:
            self.assertEqual(f.read(), "print(2)")

    def test_atomic_apply_hash_failure(self):
        # Create initial file
        (self.workspace / "target.py").write_text("v1")
        
        # Propose update with WRONG pre_hash
        p = PatchOpsProposal(
            proposal_id="p_fail", phase_id="05", summary="s",
            files=[
                PatchAction(path="target.py", operation=PatchActionType.UPDATE, content="v2", pre_hash="wrong", post_hash="dummy"),
                PatchAction(path="new.py", operation=PatchActionType.CREATE, content="v2", post_hash="dummy")
            ]
        )
        
        with self.assertRaises(ValueError):
            self.engine.apply_proposal(p)
            
        # Verify NO partial apply (new.py should NOT exist)
        self.assertFalse((self.workspace / "new.py").exists())
        self.assertEqual((self.workspace / "target.py").read_text(), "v1")

    def test_verification_flow(self):
        # Setup proposal in state
        proposal_dict = {
            "proposal_id": "p_verif",
            "state": "Awaiting_Verification",
            "proposal_type": "patch",
            "summary": "s"
        }
        self.manager.submit_proposal(proposal_dict)
        
        # Record PASS
        self.manager.record_verification("p_verif", "tests ok", "PASS")
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], "Completed")
        
        # Record FAIL
        self.manager.submit_proposal(proposal_dict) # reset
        self.manager.record_verification("p_verif", "tests failed", "FAIL")
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["state"], "Failed")

if __name__ == "__main__":
    unittest.main()
