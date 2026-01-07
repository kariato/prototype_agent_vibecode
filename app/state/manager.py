import json
from pathlib import Path
from datetime import datetime

from app.config.settings import get_settings

class StateManager:
    def __init__(self, workspace_root: str):
        self.settings = get_settings()
        self.workspace_root = Path(workspace_root).absolute()
        self.state_path = self.workspace_root / self.settings.PROJECT_STATE_FILENAME
        # Maintain backward compatibility if needed, though settings should be authoritative
        if not self.state_path.exists():
             # Fallback to .agent_ide/project_state.json if filename is different
             self.state_path = self.workspace_root / ".agent_ide" / "project_state.json"

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"schema_version": 1}
        with open(self.state_path, "r") as f:
            return json.load(f)

    def _save_state(self, state: dict):
        state["updated_at"] = datetime.now().timestamp()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=4)

    def get_state(self) -> dict:
        return self._load_state()

    def submit_proposal(self, proposal_dict: dict):
        state = self._load_state()
        state["current_proposal"] = proposal_dict
        self._save_state(state)

    def update_proposal_state(self, state_str: str, validation_messages: list = None):
        state = self._load_state()
        if "current_proposal" in state:
            state["current_proposal"]["state"] = state_str
            if validation_messages is not None:
                state["current_proposal"]["validation_messages"] = validation_messages
            self._save_state(state)

    def record_approval(self, approval_dict: dict):
        state = self._load_state()
        state.setdefault("approvals", []).append(approval_dict)
        # Update current proposal state if it matches
        if "current_proposal" in state and state["current_proposal"]["proposal_id"] == approval_dict["proposal_id"]:
            state["current_proposal"]["state"] = "Approved" if approval_dict["decision"] == "Approved" else "Rejected"
        self._save_state(state)

    def update_phase_status(self, phase_id: str, status: str):
        state = self._load_state()
        state.setdefault("phases", {}).setdefault("phase_status", {})[phase_id] = status
        self._save_state(state)

    def record_doc_write(self, proposal_id: str):
        state = self._load_state()
        state.setdefault("documents", {})["last_write_at"] = datetime.now().timestamp()
        state["documents"]["last_write_proposal_id"] = proposal_id
        if "current_proposal" in state and state["current_proposal"]["proposal_id"] == proposal_id:
            state["current_proposal"]["state"] = "Completed"
        self._save_state(state)

    def record_verification(self, proposal_id: str, output: str, result: str):
        state = self._load_state()
        if "current_proposal" in state and state["current_proposal"]["proposal_id"] == proposal_id:
            state["current_proposal"]["verification_output"] = output
            state["current_proposal"]["state"] = "Completed" if result == "PASS" else "Failed"
            
            # Log verification
            state.setdefault("verifications", []).append({
                "proposal_id": proposal_id,
                "result": result,
                "timestamp": datetime.now().timestamp(),
                "output_snippet": output[:200]
            })
        self._save_state(state)
