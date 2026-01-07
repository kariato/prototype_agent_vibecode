"""
app/main.py

The main entry point for the Agent IDE application.
Initializes the Gradio UI `Blocks` and wires together the State Manager, Runtime, and Tools.
"""

import gradio as gr
import json
import os
from datetime import datetime
from pathlib import Path
from app.proposals.models import UnifiedProposal, ProposalType, ProposalState, ApprovalRecord
from app.docops.writer import DocWriter
from app.state.manager import StateManager

from app.config.settings import get_settings
from app.runtime.docops import validate_docops_payload, execute_docops

# Load configuration
settings = get_settings()
WORKSPACE_ROOT = settings.WORKSPACE_ROOT_DEFAULT

writer = DocWriter(WORKSPACE_ROOT)
state_manager = StateManager(WORKSPACE_ROOT)

def get_current_state():
    """
    Fetches the current proposal and formats it for the UI.
    
    Returns:
         tuple: (State String, Detailed Markdown)
    """
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    if not proposal:
        return "Idle", "No active proposal."
    
    status_text = f"**Type:** {proposal['proposal_type']} | **State:** {proposal['state']}\n"
    status_text += f"**Summary:** {proposal['summary']}\n"
    if proposal.get("validation_messages"):
        status_text += "**Validation:**\n" + "\n".join([f"- {m}" for m in proposal["validation_messages"]])
    
    return proposal["state"], status_text

