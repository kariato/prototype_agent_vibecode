import gradio as gr
import os
from pathlib import Path
from proposals.models import UnifiedProposal, ProposalType, ProposalState, ApprovalRecord

# Configuration (should be from .env in future)
WORKSPACE_ROOT = "/Volumes/NVME/Source/prototype_agent_vibecode"

writer = DocWriter(WORKSPACE_ROOT)
state_manager = StateManager(WORKSPACE_ROOT)

def get_current_state():
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
    try:
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
            # DocOps validation (already mostly handled by pydantic if we used it here)
        else:
            # PatchOps Validation
            from proposals.patchops import PatchOpsProposal, PatchActionType
            from utils.hashing import calculate_file_hash, calculate_content_hash
            from utils.diffing import generate_unified_diff
            
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
                from utils.diffing import generate_patch_summary
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

        state_manager.submit_proposal(proposal.dict())
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
    
    state_manager.record_approval(approval.model_dump()) # use model_dump as per test warning
    _, status_text = get_current_state()
    return status_text

def apply_current_proposal():
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    if not proposal or proposal["state"] != ProposalState.APPROVED:
        return "Proposal must be approved first."
    
    try:
        state_manager.update_proposal_state(ProposalState.EXECUTING)
        
        if proposal["proposal_type"] == ProposalType.DOC:
            # Re-parse to use the docops protocol logic
            from docops.protocol import parse_docops, expand_action
            doc_proposal = parse_docops(json.dumps(proposal["payload"]))
            expanded_actions = [expand_action(a) for a in doc_proposal.actions]
            reports = writer.execute_bundle(expanded_actions)
            state_manager.record_doc_write(proposal["proposal_id"])
            return f"Completed: {len(reports)} doc actions applied."
        else:
            # PatchOps execution
            from proposals.patchops import PatchOpsProposal
            from patchops.engine import PatchEngine
            
            patch_engine = PatchEngine(WORKSPACE_ROOT)
            p_patch = PatchOpsProposal(**proposal["payload"])
            results = patch_engine.apply_proposal(p_patch)
            
            # Transition to Executing -> Awaiting_Verification (implicit in Completed for now if no verification needed, but Phase 5 requires loop)
            # We'll stick to the Phase 5 spec: after apply, user must verify.
            state_manager.update_proposal_state("Awaiting_Verification")
            
            log_content = f"# Patch Apply Report\nProposal: {proposal['proposal_id']}\n\n"
            for r in results:
                log_content += f"- {r['operation']} {r['path']}: {r['status']}\n"
            
            log_path = Path(WORKSPACE_ROOT) / "documents" / "RUN_LOGS" / f"run_patch_{proposal['proposal_id']}.md"
            with open(log_path, "w") as f:
                f.write(log_content)
                
            return f"Applied {len(results)} changes. Please verify and paste test output in the Verification tab."
            
    except Exception as e:
        state_manager.update_proposal_state(ProposalState.FAILED)
        return f"Failed: {str(e)}"

def handle_verification(output, result):
    state = state_manager.get_state()
    proposal = state.get("current_proposal")
    if not proposal or proposal["state"] != "Awaiting_Verification":
        return "No proposal awaiting verification."
    
    state_manager.record_verification(proposal["proposal_id"], output, result)
    
    # If Failed, log it and prepare for repair (Phase 05 Repair Lane)
    if result == "FAIL":
        # Simplified repair log entry
        log_path = Path(WORKSPACE_ROOT) / "documents" / "RUN_LOGS" / f"run_verification_{proposal['proposal_id']}_fail.md"
        with open(log_path, "w") as f:
            f.write(f"# Verification FAILED\nProposal: {proposal['proposal_id']}\n\n## Output\n```\n{output}\n```")
        return f"Verification marked FAIL. Repair proposal needed (referencing {proposal['proposal_id']})."
    
    return f"Verification marked PASS. Proposal {proposal['proposal_id']} completed."

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

with gr.Blocks(title="Agent IDE - Unified Approval Center") as demo:
    gr.Markdown("# Agent IDE - Unified Approval Center")
    
    with gr.Row():
        # Left Column: Navigator
        with gr.Column(scale=1):
            gr.Markdown("### Navigator")
            filter_dropdown = gr.Dropdown(choices=["All", "Outline", "Phases", "ADRs", "Run Logs", "Archive"], value="All", label="Filter")
            doc_list = gr.Listbox(choices=get_documents_list(), label="Documents")
            refresh_btn = gr.Button("Refresh")
        
        # Center Column: Chat & Approval
        with gr.Column(scale=2):
            gr.Markdown("### Approval Center")
            proposal_status = gr.Markdown("Status: Loading...")
            
            with gr.Row():
                approve_btn = gr.Button("✅ Approve", variant="primary")
                reject_btn = gr.Button("❌ Reject", variant="stop")
            
            note_input = gr.Textbox(label="Approval/Rejection Note", placeholder="Reason for decision...")
            execute_btn = gr.Button("⚡ Execute Action", variant="primary")

            with gr.Accordion("Debug: Manual Proposal Entry", open=False):
                proposal_input = gr.Code(label="Proposal JSON", language="json")
                submit_proposal_btn = gr.Button("Submit Proposal")

        # Right Column: Preview
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Doc Preview"):
                    preview_box = gr.Markdown("Select a document to preview.")
                with gr.TabItem("Proposal Payload"):
                    proposal_payload_view = gr.JSON(label="Payload")
                with gr.TabItem("Diff Viewer"):
                    diff_view = gr.Markdown("No active patch proposal.")
                with gr.TabItem("Verification"):
                    gr.Markdown("### Verification Loop")
                    verif_output = gr.Textbox(label="Test/Lint Output", placeholder="Paste output here...", lines=5)
                    with gr.Row():
                        pass_btn = gr.Button("✅ PASS", variant="primary")
                        fail_btn = gr.Button("❌ FAIL", variant="stop")
                    verif_status = gr.Markdown("Status: Pending")

    # Event Handlers
    demo.load(lambda: get_current_state()[1], outputs=[proposal_status])
    refresh_btn.click(lambda f: gr.update(choices=get_documents_list(f)), inputs=[filter_dropdown], outputs=[doc_list])
    doc_list.select(load_document, inputs=[doc_list], outputs=[preview_box])
    
    def on_submit(proposal_json):
        status, payload = handle_proposal_submission(proposal_json)
        diff_content = payload.get("diff_content", "No diff for this proposal.") if payload else ""
        return status, payload, f"```diff\n{diff_content}\n```"

    submit_proposal_btn.click(on_submit, inputs=[proposal_input], outputs=[proposal_status, proposal_payload_view, diff_view])
    
    approve_btn.click(lambda n: handle_approval("Approved", n), inputs=[note_input], outputs=[proposal_status])
    reject_btn.click(lambda n: handle_approval("Rejected", n), inputs=[note_input], outputs=[proposal_status])
    
    execute_btn.click(apply_current_proposal, outputs=[proposal_status])

    pass_btn.click(lambda o: handle_verification(o, "PASS"), inputs=[verif_output], outputs=[verif_status])
    fail_btn.click(lambda o: handle_verification(o, "FAIL"), inputs=[verif_output], outputs=[verif_status])

if __name__ == "__main__":
    demo.launch()
