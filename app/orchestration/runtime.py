import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .graph import build_ide_graph, IDEState
from app.state.manager import StateManager

class GraphRuntime:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).absolute()
        self.state_manager = StateManager(str(self.workspace_root))
        self.graph = build_ide_graph()
        self.artifacts_dir = self.workspace_root / ".agent_ide" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _save_checkpoint(self, state: IDEState, node_name: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_id = f"chk_{timestamp}_{node_name}"
        artifact_path = self.artifacts_dir / f"{checkpoint_id}.json"
        
        # Save full state snapshot
        with open(artifact_path, "w") as f:
            json.dump(state, f, indent=4)
        
        # Update project state pointer
        proj_state = self.state_manager.get_state()
        proj_state.setdefault("runtime", {})
        proj_state["runtime"].update({
            "last_checkpoint_id": checkpoint_id,
            "last_checkpoint_path": str(artifact_path.relative_to(self.workspace_root)),
            "resume_node": node_name,
            "updated_at": datetime.now().timestamp()
        })
        self.state_manager._save_state(proj_state)
        
        return checkpoint_id

    def run_to_pause(self, initial_state: IDEState):
        """
        Executes the graph until it hits a pause point (AwaitApproval or AwaitUserVerification).
        """
        # In a real langgraph, this would use thread_id and checkpointing
        # Here we simulate the sequence for Phase 6
        current_state = initial_state
        
        # Simulate transition through nodes
        # intake -> plan_route -> proposal_assemble -> proposal_validate
        # This is where the actual graph.invoke() would happen
        
        checkpoint_id = self._save_checkpoint(current_state, "await_approval")
        return current_state, checkpoint_id

    def resume(self, checkpoint_id: str):
        """
        Restores state from a checkpoint and returns it.
        """
        artifact_path = self.artifacts_dir / f"{checkpoint_id}.json"
        if not artifact_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")
            
        with open(artifact_path, "r") as f:
            return json.load(f)

    def emit_event(self, event_type: str, payload: dict, impact: str = "info", node_name: str = None):
        """
        Returns a structured event for the UI.
        """
        from app.runtime.events import create_event, EventImpact
        return create_event(
            event_type=event_type,
            session_id="default_session", # In a real system, this would be per-run
            impact=EventImpact(impact),
            node_name=node_name or payload.get("node_name"),
            payload=payload
        )
