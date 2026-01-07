import sys
import os
import unittest
import json
from pathlib import Path

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from docops.protocol import parse_docops, expand_action, ActionType
from docops.writer import DocWriter
from state.manager import StateManager

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.workspace = Path("/tmp/agent_ide_test")
        if self.workspace.exists():
            import shutil
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True)
        (self.workspace / "documents").mkdir()
        (self.workspace / ".agent_ide").mkdir()
        
        # Init project state
        self.state_path = self.workspace / ".agent_ide" / "project_state.json"
        with open(self.state_path, "w") as f:
            json.dump({"schema_version": 1, "phases": {"current_phase": 1}}, f)

        self.writer = DocWriter(str(self.workspace))
        self.manager = StateManager(str(self.workspace))

    def test_protocol_validation(self):
        # Valid proposal
        proposal_json = json.dumps({
            "proposal_id": "p1",
            "summary": "test",
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
        action = parse_docops(json.dumps({
            "proposal_id": "p1", "summary": "s",
            "actions": [{"type": "CreateDoc", "path": "documents/doc1.md", "content": "v1"}]
        })).actions[0]
        self.writer.execute_action(action)
        self.assertTrue((self.workspace / "documents" / "doc1.md").exists())

        # 2. CreateDoc fails if exists
        with self.assertRaises(FileExistsError):
            self.writer.execute_action(action)

        # 3. RewriteDoc archives and overwrites
        rewrite = parse_docops(json.dumps({
            "proposal_id": "p2", "summary": "s",
            "actions": [{"type": "RewriteDoc", "path": "documents/doc1.md", "content": "v2", "archive": True}]
        })).actions[0]
        self.writer.execute_action(rewrite)
        
        with open(self.workspace / "documents" / "doc1.md", "r") as f:
            self.assertEqual(f.read(), "v2")
        
        # Check archive
        archives = list((self.workspace / "documents" / "_archive").glob("**/*.md"))
        self.assertEqual(len(archives), 1)
        with open(archives[0], "r") as f:
            self.assertEqual(f.read(), "v1")

    def test_state_updates(self):
        self.manager.propose_docops("prop_123", ["documents/test.md"], 1)
        state = self.manager._load_state()
        self.assertEqual(state["documents"]["pending_proposal_id"], "prop_123")
        self.assertEqual(state["documents"]["pending_status"], "proposed")

        self.manager.record_doc_write("prop_123")
        state = self.manager._load_state()
        self.assertEqual(state["documents"]["last_write_proposal_id"], "prop_123")
        self.assertEqual(state["documents"]["pending_status"], "written")

if __name__ == "__main__":
    unittest.main()
