import unittest
import shutil
from pathlib import Path

from app.patchops.engine import PatchEngine
from app.proposals.patchops import PatchOpsProposal, PatchAction, PatchActionType
from app.utils.hashing import calculate_content_hash

class TestPhase8(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test_phase8")
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        self.engine = PatchEngine(str(self.workspace))

    def test_transactional_rollback_on_hash_mismatch(self):
        # Create a file first
        f1 = self.workspace / "f1.txt"
        with open(f1, "w") as f:
            f.write("original content")
        h1 = calculate_content_hash("original content")
        
        # Proposal with two updates: 
        # 1. Valid update
        # 2. Invalid update (post-hash mismatch)
        proposal = PatchOpsProposal(
            proposal_id="tx_123",
            phase_id="08",
            summary="test transaction",
            files=[
                PatchAction(
                    path="f1.txt",
                    operation=PatchActionType.UPDATE,
                    pre_hash=h1,
                    post_hash=calculate_content_hash("new content"),
                    content="new content"
                ),
                PatchAction(
                    path="f2.txt",
                    operation=PatchActionType.CREATE,
                    pre_hash=None,
                    post_hash="wrong_hash", # Trigger failure
                    content="created content"
                )
            ]
        )
        
        try:
            self.engine.apply_proposal(proposal)
        except ValueError as e:
            self.assertIn("Post-hash integrity check failed", str(e))
            
        # Verify ROLLBACK
        # f1.txt should be back to original
        with open(f1, "r") as f:
            self.assertEqual(f.read(), "original content")
            
        # f2.txt should NOT exist
        self.assertFalse((self.workspace / "f2.txt").exists())
        
        # Backups and temps should be cleaned up (best effort in rollback block)
        leftovers = [f for f in self.workspace.glob("**/*") if ".tmp." in f.name or ".bak." in f.name]
        self.assertEqual(len(leftovers), 0)

    def test_delete_staging_and_rollback(self):
        f1 = self.workspace / "f1.txt"
        with open(f1, "w") as f:
            f.write("delete me")
        h1 = calculate_content_hash("delete me")
        
        # Proposal: delete f1, then fail on something else
        proposal = PatchOpsProposal(
            proposal_id="tx_del",
            phase_id="08",
            summary="test delete rollback",
            files=[
                PatchAction(
                    path="f1.txt",
                    operation=PatchActionType.DELETE,
                    pre_hash=h1,
                    post_hash=None,
                    content=None
                ),
                PatchAction(
                    path="fail.txt",
                    operation=PatchActionType.CREATE,
                    pre_hash=None,
                    post_hash="wrong",
                    content="fail"
                )
            ]
        )
        
        try:
            self.engine.apply_proposal(proposal)
        except:
            pass
            
        # Verify f1.txt is restored
        self.assertTrue(f1.exists())
        with open(f1, "r") as f:
            self.assertEqual(f.read(), "delete me")

if __name__ == "__main__":
    unittest.main()
