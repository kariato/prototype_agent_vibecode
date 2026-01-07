from typing import TypedDict, List, Optional, Any, Union
from enum import Enum
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import json
from app.llm import LLMClient
from app.llm.prompts import PLANNING_SYSTEM_PROMPT, IMPLEMENTATION_SYSTEM_PROMPT

class IDEState(TypedDict):
    session_id: str
    workspace_root: str
    phase_id: Optional[str]
    lane: str # "doc" | "patch" | "show"
    intent: str
    proposal: Optional[dict]
    validation: dict # {"pass": bool, "messages": list}
    approval: dict # {"status": str, "note": str}
    execution: dict # {"status": str, "report": list}
    verification: dict # {"output": str, "result": str}
    events: List[dict]
    errors: List[dict]
    repair_count: int

def intake_node(state: IDEState):
    state["events"].append({"type": "STATE_TRANSITION", "node": "intake"})
    # Normalize intent (placeholder)
    return state

def plan_route_node(state: IDEState):
    state["events"].append({"type": "STATE_TRANSITION", "node": "plan_route"})
    if "@docs" in state["intent"]:
        state["lane"] = "doc"
    else:
        state["lane"] = "patch"
    return state

def proposal_assemble_node(state: IDEState):
    state["events"].append({"type": "STATE_TRANSITION", "node": "proposal_assemble"})
    
    client = LLMClient()
    
    if state["lane"] == "doc":
        system_prompt = PLANNING_SYSTEM_PROMPT
    else:
        system_prompt = IMPLEMENTATION_SYSTEM_PROMPT
        
    # Generate proposal from LLM
    try:
        response_text = client.generate(system_prompt, state["intent"])
        
        # Extract JSON (basic extraction in case LLM wraps in markdown)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
            
        proposal_payload = json.loads(json_str)
        state["proposal"] = proposal_payload
        state["events"].append({
            "type": "PROPOSAL_CREATED", 
            "proposal_id": proposal_payload.get("proposal_id"),
            "summary": proposal_payload.get("summary")
        })
    except Exception as e:
        state["errors"].append({"message": f"LLM generation failed: {str(e)}"})
        return state

    return state

def proposal_validate_node(state: IDEState):
    state["events"].append({"type": "STATE_TRANSITION", "node": "proposal_validate"})
    # Validation logic (placeholder)
    state["validation"] = {"pass": True, "messages": []}
    return state

def await_approval_node(state: IDEState):
    state["events"].append({"type": "AWAITING_APPROVAL", "proposal_id": state.get("proposal", {}).get("proposal_id")})
    # This is a pause point in the real runtime
    return state

def execute_proposal_node(state: IDEState):
    state["events"].append({"type": "EXECUTION_STARTED"})
    # Execution logic (placeholder)
    state["execution"] = {"status": "succeeded", "report": []}
    return state

def await_verification_node(state: IDEState):
    state["events"].append({"type": "AWAITING_VERIFICATION"})
    # This is a pause point
    return state

def close_phase_node(state: IDEState):
    state["events"].append({"type": "STATE_TRANSITION", "node": "close_phase"})
    return state

def error_handler_node(state: IDEState):
    state["events"].append({"type": "ERROR", "messages": [e["message"] for e in state["errors"]]})
    return state

def build_ide_graph():
    workflow = StateGraph(IDEState)
    
    workflow.add_node("intake", intake_node)
    workflow.add_node("plan_route", plan_route_node)
    workflow.add_node("proposal_assemble", proposal_assemble_node)
    workflow.add_node("proposal_validate", proposal_validate_node)
    workflow.add_node("await_approval", await_approval_node)
    workflow.add_node("execute_proposal", execute_proposal_node)
    workflow.add_node("await_verification", await_verification_node)
    workflow.add_node("close_phase", close_phase_node)
    workflow.add_node("error_handler", error_handler_node)
    
    workflow.set_entry_point("intake")
    workflow.add_edge("intake", "plan_route")
    workflow.add_edge("plan_route", "proposal_assemble")
    workflow.add_edge("proposal_assemble", "proposal_validate")
    workflow.add_edge("proposal_validate", "await_approval")
    
    # Conditional edges and pause logic would go here in actual langgraph implementation
    # For now, we define the topology structure
    workflow.add_edge("await_approval", "execute_proposal")
    workflow.add_edge("execute_proposal", "await_verification")
    workflow.add_edge("await_verification", "close_phase")
    workflow.add_edge("close_phase", END)
    
    return workflow.compile()
