import unittest
import json
import shutil
from pathlib import Path

from app.docops.protocol import parse_docops
from app.docops.writer import DocWriter
from app.state.manager import StateManager
from app.proposals.models import ProposalState, ProposalType

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test")
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        (self.workspace / "documents").mkdir()
        
        self.writer = DocWriter(str(self.workspace))
        self.manager = StateManager(str(self.workspace))

    def test_protocol_validation(self):
        # Valid proposal
        proposal_json = json.dumps({
            "proposal_id": "p1",
            "summary": "test",
            "version": 1,
            "actions": [{"type": "CreateDoc", "path": "documents/test.md", "content": "hello"}]
        })
        proposal = parse_docops(proposal_json)
        self.assertEqual(proposal.proposal_id, "p1")

        # Invalid path
        bad_json = json.dumps({
            "proposal_id": "p2",
            "summary": "bad path",
            "actions": [{"type": "CreateDoc", "path": "outside.md", "content": "bad"}]
        })
        with self.assertRaises(ValueError):
            parse_docops(bad_json)

        # > 3 actions
        too_many_json = json.dumps({
            "proposal_id": "p3",
            "summary": "too many",
            "actions": [{"type": "CreateDoc", "path": f"documents/{i}.md", "content": "x"} for i in range(4)]
        })
        with self.assertRaises(ValueError):
            parse_docops(too_many_json)

    def test_doc_writing_and_archival(self):
        # 1. CreateDoc
        proposal = parse_docops(json.dumps({
            "proposal_id": "p1", "summary": "s",
            "actions": [{"type": "CreateDoc", "path": "documents/doc1.md", "content": "v1"}]
        }))
        action = proposal.actions[0]
        self.writer.execute_action(action)
        self.assertTrue((self.workspace / "documents" / "doc1.md").exists())

        # 2. CreateDoc fails if exists
        with self.assertRaises(FileExistsError):
            self.writer.execute_action(action)

        # 3. RewriteDoc archives and overwrites
        rewrite_proposal = parse_docops(json.dumps({
            "proposal_id": "p2", "summary": "s",
            "actions": [{"type": "RewriteDoc", "path": "documents/doc1.md", "content": "v2", "archive": True}]
        }))
        rewrite = rewrite_proposal.actions[0]
        self.writer.execute_action(rewrite)
        
        with open(self.workspace / "documents" / "doc1.md", "r") as f:
            self.assertEqual(f.read(), "v2")
        
        # Check archive
        archives = list((self.workspace / "documents" / "_archive").glob("**/*.md"))
        self.assertEqual(len(archives), 1)
        with open(archives[0], "r") as f:
            self.assertEqual(f.read(), "v1")

    def test_state_updates(self):
        proposal_dict = {
            "proposal_id": "prop_123",
            "proposal_type": ProposalType.DOC,
            "phase_id": "02",
            "summary": "test",
            "state": ProposalState.AWAITING_APPROVAL,
            "targets": ["documents/test.md"]
        }
        self.manager.submit_proposal(proposal_dict)
        state = self.manager.get_state()
        self.assertEqual(state["current_proposal"]["proposal_id"], "prop_123")
        self.assertEqual(state["current_proposal"]["state"], ProposalState.AWAITING_APPROVAL)

        self.manager.record_doc_write("prop_123")
        state = self.manager.get_state()
        self.assertEqual(state["documents"]["last_write_proposal_id"], "prop_123")
        self.assertEqual(state["current_proposal"]["state"], "Completed")

if __name__ == "__main__":
    unittest.main()
