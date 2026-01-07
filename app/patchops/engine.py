import os
from pathlib import Path
from typing import List, Dict
from proposals.patchops import PatchOpsProposal, PatchActionType
from utils.hashing import calculate_file_hash

class PatchEngine:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).absolute()

    def _get_abs_path(self, rel_path: str) -> Path:
        abs_path = (self.workspace_root / rel_path).absolute()
        if not str(abs_path).startswith(str(self.workspace_root)):
            raise ValueError(f"Forbidden path: {rel_path}. Path must be within workspace root.")
        return abs_path

    def apply_proposal(self, proposal: PatchOpsProposal) -> List[Dict]:
        """
        Applies a PatchOps proposal to the filesystem.
        Ensures all-or-nothing semantics by validating all pre-hashes before any write.
        """
        # 1. Validation phase (Atomic check)
        for action in proposal.files:
            abs_path = self._get_abs_path(action.path)
            
            # Boundary and protection checks (though UI/Gate should have stopped this)
            if "documents" in action.path or ".agent_ide" in action.path or action.path == ".env":
                raise ValueError(f"Protected path: {action.path}")

            current_hash = calculate_file_hash(abs_path)
            
            if action.operation == PatchActionType.UPDATE:
                if not abs_path.exists():
                    raise FileNotFoundError(f"File not found for update: {action.path}")
                if current_hash != action.pre_hash:
                    raise ValueError(f"Hash mismatch for {action.path}. Expected {action.pre_hash}, got {current_hash}")
            
            elif action.operation == PatchActionType.DELETE:
                if not abs_path.exists():
                    raise FileNotFoundError(f"File not found for delete: {action.path}")
                if current_hash != action.pre_hash:
                    raise ValueError(f"Hash mismatch for {action.path}. Expected {action.pre_hash}, got {current_hash}")
            
            elif action.operation == PatchActionType.CREATE:
                if abs_path.exists():
                    raise FileExistsError(f"File already exists: {action.path}")

        # 2. Execution phase
        results = []
        for action in proposal.files:
            abs_path = self._get_abs_path(action.path)
            
            if action.operation == PatchActionType.CREATE or action.operation == PatchActionType.UPDATE:
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                with open(abs_path, "w") as f:
                    # File-level atomic write (v1)
                    f.write(action.content)
                results.append({"path": action.path, "operation": action.operation, "status": "success"})
            
            elif action.operation == PatchActionType.DELETE:
                if abs_path.exists():
                    abs_path.unlink()
                results.append({"path": action.path, "operation": action.operation, "status": "success"})

        return results
