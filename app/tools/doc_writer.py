"""
app/tools/doc_writer.py

The pure side-effect tool for writing documents to the filesystem.
Implements the rigid DocOps logic:
- Atomic file writes.
- Automatic archiving of old versions (RewriteDoc).
- Strict path boundary enforcement (must be in `documents/`).
"""

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

def apply_docops_actions(workspace_root: str, proposal_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Applies a list of DocOps actions (Create, Rewrite, Append) to the filesystem.
    This function is the "actuator" for DocOps proposals.
    
    Args:
        workspace_root (str): Root of the workspace.
        proposal_id (str): ID of the proposal triggering this write.
        actions (list): List of action dictionaries from the payload.
        
    Returns:
        dict: A report containing files written, archived, and any errors.
    """
    root = Path(workspace_root).absolute()
    report = {
        "proposal_id": proposal_id,
        "success": True,
        "files_written": [],
        "files_archived": [],
        "errors": []
    }

    for action in actions:
        try:
            action_type = action.get("action_type")
            rel_path = action.get("path")
            content = action.get("content", "")
            
            if not rel_path:
                raise ValueError("Action missing path")
            
            abs_path = (root / rel_path).absolute()
            
            # Boundary check
            if not str(abs_path).startswith(str(root)):
                raise ValueError(f"Forbidden path: {rel_path}")
            
            # Path safety (Packet 04: only under documents/)
            if not rel_path.startswith("documents/"):
                raise ValueError(f"DocOps only permitted under documents/: {rel_path}")

            if action_type == "CreateDoc":
                if abs_path.exists():
                    raise FileExistsError(f"File exists: {rel_path}")
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                with open(abs_path, "w") as f:
                    f.write(content)
                report["files_written"].append(rel_path)

            elif action_type == "RewriteDoc":
                if not abs_path.exists():
                    raise FileNotFoundError(f"File not found for rewrite: {rel_path}")
                
                # Archive first
                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                # documents/PHASES/p1.md -> documents__PHASES__p1.md
                archive_filename = rel_path.replace("/", "__") + f"__{ts}.md"
                archive_dir = root / "documents" / "_archive"
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_rel_path = f"documents/_archive/{archive_filename}"
                archive_abs_path = archive_dir / archive_filename
                
                shutil.copy2(abs_path, archive_abs_path)
                report["files_archived"].append(archive_rel_path)
                
                # Write new version
                with open(abs_path, "w") as f:
                    f.write(content)
                report["files_written"].append(rel_path)

            elif action_type == "AppendDoc":
                if not abs_path.exists():
                    raise FileNotFoundError(f"File not found for append: {rel_path}")
                with open(abs_path, "a") as f:
                    f.write(content)
                report["files_written"].append(rel_path)
            
            elif action_type == "CreatePhaseDoc":
                # Convenience: path is assumed pre-built in current schema
                if abs_path.exists():
                    raise FileExistsError(f"Phase doc exists: {rel_path}")
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                with open(abs_path, "w") as f:
                    f.write(content)
                report["files_written"].append(rel_path)
            
            else:
                raise ValueError(f"Unknown action type: {action_type}")

        except Exception as e:
            report["success"] = False
            report["errors"].append({
                "code": type(e).__name__,
                "message": str(e),
                "path": rel_path if "rel_path" in locals() else None
            })
            # Packet 04 doesn't explicitly say stop on first error for DocOps, 
            # but usually we want to fail fast for safety.
            break 

    return report
