import unittest
import json
import shutil
from pathlib import Path

# Use app imports
import app.main as main
from app.main import bootstrap_workspace, handle_proposal_submission, apply_current_proposal, handle_verification
from app.state.manager import StateManager
from app.docops.writer import DocWriter
from app.utils.hashing import calculate_content_hash

class TestPhase7(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test_phase7")
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        
        # Monkeypatch main for the test
        main.WORKSPACE_ROOT = str(self.workspace)
        main.writer = DocWriter(str(self.workspace))
        main.state_manager = StateManager(str(self.workspace))

    def test_full_hello_world_loop(self):
        # 1. Bootstrap
        msg = bootstrap_workspace()
        self.assertIn("successfully", msg)
        self.assertTrue((self.workspace / ".agent_ide").exists())

        # 2. @docs command
        status, payload = handle_proposal_submission("@docs:phase create 07 hello-world")
        self.assertEqual(payload["proposal_id"], "doc_phase_07")
        
        # 3. Initial Patch (Failing)
        patch_data = {
            "proposal_id": "p1", "phase_id": "07", "summary": "fail test",
            "files": [
                {"path": "adder.py", "operation": "create", "content": "def add(a,b): return a+b", "post_hash": ""},
                {"path": "tests/test_adder.py", "operation": "create", "content": "def test_add(): from adder import add; assert add(2,2) == 5", "post_hash": ""}
            ]
        }
        patch_data["files"][0]["post_hash"] = calculate_content_hash(patch_data["files"][0]["content"])
        patch_data["files"][1]["post_hash"] = calculate_content_hash(patch_data["files"][1]["content"])
        
        status, payload = handle_proposal_submission(json.dumps(patch_data))
        self.assertIn("Awaiting_Approval", status)

        # 4. Approve & Apply
        from app.proposals.models import ApprovalRecord
        approval = ApprovalRecord(proposal_id="p1", phase_id="07", gate="B", decision="Approved", note="ok")
        main.state_manager.record_approval(approval.model_dump())
        
        apply_msg = apply_current_proposal()
        self.assertIn("Execution report: success", apply_msg)
        self.assertTrue((self.workspace / "adder.py").exists())

        # 5. Verify (FAIL)
        fail_output = "tests/test_adder.py:1: AssertionError\nE       AssertionError: assert 4 == 5"
        verif_msg = handle_verification(fail_output, "FAIL")
        self.assertIn("repair_proposed", verif_msg)

        # 6. Verify Repair Proposal exists
        state = main.state_manager.get_state()
        self.assertEqual(state["current_proposal"]["proposal_id"], "repair_p1")
        self.assertIn("Fixing test expectation", state["current_proposal"]["summary"])

if __name__ == "__main__":
    unittest.main()
