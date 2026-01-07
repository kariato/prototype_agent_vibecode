import os
import shutil
import random
import string
from pathlib import Path
from typing import List, Dict, Optional
from app.proposals.patchops import PatchOpsProposal, PatchActionType
from app.utils.hashing import calculate_file_hash, calculate_content_hash

class PatchEngine:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).absolute()

    def _get_abs_path(self, rel_path: str) -> Path:
        abs_path = (self.workspace_root / rel_path).absolute()
        if not str(abs_path).startswith(str(self.workspace_root)):
            raise ValueError(f"Forbidden path: {rel_path}. Path must be within workspace root.")
        return abs_path

    def _generate_nonce(self, length=6):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _fsync_dir(self, dir_path: Path):
        fd = os.open(dir_path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def apply_proposal(self, proposal: PatchOpsProposal) -> List[Dict]:
        """
        Applies a PatchOps proposal using a transactional multi-stage approach.
        Stages: Preflight/Stage (temps) -> Commit (backups/renames) -> Cleanup
        Rollback occurs if any commit step fails.
        """
        proposal_id = proposal.proposal_id
        staged_files = [] # List of tuples: (action, temp_path)
        committed_files = [] # List of tuples: (action, backup_path, original_target)
        results = []

        try:
            # 1. STAGE: Validation & Temp creation
            for action in proposal.files:
                abs_path = self._get_abs_path(action.path)
                
                # Boundary and protection checks
                if "documents" in action.path or ".agent_ide" in action.path or action.path == ".env":
                    raise ValueError(f"Protected path: {action.path}")

                current_hash = calculate_file_hash(abs_path)
                
                if action.operation == PatchActionType.UPDATE or action.operation == PatchActionType.DELETE:
                    if not abs_path.exists():
                        raise FileNotFoundError(f"File not found: {action.path}")
                    if current_hash != action.pre_hash:
                        raise ValueError(f"Hash mismatch for {action.path}. Expected {action.pre_hash}, got {current_hash}")
                
                elif action.operation == PatchActionType.CREATE:
                    if abs_path.exists():
                        raise FileExistsError(f"File already exists: {action.path}")

                # Create temp file for creates/updates
                if action.operation in [PatchActionType.CREATE, PatchActionType.UPDATE]:
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    nonce = self._generate_nonce()
                    temp_path = abs_path.parent / f".{abs_path.name}.tmp.{proposal_id}.{nonce}"
                    
                    with open(temp_path, "w") as f:
                        f.write(action.content)
                        f.flush()
                        os.fsync(f.fileno())
                    
                    staged_files.append((action, temp_path))
                else:
                    staged_files.append((action, None))

            # 2. COMMIT: Atomic renames with backups
            # Sort files by path for deterministic order
            sorted_staged = sorted(staged_files, key=lambda x: x[0].path)
            
            # Sub-stage: Process Updates and Creates first
            for action, temp_path in sorted_staged:
                if action.operation == PatchActionType.DELETE:
                    continue
                    
                target = self._get_abs_path(action.path)
                backup = None
                
                if action.operation == PatchActionType.UPDATE:
                    backup = target.parent / f".{target.name}.bak.{proposal_id}"
                    shutil.move(target, backup)
                    self._fsync_dir(target.parent)
                
                # Move temp to target
                shutil.move(temp_path, target)
                self._fsync_dir(target.parent)
                
                # Register for rollback before integrity check
                committed_files.append((action, backup, target))

                # Integrity check
                if calculate_file_hash(target) != action.post_hash:
                     raise ValueError(f"Post-hash integrity check failed for {action.path}")

            # Sub-stage: Process Deletes last
            for action, _ in sorted_staged:
                if action.operation != PatchActionType.DELETE:
                    continue
                
                target = self._get_abs_path(action.path)
                backup = target.parent / f".{target.name}.del.{proposal_id}"
                shutil.move(target, backup)
                self._fsync_dir(target.parent)
                committed_files.append((action, backup, target))

            # 3. CLEANUP: Success Case
            execution_report = {
                "proposal_id": proposal_id,
                "status": "committed",
                "files": [
                    {"path": a.path, "op": a.operation, "status": "success"} for a, b, t in committed_files
                ]
            }
            report_path = self.workspace_root / ".agent_ide" / "artifacts" / f"execution_{proposal_id}.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w") as f:
                import json
                json.dump(execution_report, f, indent=4)

            for action, backup, target in committed_files:
                if backup and backup.exists():
                    backup.unlink()
                results.append({"path": action.path, "operation": action.operation, "status": "success"})

        except Exception as e:
            # ROLLBACK
            rollback_report = {
                "proposal_id": proposal_id,
                "status": "rolled_back",
                "error": str(e)
            }
            # (Save rollback report same as above if needed, but the main goal is forensics)
            for action, backup, target in reversed(committed_files):
                try:
                    if action.operation == PatchActionType.UPDATE:
                        # Restore from backup
                        if target.exists():
                            target.unlink()
                        shutil.move(backup, target)
                    elif action.operation == PatchActionType.CREATE:
                        # Remove created file
                        if target.exists():
                            target.unlink()
                    elif action.operation == PatchActionType.DELETE:
                        # Restore from del-stage
                        shutil.move(backup, target)
                except:
                    pass # Best effort rollback
            
            # Also cleanup any remaining temps
            for _, temp_path in staged_files:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
            
            raise e

        return results
