from app.orchestration.graph import intake_node, plan_route_node, proposal_assemble_node, IDEState
from unittest.mock import MagicMock, patch

def test_llm_assembly():
    state: IDEState = {
        "session_id": "test_session",
        "workspace_root": "/tmp",
        "phase_id": "01",
        "lane": "patch",
        "intent": "Implement a subtraction function in adder.py",
        "proposal": None,
        "validation": {"pass": True, "messages": []},
        "approval": {"status": "pending", "note": ""},
        "execution": {"status": "idle", "report": []},
        "verification": {"output": "", "result": ""},
        "events": [],
        "errors": [],
        "repair_count": 0
    }

    mock_response = """
    ```json
    {
      "version": 1,
      "proposal_id": "prop_subtract_123",
      "summary": "Add subtraction function to adder.py",
      "actions": [
        {
          "op": "update",
          "path": "adder.py",
          "content": "def add(a, b):\\n    return a + b\\n\\ndef subtract(a, b):\\n    return a - b"
        }
      ]
    }
    ```
    """

    with patch('app.llm.client.LLMClient.generate', return_value=mock_response):
        state = intake_node(state)
        state = plan_route_node(state)
        state = proposal_assemble_node(state)
        
        print(f"Lane: {state['lane']}")
        print(f"Proposal Summary: {state['proposal'].get('summary')}")
        print(f"Proposal ID: {state['proposal'].get('proposal_id')}")
        
        assert state['proposal']['proposal_id'] == "prop_subtract_123"
        assert len(state['events']) > 0
        assert any(e['type'] == 'PROPOSAL_CREATED' for e in state['events'])
        print("Test Passed: LLM assembly correctly parsed mocked Response.")

if __name__ == "__main__":
    test_llm_assembly()