def handle_proposal_submission(proposal_json):
    """
    Validates and processes a raw JSON proposal submission from the UI.
    Determines if it's a DocOps or PatchOps proposal and runs initial validation.
    
    Args:
        proposal_json (str): Raw JSON string.
    
    Returns:
        tuple: (Status Message, Payload Dict or None)
    """
    try:
        # Handle @docs command
        if proposal_json.startswith("@docs"):
            cmd = proposal_json.replace("@docs:", "@docs ").strip()
            parts = cmd.split(" ")
            if len(parts) >= 4 and parts[1] == "phase" and parts[2] == "create":
                phase_num = parts[3]
                title = " ".join(parts[4:]) if len(parts) > 4 else "Unknown"
                proposal_data = {
                    "proposal_id": f"doc_phase_{phase_num}",
                    "phase_id": phase_num,
                    "summary": f"Create phase {phase_num} doc: {title}",
                    "actions": [
                        {"type": "CreateDoc", "path": f"documents/PHASES/phase_{phase_num}_{title.replace(' ', '_').lower()}.md", "content": f"# Phase {phase_num} - {title}\nPlaceholder content."},
                        {"type": "AppendLog", "path": f"documents/RUN_LOGS/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_phase{phase_num}.md", "content": f"Started phase {phase_num}"}
                    ]
                }
                proposal_json = json.dumps(proposal_data)

        data = json.loads(proposal_json)
        
        # Determine type
        is_doc = any(a.get("type", "").endswith("Doc") or a.get("type") == "AppendLog" for a in data.get("actions", []))
        p_type = ProposalType.DOC if is_doc else ProposalType.PATCH
        
        proposal = UnifiedProposal(
            proposal_id=data.get("proposal_id", "manual_123"),
            proposal_type=p_type,
            phase_id=data.get("phase_id", "00"),
            summary=data.get("summary", "Manual Proposal"),
            targets=[],
            payload=data
        )
        
        validation_errors = []
        diffs_to_save = []
        
        if p_type == ProposalType.DOC:
            proposal.targets = [a.get("path", "unknown") for a in data.get("actions", [])]
            ok, errors = validate_docops_payload(data, WORKSPACE_ROOT)
            if not ok:
                validation_errors.extend(errors)
        else:
            # PatchOps Validation
            from app.proposals.patchops import PatchOpsProposal, PatchActionType
            from app.utils.hashing import calculate_file_hash, calculate_content_hash
            from app.utils.diffing import generate_unified_diff
            
            p_patch = PatchOpsProposal(**data)
            proposal.targets = [f.path for f in p_patch.files]
            
            if len([f for f in p_patch.files if "test" not in f.path]) > 3:
                validation_errors.append("Too many non-test files in one patch (max 3).")
            
            for file_patch in p_patch.files:
                abs_p = Path(WORKSPACE_ROOT) / file_patch.path
                
                # Boundary check
                if not str(abs_p.absolute()).startswith(WORKSPACE_ROOT):
                    validation_errors.append(f"Forbidden path: {file_patch.path}")
                
                # Protected paths
                if "documents" in file_patch.path or ".agent_ide" in file_patch.path or file_patch.path == ".env":
                    validation_errors.append(f"Protected path: {file_patch.path}")

                current_hash = calculate_file_hash(abs_p)
                current_content = ""
                if abs_p.exists():
                    with open(abs_p, "r") as f:
                        current_content = f.read()

                if file_patch.operation == PatchActionType.CREATE:
                    if abs_p.exists():
                        validation_errors.append(f"File already exists: {file_patch.path}")
                    if calculate_content_hash(file_patch.content) != file_patch.post_hash:
                        validation_errors.append(f"Post-hash mismatch for {file_patch.path}")
                    diffs_to_save.append({
                        "path": file_patch.path,
                        "diff": generate_unified_diff("", file_patch.content, file_patch.path)
                    })

                elif file_patch.operation == PatchActionType.UPDATE:
                    if not abs_p.exists():
                        validation_errors.append(f"File not found: {file_patch.path}")
                    if current_hash != file_patch.pre_hash:
                        validation_errors.append(f"Hash mismatch for {file_patch.path}. Stale patch?")
                    if calculate_content_hash(file_patch.content) != file_patch.post_hash:
                        validation_errors.append(f"Post-hash mismatch for {file_patch.path}")
                    diffs_to_save.append({
                        "path": file_patch.path,
                        "diff": generate_unified_diff(current_content, file_patch.content, file_patch.path)
                    })

                elif file_patch.operation == PatchActionType.DELETE:
                    if not abs_p.exists():
                        validation_errors.append(f"File not found: {file_patch.path}")
                    if current_hash != file_patch.pre_hash:
                        validation_errors.append(f"Hash mismatch for {file_patch.path}")
                    diffs_to_save.append({
                        "path": file_patch.path,
                        "diff": generate_unified_diff(current_content, "", file_patch.path)
                    })

        if validation_errors:
            proposal.state = ProposalState.FAILED
            proposal.validation_messages = validation_errors
        else:
            proposal.state = ProposalState.AWAITING_APPROVAL
            # Store diff artifact if Patch
            if p_type == ProposalType.PATCH:
                from app.utils.diffing import generate_patch_summary
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                diff_filename = f"patch_{timestamp}_phase{proposal.phase_id}.diff"
                diff_path = Path(WORKSPACE_ROOT) / "documents" / "RUN_LOGS" / diff_filename
                
                full_diff_content = generate_patch_summary(diffs_to_save)
                for d in diffs_to_save:
                    full_diff_content += f"\n--- {d['path']} ---\n{d['diff']}\n"
                
                with open(diff_path, "w") as f:
                    f.write(full_diff_content)
                
                proposal.payload["diff_file"] = diff_filename
                proposal.payload["diff_content"] = full_diff_content

        state_manager.submit_proposal(proposal.model_dump())
        _, status_text = get_current_state()
        return status_text, proposal.payload
    except Exception as e:
        return f"Error: {str(e)}", None

def handle_approval(decision, note=""):
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    if not proposal:
        return "No active proposal."
    
    approval = ApprovalRecord(
        proposal_id=proposal["proposal_id"],
        phase_id=proposal.get("phase_id", "00"),
        gate="B" if proposal["proposal_type"] == ProposalType.PATCH else "A",
        decision=decision,
        note=note
    )
    
    state_manager.record_approval(approval.model_dump())
    _, status_text = get_current_state()
    return status_text

def apply_current_proposal():
    """
    Executes the currently pending proposal if it is in an approved state.
    Routes to the appropriate runtime (DocOps or PatchOps) based on type.
    """
    from app.runtime.execution_engine import execute_patch_proposal
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    if not proposal: return "No proposal."
    
    try:
        if proposal["proposal_type"] == ProposalType.DOC:
            report = execute_docops(WORKSPACE_ROOT, proposal["proposal_id"], "ui_session")
            if report["success"]:
                return f"DocOps executed: {report['files_written']}. Archived: {report['files_archived']}"
            else:
                return f"DocOps failed: {report['errors']}"
        else:
            report = execute_patch_proposal(WORKSPACE_ROOT, proposal["proposal_id"], "ui_session")
            return f"Execution report: {report['status']}. {report.get('results', [])}"
    except Exception as e:
        return f"Error: {str(e)}"

