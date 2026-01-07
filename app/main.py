import gradio as gr
import os
from pathlib import Path
from docops.protocol import parse_docops, expand_action, ActionType
from docops.writer import DocWriter
from state.manager import StateManager

# Configuration (should be from .env in future)
WORKSPACE_ROOT = "/Volumes/NVME/Source/prototype_agent_vibecode"

writer = DocWriter(WORKSPACE_ROOT)
state_manager = StateManager(WORKSPACE_ROOT)

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

def handle_docops(proposal_json):
    try:
        proposal = parse_docops(proposal_json)
        # In a real app, this would update state and wait for approval
        # For now, we'll just show the actions
        actions_str = ""
        for action in proposal.actions:
            expanded = expand_action(action)
            actions_str += f"- {expanded.type}: {expanded.path}\n"
        return f"Proposal {proposal.proposal_id} validated:\n{actions_str}", proposal_json
    except Exception as e:
        return f"Error: {str(e)}", ""

def apply_docops(proposal_json):
    try:
        if not proposal_json:
            return "No proposal to apply."
        proposal = parse_docops(proposal_json)
        expanded_actions = [expand_action(a) for a in proposal.actions]
        reports = writer.execute_bundle(expanded_actions)
        
        state_manager.record_doc_write(proposal.proposal_id)
        
        # Log the write
        log_content = f"# DocWrite Report\nProposal: {proposal.proposal_id}\n\n"
        for r in reports:
            log_content += f"- {r['action']} {r['path']}: {r['status']}\n"
            if 'archive_path' in r:
                log_content += f"  - Archived to: {r['archive_path']}\n"
        
        # Simplified log append for now
        log_path = Path(WORKSPACE_ROOT) / "documents" / "RUN_LOGS" / f"run_write_{proposal.proposal_id}.md"
        with open(log_path, "w") as f:
            f.write(log_content)
        
        return f"Success! Applied {len(reports)} actions. Log: {log_path.name}"
    except Exception as e:
        return f"Error: {str(e)}"

with gr.Blocks(title="Agent IDE - Documents Workspace") as demo:
    gr.Markdown("# Agent IDE - Documents Workspace")
    
    with gr.Row():
        # Left Column: Navigator
        with gr.Column(scale=1):
            gr.Markdown("### Navigator")
            filter_dropdown = gr.Dropdown(choices=["All", "Outline", "Phases", "ADRs", "Run Logs", "Archive"], value="All", label="Filter")
            doc_list = gr.Listbox(choices=get_documents_list(), label="Documents")
            refresh_btn = gr.Button("Refresh")
        
        # Center Column: Chat/Commands
        with gr.Column(scale=2):
            gr.Markdown("### Chat & Commands")
            chat_box = gr.Textbox(label="Transcript", interactive=False, lines=10)
            cmd_input = gr.Textbox(label="Command", placeholder="@docs:phase create ...")
            submit_cmd = gr.Button("Submit")
            
            with gr.Accordion("Direct DocOps Entry (Debug)", open=False):
                proposal_input = gr.Code(label="DocOps JSON", language="json")
                validate_btn = gr.Button("Validate Proposal")
                proposal_status = gr.Markdown("Status: Idle")
                apply_btn = gr.Button("Approve & Write Docs")

        # Right Column: Tabs
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Doc Preview"):
                    preview_box = gr.Markdown("Select a document to preview.")
                with gr.TabItem("Proposed DocOps"):
                    docops_preview = gr.JSON(label="Proposed Actions")
                with gr.TabItem("Archive & Logs"):
                    gr.Markdown("Archive and Logs viewing coming soon.")

    # Event Handlers
    refresh_btn.click(lambda f: gr.update(choices=get_documents_list(f)), inputs=[filter_dropdown], outputs=[doc_list])
    doc_list.select(load_document, inputs=[doc_list], outputs=[preview_box])
    
    validate_btn.click(handle_docops, inputs=[proposal_input], outputs=[proposal_status, docops_preview])
    apply_btn.click(apply_docops, inputs=[proposal_input], outputs=[proposal_status])

if __name__ == "__main__":
    demo.launch()
