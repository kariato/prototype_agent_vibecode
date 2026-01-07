# Agent IDE User Guide

Welcome to the **Agent IDE**. This manual provides detailed instructions on how to use the system to build software safely and agentically.

---

## 🏗️ Philosophy: Document-First Development

The core philosophy of this IDE is: **"If it's not documented, it doesn't exist."**

Traditional coding agents often jump straight to `edit file`. This is dangerous. The Agent IDE forces a 2-step process:
1.  **Architecture Step (Gate A)**: The Agent proposes *documentation changes* (Plans, Specs, RFCs). You approve them.
2.  **Implementation Step (Gate B)**: The Agent proposes *code changes* that implement the approved docs. You approve them.

This ensures you are always in control of *what* is being built, not just debugging *how* it was built.

---

## 🚀 Getting Started

1.  **Start the Server**:
    Run `python app/main.py`. The UI will open at `http://localhost:7860`.

2.  **Bootstrap (First Time Only)**:
    If this is a new workspace, click the **"🚀 Bootstrap Workspace"** button in Local Panel 1. This creates the required `documents/` hierarchy.

---

## 🧠 Using the AI Brain

The "Brain" feature allows you to control the IDE with natural language.

1.  **Locate the Brain Panel**: Found in the "Approval & Intent" column.
2.  **Enter Intent**: Type a clear instruction.
    *   *Bad:* "Fix the bug."
    *   *Good:* "Investigate why the login page 500s and proposal a fix plan."
3.  **Click "🧠 Think & Plan"**:
    *   The Agent will parse your intent.
    *   It will check if you need a **Plan** (DocOps) or **Code** (PatchOps).
    *   *Note: The Agent is biased to ask for a Plan first.*

---

## 🛑 The Approval Gates

### Gate A: Document Operations (`DocOps`)
When the Agent proposes a document change (e.g., "Create Phase 2 Plan"), you will see:
-   **Type**: DOC
-   **Summary**: "Create phase 02 doc..."
-   **Payload**: A list of file actions.

**Action:**
-   Read the summary.
-   If it looks good, click **✅ Approve**.
-   **Result**: The file is written to `documents/`. If it overwrites a file, the old one is safely archived to `documents/_archive/`.

### Gate B: Code Operations (`PatchOps`)
When the Agent proposes code (e.g., "Implement login.py"), you will see:
-   **Type**: PATCH
-   **Diff View**: Click the "Diff View" tab in Panel 3 to see exactly what lines will change.

**Action:**
-   Review the diffs carefully.
-   If valid, click **✅ Approve**.
-   **Result**: The code is applied atomically. If the power goes out mid-write, your files remain consistent.

---

## 🕰️ Visual Timeline

Accidents happen. The **Visual Timeline** (Panel 4) keeps a permanent record of every event:
-   `PROPOSAL_CREATED`: Agent had an idea.
-   `APPROVAL_GRANTED`: You said "Yes".
-   `DOCOPS_EXECUTED`: A plan was saved.
-   `PATCH_COMMITTED`: Code was shipped.

Use this to trace back *why* a change was made.

---

## 🚨 Troubleshooting & Recovery

### "Recovery Required!" Alert
If the IDE crashes while writing files, you may see a red "Recovery Required!" alert on restart.
*   **What it means**: Leftover temporary files (`.tmp`, `.bak`) were found.
*   **What to do**:
    1.  Review the file list in the alert.
    2.  Click **"🗑️ Clean Up Artifacts"**.
    3.  The system will discard the partial write and restore consistency.

### "Forbidden Path" Error
The Agent is strictly sandboxed. It cannot write to:
-   Your system root (`/`)
-   Outside the workspace
-   Hidden configuration files (`.env`, `.agent_ide/`)

If you see this error, it means the Agent tried to do something unsafe and was blocked.

---

## 🔧 Configuration Reference

Edit your `.env` file to tune behavior:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `openai`, `gemini`, or `ollama` | `openai` |
| `OPENAI_MODEL` | specific model tag | `gpt-4o` |
| `GEMINI_MODEL` | specific model tag | `gemini-1.5-pro-002` |
| `OLLAMA_BASE_URL` | URL for local inference | `http://localhost:11434` |
| `WORKSPACE_ROOT_DEFAULT` | Path to your project files | `./workspace` |

---

**Happy Coding!**
