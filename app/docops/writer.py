import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from .protocol import DocOpsAction, ActionType

class DocWriter:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).absolute()

    def _get_absolute_path(self, relative_path: str) -> Path:
        abs_path = (self.workspace_root / relative_path).absolute()
        if not str(abs_path).startswith(str(self.workspace_root)):
            raise ValueError(f"Path is outside workspace root: {relative_path}")
        return abs_path

    def _archive_file(self, relative_path: str):
        source_path = self._get_absolute_path(relative_path)
        if not source_path.exists():
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_dir = self.workspace_root / "documents" / "_archive" / timestamp
        archive_path = archive_dir / relative_path
        
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, archive_path)
        return str(archive_path)

    def execute_action(self, action: DocOpsAction) -> dict:
        if not action.path:
            raise ValueError("Action must have a path")
        
        rel_path = action.path
        abs_path = self._get_absolute_path(rel_path)
        report = {"action": action.type, "path": rel_path, "status": "success"}

        if action.type == ActionType.CREATE_DOC:
            if abs_path.exists():
                raise FileExistsError(f"File already exists: {rel_path}. Use RewriteDoc to overwrite.")
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(abs_path, "w") as f:
                f.write(action.content)

        elif action.type == ActionType.REWRITE_DOC:
            archive_path = self._archive_file(rel_path)
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(abs_path, "w") as f:
                f.write(action.content)
            report["archive_path"] = archive_path

        elif action.type == ActionType.APPEND_LOG:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            with open(abs_path, "a") as f:
                f.write(action.content)

        return report

    def execute_bundle(self, actions: list[DocOpsAction]) -> list[dict]:
        reports = []
        for action in actions:
            reports.append(self.execute_action(action))
        return reports
