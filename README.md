# Warning this is a prototype to test chatgp and antigravity
# it is not ready for production use
# its actually just a proof of concept using vibe coding
# Do not use it for production

# Document-First Lightweight Agent IDE

**A local-first, crash-safe, and approval-driven development environment for AI Agents.**

---

## 🚀 Overview

The **Agent IDE** is a specialized environment designed for **High-Assurance AI Coding**. Unlike typical "autonomous" agents that modify code directly, this system enforces a strict **Document-First** workflow. The AI must first **Plan** (via `DocOps`), get **Approval**, and only then **Implement** (via `PatchOps`).

This architecture guarantees:
1.  **Safety**: No unapproved side-effects. All writes are atomic.
2.  **Auditability**: Every change is traced back to a persistent document and an approval record.
3.  **Resilience**: Crash-safe execution with automated recovery scanning.

## 🧠 Brain Features (Phase 14+)

The IDE allows you to connect an LLM (OpenAI, Gemini, Ollama) to act as the "Brain".
- **Think & Plan**: Type a high-level intent (e.g., "Add a user login system"), and the Agent will generate a structured Planning Proposal (`DocOps`).
- **Constraint Enforcement**: The AI is strictly prompted to follow "Small Phase" rules (max 3 files, 200 LOC per phase), preventing massive, risky rewrites.

## 🏗️ Architecture

The system is layered for maximum separation of concerns:

-   **Tools (`app/tools/`)**: Pure side-effect modules (e.g., `doc_writer.py`, `atomic_fs.py`). These are the *only* modules allowed to touch the filesystem.
-   **Runtime (`app/runtime/`)**: Logic layer that handles validation, schemas, and gate enforcement.
-   **State (`app/state/`)**: Manages the persistent project state (`project_state.json`) and artifacts (`.agent_ide/artifacts/`).
-   **Orchestration (`app/orchestration/`)**: LangGraph-based engine that routes intents and assembles proposals.
-   **Config (`app/config/`)**: Typed settings via `.env`.

## 🛠️ Installation

### Prerequisites
-   Python 3.10+
-   `pip`

### Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/agent-ide.git
    cd agent-ide
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure `gradio`, `pydantic`, `pydantic-settings`, `langgraph`, `openai`, `google-generativeai` are installed)*

3.  **Configure Environment**:
    Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to set your preferences:
    ```ini
    # Workspace
    WORKSPACE_ROOT_DEFAULT="./my_project_workspace"

    # LLM Provider (openai | gemini | ollama)
    LLM_PROVIDER="openai"

    # Keys
    OPENAI_API_KEY="sk-..."
    GEMINI_API_KEY="AIza..."
    ```

## 🚦 Usage

1.  **Launch the IDE**:
    ```bash
    python app/main.py
    ```
    Access the UI at `http://127.0.0.1:7860`.

2.  **The Workflow**:
    -   **Step 1: Bootstrap**: Click "Bootstrap Workspace" to initialize the folder structure.
    -   **Step 2: Intent**: Type your goal in the "Agent Intent" box (e.g., "Create a README for my new project").
    -   **Step 3: Plan**: Click "🧠 Think & Plan". The AI will generate a `DocOps` proposal.
    -   **Step 4: Approve (Gate A)**: Review the plan in the "Proposal Payload" view. Click "✅ Approve". The documents will be written.
    -   **Step 5: Implement**: Type "Implement the code based on the approved docs". The AI will generate a `PatchOps` proposal.
    -   **Step 6: Approve (Gate B)**: Review the code diffs. Click "✅ Approve". The code will be applied atomically.

## 🛡️ Safety Mechanisms

-   **Archive-First**: Rewriting a document *always* moves the old version to `documents/_archive/` with a timestamp.
-   **Atomic Writes**: Code patches are applied using a `temp -> fsync -> rename` strategy to prevent partial corruption.
-   **Recovery Scan**: On startup, the system scans for leftover `.tmp` or `.bak` files from crashed transactions and prompts for cleanup.

## 🤝 Contributing

This project is built using its own strictly defined "Phases" (see `documents/PHASES/`). To contribute, please follow the **Document-First** protocol: propose a `Phase Doc` before submitting a `Patch`.