def handle_verification(output, result):
    from app.runtime.verification import record_verification
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    if not proposal: return "No proposal."
    
    try:
        res = record_verification(WORKSPACE_ROOT, proposal["proposal_id"], "ui_session", result == "PASS", output)
        return f"Verification recorded: {res['status']}"
    except Exception as e:
        return f"Error: {str(e)}"

def scan_for_recovery():
    """Scans the workspace for leftover .tmp, .bak, or .del files from failed transactions."""
    leftovers = []
    for root, _, filenames in os.walk(WORKSPACE_ROOT):
        for filename in filenames:
            if ".tmp." in filename or ".bak." in filename or ".del." in filename:
                leftovers.append(os.path.join(root, filename))
    return leftovers

def perform_cleanup():
    """Deletes all detected leftover transaction files."""
    leftovers = scan_for_recovery()
    for f in leftovers:
        try:
            os.remove(f)
        except:
            pass
    return f"Cleaned up {len(leftovers)} files."

def bootstrap_workspace():
    try:
        # Directories
        dirs = ["documents/PHASES", "documents/DECISIONS", "documents/RUN_LOGS", "documents/_archive", ".agent_ide"]
        for d in dirs:
            (Path(WORKSPACE_ROOT) / d).mkdir(parents=True, exist_ok=True)
        
        # Initial State
        state = state_manager.get_state()
        state["workspace"] = {"root_path": WORKSPACE_ROOT, "status": "initialized"}
        state_manager._save_state(state)
        
        # Initial Log
        log_path = Path(WORKSPACE_ROOT) / "documents" / "RUN_LOGS" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_phase01_bootstrap.md"
        with open(log_path, "w") as f:
            f.write("# Phase 01: Bootstrap\nWorkspace initialized successfully.")
            
        return "Workspace bootstrapped successfully."
    except Exception as e:
        return f"Bootstrap failed: {str(e)}"

from app.runtime.events import EventImpact

def format_visual_timeline(events: list) -> str:
    """Formats events into a clean Markdown timeline."""
    if not events:
        return "*No events recorded.*"
    
    lines = []
    for e in reversed(events):
        ts = datetime.fromtimestamp(e['timestamp']).strftime('%H:%M:%S')
        impact = e.get('impact', 'info')
        etype = e.get('type', 'EVENT')
        
        # Color coding based on impact
        icon = "ℹ️"
        if impact == EventImpact.MUTATION:
            icon = "⚡"
            etype = f"**{etype}**"
        elif impact == EventImpact.ERROR:
            icon = "❌"
            etype = f"<span style='color:red'>{etype}</span>"
        elif impact == EventImpact.SYSTEM:
            icon = "⚙️"
        
        line = f"| `{ts}` | {icon} | {etype} |"
        lines.append(line)
    
    header = "| Time | | Event |\n| :--- | :--- | :--- |"
    return header + "\n" + "\n".join(lines)

def get_documents_list(filter_type="All"):
    doc_dir = Path(WORKSPACE_ROOT) / "documents"
    if not doc_dir.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(doc_dir):
        for filename in filenames:
            if filename.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, filename), doc_dir)
                if filter_type == "All":
                    files.append(rel_path)
                elif filter_type == "Outline" and filename == "PROJECT_OUTLINE.md":
                    files.append(rel_path)
                elif filter_type == "Phases" and "PHASES" in root:
                    files.append(rel_path)
                elif filter_type == "ADRs" and "DECISIONS" in root:
                    files.append(rel_path)
                elif filter_type == "Run Logs" and "RUN_LOGS" in root:
                    files.append(rel_path)
                elif filter_type == "Archive" and "_archive" in root:
                    files.append(rel_path)
    return sorted(files)

def load_document(rel_path):
    if not rel_path:
        return ""
    abs_path = Path(WORKSPACE_ROOT) / "documents" / rel_path
    if abs_path.exists():
        with open(abs_path, "r") as f:
            return f.read()
    return "File not found."

