import unittest
from pathlib import Path

from app.proposals.patchops import PatchOpsProposal, PatchAction, PatchActionType
from app.utils.hashing import calculate_content_hash
from app.utils.diffing import generate_unified_diff

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test_phase4")
        if self.workspace.exists():
            import shutil
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)

    def test_hashing_and_diff(self):
        old_content = "line 1\nline 2\n"
        new_content = "line 1\nline 2 changed\n"
        
        old_hash = calculate_content_hash(old_content)
        new_hash = calculate_content_hash(new_content)
        
        self.assertNotEqual(old_hash, new_hash)
        
        diff = generate_unified_diff(old_content, new_content, "test.py")
        self.assertIn("-line 2", diff)
        self.assertIn("+line 2 changed", diff)

    def test_patch_proposal_validation_schema(self):
        proposal_data = {
            "proposal_id": "p1",
            "phase_id": "04",
            "summary": "Fix",
            "files": [
                {
                    "path": "app/main.py",
                    "operation": "update",
                    "pre_hash": "abc",
                    "post_hash": "def",
                    "content": "new content"
                }
            ]
        }
        proposal = PatchOpsProposal(**proposal_data)
        self.assertEqual(proposal.files[0].operation, PatchActionType.UPDATE)

if __name__ == "__main__":
    unittest.main()
