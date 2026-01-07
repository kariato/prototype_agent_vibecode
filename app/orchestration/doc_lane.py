from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
import json

class DocLaneState(TypedDict):
    user_input: str
    intent: str
    target_docs: List[str]
    drafts: dict
    proposal: dict
    approval_status: str
    write_report: List[dict]
    messages: List[str]

def doc_intake(state: DocLaneState):
    # Mocking interpretation
    state["messages"].append("Intake: Interpreting user command.")
    if "@docs:phase create" in state["user_input"]:
        state["intent"] = "create_phase"
    else:
        state["intent"] = "unknown"
    return state

def doc_draft(state: DocLaneState):
    state["messages"].append("Draft: Generating markdown content.")
    state["drafts"] = {"documents/PHASES/new_phase.md": "# New Phase\nDetails..."}
    return state

def doc_ops_emit(state: DocLaneState):
    state["messages"].append("Emit: Producing DocOps proposal.")
    state["proposal"] = {
        "proposal_id": "prop_new",
        "summary": "Create new phase",
        "actions": [
            {"type": "CreateDoc", "path": "documents/PHASES/new_phase.md", "content": state["drafts"]["documents/PHASES/new_phase.md"]}
        ]
    }
    return state

def build_doc_lane():
    workflow = StateGraph(DocLaneState)
    
    workflow.add_node("intake", doc_intake)
    workflow.add_node("draft", doc_draft)
    workflow.add_node("emit", doc_ops_emit)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "draft")
    workflow.add_edge("draft", "emit")
    workflow.add_edge("emit", END)
    
    return workflow.compile()