def handle_brain_intent(intent):
    from app.orchestration.graph import IDEState
    from app.orchestration.runtime import GraphRuntime
    
    runtime = GraphRuntime(WORKSPACE_ROOT)
    
    # Initialize State
    initial_state: IDEState = {
        "session_id": "session_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        "workspace_root": WORKSPACE_ROOT,
        "phase_id": "01", # Default or detect current
        "lane": "patch" if "@docs" not in intent else "doc",
        "intent": intent,
        "proposal": None,
        "validation": {"pass": True, "messages": []},
        "approval": {"status": "pending", "note": ""},
        "execution": {"status": "idle", "report": []},
        "verification": {"output": "", "result": ""},
        "events": [],
        "errors": [],
        "repair_count": 0
    }
    
    # Run to pause (await_approval)
    final_state, checkpoint_id = runtime.run_to_pause(initial_state)
    
    if final_state.get("errors"):
        return f"Error: {final_state['errors'][0]['message']}", None, "", refresh_runtime_hist()[1]
        
    proposal = final_state.get("proposal")
    if not proposal:
        return "Internal Error: No proposal generated.", None, "", refresh_runtime_hist()[1]
        
    # Wrap in UnifiedProposal for the UI
    status, payload = handle_proposal_submission(json.dumps(proposal))
    
    # Sync events from graph to project state
    p_state = state_manager.get_state()
    for ev in final_state.get("events", []):
        p_state.setdefault("events", []).append(ev)
    state_manager._save_state(p_state)
    
    diff_content = payload.get("diff_content", "No diff for this proposal.") if payload else ""
    return status, payload, f"```diff\n{diff_content}\n```", refresh_runtime_hist()[1]

