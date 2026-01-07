import json
from pathlib import Path
from datetime import datetime

class StateManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).absolute()
        self.state_path = self.workspace_root / ".agent_ide" / "project_state.json"

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            raise FileNotFoundError(f"Project state file not found: {self.state_path}")
        with open(self.state_path, "r") as f:
            return json.load(f)

    def _save_state(self, state: dict):
        state["updated_at"] = datetime.utcnow().timestamp() # Simplified for now
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=4)

    def record_approval(self, phase_id: str, gate: str, note: str):
        state = self._load_state()
        state.setdefault("approvals", []).append({
            "phase_id": phase_id,
            "gate": gate,
            "timestamp": datetime.utcnow().timestamp(),
            "note": note
        })
        self._save_state(state)

    def update_phase_status(self, phase_id: str, status: str):
        state = self._load_state()
        state.setdefault("phases", {}).setdefault("phase_status", {})[phase_id] = status
        self._save_state(state)

    def record_doc_write(self, proposal_id: str):
        state = self._load_state()
        state.setdefault("documents", {})["last_write_at"] = datetime.utcnow().timestamp()
        state["documents"]["last_write_proposal_id"] = proposal_id
        state["documents"]["pending_status"] = "written"
        self._save_state(state)

    def propose_docops(self, proposal_id: str, targets: list[str], actions_count: int):
        state = self._load_state()
        state.setdefault("documents", {})
        state["documents"]["pending_proposal_id"] = proposal_id
        state["documents"]["pending_created_at"] = datetime.utcnow().timestamp()
        state["documents"]["pending_targets"] = targets
        state["documents"]["pending_actions_count"] = actions_count
        state["documents"]["pending_status"] = "proposed"
        self._save_state(state)
