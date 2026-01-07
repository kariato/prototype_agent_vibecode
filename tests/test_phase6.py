import unittest
import json
import shutil
from pathlib import Path

from app.orchestration.runtime import GraphRuntime
from app.proposals.artifacts import ProposalArtifactManager
from app.runtime.events import EventImpact

class TestPhase6(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test_phase6")
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        (self.workspace / "documents" / "RUN_LOGS").mkdir(parents=True)
        
        self.runtime = GraphRuntime(str(self.workspace))
        self.artifact_manager = ProposalArtifactManager(str(self.workspace))

    def test_checkpoint_and_resume(self):
        state = {
            "session_id": "test_sess",
            "workspace_root": str(self.workspace),
            "lane": "patch",
            "intent": "fix bug",
            "events": [],
            "errors": []
        }
        
        # Save checkpoint
        checkpoint_id = self.runtime._save_checkpoint(state, "await_approval")
        self.assertIn("chk_", checkpoint_id)
        
        # Verify project state update
        proj_state = self.runtime.state_manager.get_state()
        self.assertEqual(proj_state["runtime"]["resume_node"], "await_approval")
        self.assertEqual(proj_state["runtime"]["last_checkpoint_id"], checkpoint_id)
        
        # Resume
        restored_state = self.runtime.resume(checkpoint_id)
        self.assertEqual(restored_state["session_id"], "test_sess")

    def test_proposal_artifact_lifecycle(self):
        payload = {"proposal_id": "p1", "actions": []}
        path = self.artifact_manager.save_proposal("p1", payload)
        self.assertTrue(path.exists())
        
        loaded = self.artifact_manager.load_proposal(path)
        self.assertEqual(loaded["proposal_id"], "p1")
        
        proposals = self.artifact_manager.list_proposals()
        self.assertEqual(len(proposals), 1)

    def test_event_emission(self):
        event = self.runtime.emit_event("PROPOSAL_CREATED", {"id": "p1"})
        self.assertEqual(event["type"], "PROPOSAL_CREATED")
        self.assertIn("timestamp", event)
        self.assertEqual(event["impact"], EventImpact.INFO)
        self.assertEqual(event["session_id"], "default_session")

if __name__ == "__main__":
    unittest.main()
