import json
from pathlib import Path
from datetime import datetime

class ProposalArtifactManager:
    def __init__(self, workspace_root: str):
        self.artifacts_dir = Path(workspace_root) / ".agent_ide" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_proposal(self, proposal_id: str, payload: dict) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proposal_{timestamp}_{proposal_id}.json"
        artifact_path = self.artifacts_dir / filename
        
        with open(artifact_path, "w") as f:
            json.dump(payload, f, indent=4)
        
        return artifact_path

    def load_proposal(self, artifact_path: str) -> dict:
        full_path = Path(artifact_path)
        if not full_path.exists():
             # Try absolute path if it was saved relative or vice versa
             pass
        with open(full_path, "r") as f:
            return json.load(f)

    def list_proposals(self) -> list:
        return sorted(list(self.artifacts_dir.glob("proposal_*.json")), reverse=True)