with gr.Blocks(title="Agent IDE - Phase 9 Hardened UI") as demo:
    gr.Markdown("# Agent IDE - Unified Approval Center")
    
    with gr.Row():
        # Panel 1: Documents Workspace
        with gr.Column(scale=1):
            gr.Markdown("### 🗄️ Documents Workspace")
            filter_dropdown = gr.Dropdown(choices=["All", "Outline", "Phases", "ADRs", "Run Logs", "Archive"], value="All", label="Filter")
            doc_list = gr.Dropdown(choices=get_documents_list(), label="Documents")
            refresh_btn = gr.Button("Refresh")
            bootstrap_btn = gr.Button("🚀 Bootstrap Workspace", variant="secondary")
            scaffold_btn = gr.Button("🚀 Create Acceptance Scaffold", variant="secondary")
            
            # Integrated Preview
            preview_box = gr.Markdown("Select a document to preview.")
        
        # Panel 2: Approval & Intent (Runtime Console part A)
        with gr.Column(scale=2):
            gr.Markdown("### ⚖️ Approval & Intent")
            
            with gr.Accordion("🚨 Recovery Required!", open=True, visible=False) as recovery_alert:
                gr.Markdown("Leftover transaction files detected (.tmp, .bak, .del).")
                recovery_list = gr.Textbox(label="Orphaned Files", lines=3, interactive=False)
                cleanup_btn = gr.Button("🗑️ Clean Up Artifacts", variant="stop")

            proposal_status = gr.Markdown("Status: Idle")
            proposal_payload_view = gr.JSON(label="Active Proposal Artifact (JSON)")
            
            with gr.Row():
                approve_btn = gr.Button("✅ Approve", variant="primary")
                reject_btn = gr.Button("❌ Reject", variant="stop")
            
            note_input = gr.Textbox(label="Decision Note", placeholder="Reason for decision...")
            execute_btn = gr.Button("⚡ Execute Action", variant="primary")

            with gr.Row():
                intent_input = gr.Textbox(label="Agent Intent (AI Brain)", placeholder="e.g., Implement add() in math.py", scale=4)
                brain_btn = gr.Button("🧠 Think & Plan", variant="primary", scale=1)

            with gr.Accordion("Debug: Manual Proposal Entry", open=False):
                proposal_input = gr.Code(label="Proposal JSON (Draft)", language="json")
                submit_proposal_btn = gr.Button("Submit Proposal")

        # Panel 3: Diff Viewer & Verification
        with gr.Column(scale=2):
            gr.Markdown("### 🔍 Diff Viewer & Verification")
            with gr.Tabs():
                with gr.TabItem("Diff View"):
                    diff_view = gr.Markdown("No active patch proposal.")
                with gr.TabItem("Verification"):
                    verif_output = gr.Textbox(label="Test/Lint Output Artifact", placeholder="Paste output here...", lines=10)
                    with gr.Row():
                        pass_btn = gr.Button("✅ PASS", variant="primary")
                        fail_btn = gr.Button("❌ FAIL", variant="stop")
                    verif_status = gr.Markdown("Status: Pending")

        # Panel 4: Runtime Console (Part B: History)
        with gr.Column(scale=1):
            gr.Markdown("### 📜 Runtime Console")
            checkpoint_view = gr.JSON(label="Last Checkpoint State")
            event_log = gr.Markdown(label="Visual Timeline")
            refresh_hist_btn = gr.Button("Refresh History")

    # Event Handlers
    from app.orchestration.runtime import GraphRuntime
    from app.proposals.artifacts import ProposalArtifactManager
    runtime = GraphRuntime(WORKSPACE_ROOT)
    artifact_manager = ProposalArtifactManager(WORKSPACE_ROOT)

    def refresh_runtime_hist():
        state = state_manager.get_state()
        runtime_info = state.get("runtime", {})
        events = state.get("events", [])
        timeline_md = format_visual_timeline(events)
        
        leftovers = scan_for_recovery()
        recovery_visible = len(leftovers) > 0
        leftovers_text = "\n".join(leftovers)
        
        return runtime_info, timeline_md, gr.update(visible=recovery_visible), leftovers_text

    demo.load(refresh_runtime_hist, outputs=[checkpoint_view, event_log, recovery_alert, recovery_list])
    refresh_btn.click(lambda f: gr.update(choices=get_documents_list(f)), inputs=[filter_dropdown], outputs=[doc_list])
    doc_list.select(load_document, inputs=[doc_list], outputs=[preview_box])
    refresh_hist_btn.click(refresh_runtime_hist, outputs=[checkpoint_view, event_log, recovery_alert, recovery_list])
    cleanup_btn.click(perform_cleanup).then(refresh_runtime_hist, outputs=[checkpoint_view, event_log, recovery_alert, recovery_list])

    def on_submit(proposal_json):
        # 1. Standard validation
        status, payload = handle_proposal_submission(proposal_json)
        if "Error" in status:
            return status, None, "Error", None
        
        # 2. Save artifact
        proposal_id = payload.get("proposal_id", "manual")
        artifact_path = artifact_manager.save_proposal(proposal_id, payload)
        
        # 3. Update project state with the artifact pointer
        p_state = state_manager.get_state()
        p_state.setdefault("runtime", {})["pending_proposal_path"] = str(artifact_path)
        
        # 4. Log event
        event = runtime.emit_event("PROPOSAL_CREATED", {"proposal_id": proposal_id, "path": str(artifact_path)})
        p_state.setdefault("events", []).append(event)
        state_manager._save_state(p_state)

        diff_content = payload.get("diff_content", "No diff for this proposal.") if payload else ""
        return status, payload, f"```diff\n{diff_content}\n```", refresh_runtime_hist()[1]

    submit_proposal_btn.click(on_submit, inputs=[proposal_input], outputs=[proposal_status, proposal_payload_view, diff_view, event_log])
    
    approve_btn.click(lambda n: handle_approval("Approved", n), inputs=[note_input], outputs=[proposal_status])
    reject_btn.click(lambda n: handle_approval("Rejected", n), inputs=[note_input], outputs=[proposal_status])
    
    execute_btn.click(apply_current_proposal, outputs=[proposal_status])
    bootstrap_btn.click(bootstrap_workspace, outputs=[proposal_status])
    
    from app.tools.scaffold_phase07 import scaffold_phase07_workspace
    scaffold_btn.click(lambda: f"Scaffold result: {scaffold_phase07_workspace(WORKSPACE_ROOT)}", outputs=[proposal_status])

    brain_btn.click(handle_brain_intent, inputs=[intent_input], outputs=[proposal_status, proposal_payload_view, diff_view, event_log])

    pass_btn.click(lambda o: handle_verification(o, "PASS"), inputs=[verif_output], outputs=[verif_status])
    fail_btn.click(lambda o: handle_verification(o, "FAIL"), inputs=[verif_output], outputs=[verif_status])

if __name__ == "__main__":
    demo.launch()
