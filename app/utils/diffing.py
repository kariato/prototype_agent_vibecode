"""
app/utils/diffing.py

Utilities for generating unified diffs and patch summaries.
Used by the PatchOps engine to verify changes and generate artifacts.
"""

import difflib
from typing import List

def generate_unified_diff(old_content: str, new_content: str, filename: str) -> str:
    """Generates a unified diff between two strings."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}"
    )
    
    return "".join(diff)

def generate_patch_summary(files_diffs: List[dict]) -> str:
    """Generates a summary of changes across multiple files."""
    summary = "# Patch Summary\n\n"
    for item in files_diffs:
        filename = item["path"]
        diff = item["diff"]
        
        added = len([l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")])
        removed = len([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")])
        
        summary += f"### {filename}\n"
        summary += f"- **Lines Added:** {added}\n"
        summary += f"- **Lines Removed:** {removed}\n\n"
        
    return summary
