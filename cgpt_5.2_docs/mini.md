Your earlier “wonderful stack” is overkill for what you just described. If the goal is **(a) upload example files**, **(b) shove their text into the prompt**, **(c) get a response**, **(d) extract code/doc blocks**, **(e) save them as files** — you can do that in a single Gradio app with ~150 lines of Python.

The only real “gotchas” are:

* You must **limit how much example text** you inject (or you’ll drown the real question and blow context).
* Your “extract code” needs deterministic rules (or you’ll save garbage).

Below are three architectures (pick one mentally; you can implement any quickly):

## Option 1 (simple + robust): “Examples are prompt prefix”

* Upload N files (txt/md/py/json/etc)
* Read them as text, wrap each with a label + fence
* Prepend into the user’s request as: `### EXAMPLE FILE: name.ext\n```...\n````
* Call OpenAI
* Parse assistant output:

  * fenced code blocks -> `out/<index>_<lang>.<ext>`
  * `# File: path` markers -> exact filenames if present
  * everything else -> `out/response.md`

## Option 2 (cleaner output): enforce “file manifest” protocol

You tell the model to output in a strict template:

````
# File: src/foo.py
```python
...
````

# File: README.md

```md
...
```

````

This massively improves extraction accuracy. If you don’t do this, you’ll get random prose and half-formed blocks.

## Option 3 (best long-term): store examples in a mini “library”
You upload examples once, they persist on disk, you choose which ones to inject each run.
Same parsing, just better UX.

---

# Minimal Gradio app (uploads examples + saves extracted files)

This is the “Option 2” implementation because it actually works reliably.

```python
import os
import re
import json
from pathlib import Path
import gradio as gr

# If you're using the new OpenAI python client:
from openai import OpenAI

client = OpenAI()  # expects OPENAI_API_KEY in env


# ---------- helpers

TEXT_EXTS = {".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css", ".csv", ".log"}

def read_file_text(filepath: str, max_chars: int = 80_000) -> str:
    """
    Read file as text with a simple fallback. Truncates to max_chars.
    """
    p = Path(filepath)
    data = p.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        # latin-1 fallback (lossy-ish but doesn't crash)
        text = data.decode("latin-1", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[TRUNCATED]"
    return text

def build_examples_prefix(files: list[str]) -> str:
    """
    Build a prompt prefix containing uploaded example file contents.
    """
    if not files:
        return ""

    chunks = []
    for f in files:
        p = Path(f)
        ext = p.suffix.lower()
        if ext not in TEXT_EXTS:
            # Skip non-text (pdf/docx/etc) in this simple version.
            continue
        content = read_file_text(f)
        # Wrap content in fences so the model doesn't "merge" it with instructions.
        chunks.append(
            f"### EXAMPLE FILE: {p.name}\n"
            f"```{ext.lstrip('.') if ext else ''}\n{content}\n```\n"
        )
    if not chunks:
        return ""
    return "## Provided Examples (reference only)\n" + "\n".join(chunks) + "\n"

def lang_to_ext(lang: str) -> str:
    lang = (lang or "").strip().lower()
    mapping = {
        "python": ".py",
        "py": ".py",
        "javascript": ".js",
        "js": ".js",
        "typescript": ".ts",
        "ts": ".ts",
        "json": ".json",
        "yaml": ".yml",
        "yml": ".yml",
        "html": ".html",
        "css": ".css",
        "markdown": ".md",
        "md": ".md",
        "bash": ".sh",
        "sh": ".sh",
        "text": ".txt",
        "txt": ".txt",
    }
    return mapping.get(lang, ".txt")

FILE_HEADER_RE = re.compile(r"^\s*#\s*File:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
FENCE_RE = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)\n```", re.DOTALL)

def extract_files_from_response(resp: str):
    """
    Extraction rules (deterministic):
    1) If response uses '# File: path' headers followed by a fenced block, save with that path.
    2) Otherwise, save each fenced block as out/block_XX.ext
    3) Save full response as out/response.md always.
    """
    assets = []  # list of (relative_path, content)
    resp = resp.strip()

    # Always keep the full response
    assets.append(("response.md", resp + "\n"))

    # Try "File:" protocol
    file_headers = list(FILE_HEADER_RE.finditer(resp))
    if file_headers:
        for i, m in enumerate(file_headers):
            start = m.end()
            end = file_headers[i + 1].start() if i + 1 < len(file_headers) else len(resp)
            block_region = resp[start:end].strip()

            fence = FENCE_RE.search(block_region)
            if not fence:
                continue
            lang = fence.group(1)
            code = fence.group(2)

            rel_path = m.group(1).strip().lstrip("/").replace("\\", "/")
            # If user gave a directory, keep it.
            # If no extension, infer from lang.
            rp = Path(rel_path)
            if rp.suffix == "":
                rel_path = str(rp.with_suffix(lang_to_ext(lang)))
            assets.append((rel_path, code + "\n"))
        return assets

    # Otherwise, save all fenced blocks with synthetic names
    fences = list(FENCE_RE.finditer(resp))
    for idx, f in enumerate(fences, start=1):
        lang = f.group(1)
        code = f.group(2)
        ext = lang_to_ext(lang)
        assets.append((f"block_{idx:02d}{ext}", code + "\n"))

    return assets

def write_assets(out_dir: str, assets: list[tuple[str, str]]) -> list[str]:
    """
    Write extracted assets under out_dir. Returns list of actual filepaths.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []

    for rel, content in assets:
        rel = rel.strip().lstrip("/").replace("\\", "/")
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(str(path))
    return written


# ---------- OpenAI call

SYSTEM = """You are a software assistant.
When you want to output files, use this exact protocol:

# File: relative/path/filename.ext
```lang
...content...
````

You may output multiple files. Avoid extra chatter between files.
"""

def run(prompt: str, example_files, model: str = "gpt-4.1-mini", out_dir: str = "out"):
files = [f.name for f in (example_files or [])]  # gradio gives tempfile objects
examples_prefix = build_examples_prefix(files)

```
user_msg = f"{examples_prefix}\n## Task\n{prompt}".strip()

r = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_msg},
    ],
    temperature=0.2,
)

text = r.choices[0].message.content or ""
assets = extract_files_from_response(text)
written = write_assets(out_dir, assets)

# Show response + list of files created
file_list = "\n".join([f"- {Path(p).as_posix()}" for p in written])
summary = f"Saved files:\n{file_list}"
return text, summary
```

# ---------- UI

with gr.Blocks() as demo:
gr.Markdown("## Simple Examples → Prompt → Parse → Save")

```
with gr.Row():
    prompt = gr.Textbox(label="Task prompt", lines=8, placeholder="What do you want the model to do?")
    examples = gr.Files(label="Example files (text-based)", file_count="multiple")

with gr.Row():
    model = gr.Dropdown(
        label="Model",
        choices=["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
        value="gpt-4.1-mini",
    )
    out_dir = gr.Textbox(label="Output folder", value="out")

run_btn = gr.Button("Run")

response = gr.Textbox(label="Model response", lines=16)
saved = gr.Textbox(label="Saved file list", lines=10)

run_btn.click(fn=run, inputs=[prompt, examples, model, out_dir], outputs=[response, saved])
```

demo.launch()

```

---

## Critique of your ask (what’s under-specified / likely to bite you)
1) **“attachments”**: Gradio will give you file paths, but *PDF/DOCX need extraction*. If you expect those, your “simple” spec isn’t simple anymore. (Still doable, but it’s a different problem.)
2) **“extract code etc”**: “etc” is where projects die. Decide what you mean:
   - fenced code blocks only?
   - also `---` docs blocks?
   - JSON blobs?
   - inline `def foo():` without fences? (Don’t do this—force fences.)
3) **Filename mapping**: if you don’t enforce `# File:` protocol, you’ll end up with `block_01.txt` garbage and manual cleanup.

---

## Next branch (pick one to refine)
1) **Add PDF/DOCX support** (still fairly small): use `python-docx` for docx; pdf text extraction is messy but possible.
2) **Add a “prompt template” editor**: a textbox for system prompt + checkbox “enforce file protocol”.
3) **Add a file tree preview**: show the parsed filenames before writing, so you can reject nonsense.

One probing question that determines the next step: **Do you want the uploaded example files to be used as “reference context” (few-shot style), or as “inputs to transform” (the model must rewrite them and output new versions)?** That single choice changes the system prompt and the extraction rules.
```


Below is a **copy/pasteable mini-project**: a `README.md` plus a single `app.py` you can drop into a folder and run. It does exactly what you asked: upload example files in Gradio, inject them into the prompt, call OpenAI, then parse the response to extract code blocks into saved files.

---

## `README.md`

````markdown
# Gradio Example-Injection + Code Extraction Saver (OpenAI)

A tiny Gradio app that lets you:
1) Upload "example" text files (attachments)
2) Add a task prompt
3) Send both to an OpenAI chat completion call
4) Parse the model response to extract code/doc blocks
5) Save them as real files under an output folder

## What this is (and what it isn't)

✅ Simple: one `app.py`  
✅ Uses Gradio file uploads for examples  
✅ Enforces a reliable "File Manifest" protocol for deterministic extraction  
✅ Saves:
- `out/response.md` (full raw model response)
- Extracted files like `out/src/foo.py`, `out/README.md`, etc.

❌ Not included (by design):
- PDF/DOCX extraction
- Fancy file tree UI preview
- RAG / embeddings / vector store

You can add those later.

---

## Protocol (important)

The app instructs the model to output files like this:

# File: relative/path/filename.ext
```lang
...content...
````

If the model follows this, the saver writes exact files.

If the model does NOT follow it, the app falls back to saving fenced blocks as:

* `out/block_01.py`
* `out/block_02.md`
  etc.

---

## Setup

### 1) Create folder

```bash
mkdir gradio_examples_saver
cd gradio_examples_saver
```

### 2) Create a virtual env (recommended)

```bash
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows (powershell)
# .\.venv\Scripts\Activate.ps1
```

### 3) Install deps

```bash
pip install -U gradio openai
```

### 4) Set your OpenAI API key

mac/linux:

```bash
export OPENAI_API_KEY="YOUR_KEY"
```

windows (powershell):

```powershell
setx OPENAI_API_KEY "YOUR_KEY"
```

Restart your shell after `setx`.

---

## Run

```bash
python app.py
```

Gradio will print a local URL (typically [http://127.0.0.1:7860](http://127.0.0.1:7860)).

---

## Usage

1. Upload example files (txt/md/py/json/etc)
2. Enter your task prompt
3. Click "Run"
4. Check the output folder (default `out/`)

---

## Practical tips (so it actually works)

### Tip 1: Keep examples small

If you upload a giant log or massive codebase, you will drown the model and/or hit context limits.

### Tip 2: Use the manifest protocol for real file output

If you want "saveable" output, tell the model what you want: filenames + fences.
This app already enforces that via the system prompt.

### Tip 3: Make your prompt explicit

Bad: "help me with this"
Good: "Generate a Flask API with endpoints X/Y/Z. Output files using the protocol."

---

## Extending (deliberate next steps)

* Add PDF/DOCX extraction:

  * DOCX: python-docx
  * PDF: pypdf (text-only, imperfect)
* Add a preview of extracted filenames before writing
* Add a "max chars per file" slider and chunking

````

---

## `app.py`

```python
import os
import re
from pathlib import Path
import gradio as gr
from openai import OpenAI

# ----------------------------
# OpenAI client
# ----------------------------
client = OpenAI()  # reads OPENAI_API_KEY from environment


# ----------------------------
# Config
# ----------------------------
TEXT_EXTS = {
    ".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".html", ".css", ".csv", ".log"
}

SYSTEM_PROMPT = """You are a software assistant.

When you want to output files, you MUST use this exact protocol:

# File: relative/path/filename.ext
```lang
...content...
````

You may output multiple files.
Avoid extra chatter between files.
If you have no files to create, output a single markdown response.

Be consistent and deterministic.
"""

# ----------------------------

# Helpers: reading + prompt building

# ----------------------------

def read_file_text(filepath: str, max_chars: int = 80_000) -> str:
"""
Read file as text with safe fallbacks. Truncates to max_chars.
"""
p = Path(filepath)
data = p.read_bytes()
try:
text = data.decode("utf-8")
except UnicodeDecodeError:
text = data.decode("latin-1", errors="replace")
if len(text) > max_chars:
text = text[:max_chars] + "\n\n[TRUNCATED]"
return text

def build_examples_prefix(filepaths: list[str], max_files: int = 12) -> str:
"""
Builds a prefix that injects example files into the prompt.
Non-text files are skipped.
"""
if not filepaths:
return ""

````
chunks = []
for fp in filepaths[:max_files]:
    p = Path(fp)
    ext = p.suffix.lower()
    if ext not in TEXT_EXTS:
        continue

    content = read_file_text(fp)
    lang = ext.lstrip(".") if ext else ""

    chunks.append(
        f"### EXAMPLE FILE: {p.name}\n"
        f"```{lang}\n{content}\n```\n"
    )

if not chunks:
    return ""

return "## Provided Examples (reference only)\n" + "\n".join(chunks) + "\n"
````

# ----------------------------

# Helpers: extraction + saving

# ----------------------------

FILE_HEADER_RE = re.compile(r"^\s*#\s*File:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
FENCE_RE = re.compile(r"`([a-zA-Z0-9_-]*)\n(.*?)\n`", re.DOTALL)

def lang_to_ext(lang: str) -> str:
lang = (lang or "").strip().lower()
mapping = {
"python": ".py",
"py": ".py",
"javascript": ".js",
"js": ".js",
"typescript": ".ts",
"ts": ".ts",
"json": ".json",
"yaml": ".yml",
"yml": ".yml",
"html": ".html",
"css": ".css",
"markdown": ".md",
"md": ".md",
"bash": ".sh",
"sh": ".sh",
"text": ".txt",
"txt": ".txt",
}
return mapping.get(lang, ".txt")

def extract_assets(resp: str) -> list[tuple[str, str]]:
"""
Deterministic extraction rules:

````
Always save:
  - response.md (full text)

Preferred: "File Manifest" protocol
  # File: path
  ```lang
  content
  ```

Fallback:
  Save each fenced code block as block_XX.ext
"""
resp = (resp or "").strip()
assets: list[tuple[str, str]] = []
assets.append(("response.md", resp + "\n"))

headers = list(FILE_HEADER_RE.finditer(resp))
if headers:
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(resp)
        region = resp[start:end].strip()

        fence = FENCE_RE.search(region)
        if not fence:
            continue

        lang = fence.group(1)
        content = fence.group(2)

        rel_path = m.group(1).strip().lstrip("/").replace("\\", "/")
        rp = Path(rel_path)
        if rp.suffix == "":
            rel_path = str(rp.with_suffix(lang_to_ext(lang)))

        assets.append((rel_path, content + "\n"))

    return assets

# fallback: all fenced blocks
fences = list(FENCE_RE.finditer(resp))
for idx, f in enumerate(fences, start=1):
    lang = f.group(1)
    content = f.group(2)
    assets.append((f"block_{idx:02d}{lang_to_ext(lang)}", content + "\n"))

return assets
````

def write_assets(out_dir: str, assets: list[tuple[str, str]]) -> list[str]:
out = Path(out_dir)
out.mkdir(parents=True, exist_ok=True)

```
written = []
for rel, content in assets:
    rel = rel.strip().lstrip("/").replace("\\", "/")
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    written.append(str(path))
return written
```

# ----------------------------

# Main run function (Gradio handler)

# ----------------------------

def run(prompt: str, uploaded_files, model: str, out_dir: str, temperature: float):
# Convert Gradio uploaded file objects -> file paths
filepaths = []
if uploaded_files:
for f in uploaded_files:
# gr.Files returns objects with .name pointing to temp path
filepaths.append(f.name)

```
examples_prefix = build_examples_prefix(filepaths)

user_msg = f"{examples_prefix}\n## Task\n{prompt}".strip()

r = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ],
    temperature=float(temperature),
)

text = r.choices[0].message.content or ""
assets = extract_assets(text)
written = write_assets(out_dir, assets)

# Nice list for UI
written_pretty = "\n".join(f"- {Path(p).as_posix()}" for p in written)
return text, f"Saved files:\n{written_pretty}"
```

# ----------------------------

# Gradio UI

# ----------------------------

with gr.Blocks() as demo:
gr.Markdown("## Examples (Files) → Prompt → OpenAI → Extract → Save")

```
with gr.Row():
    prompt = gr.Textbox(
        label="Task prompt",
        lines=10,
        placeholder="Describe what you want. If you want file outputs, ask for them explicitly.",
    )
    examples = gr.Files(label="Example files (text only)", file_count="multiple")

with gr.Row():
    model = gr.Dropdown(
        label="Model",
        choices=["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
        value="gpt-4.1-mini",
    )
    out_dir = gr.Textbox(label="Output folder", value="out")

with gr.Row():
    temperature = gr.Slider(label="Temperature", minimum=0.0, maximum=1.0, value=0.2, step=0.05)
    run_btn = gr.Button("Run")

response = gr.Textbox(label="Model response", lines=18)
saved = gr.Textbox(label="Saved file list", lines=10)

run_btn.click(
    fn=run,
    inputs=[prompt, examples, model, out_dir, temperature],
    outputs=[response, saved],
)
```

demo.launch()

```

---

### Critique (so you don’t step on rakes)
- If you don’t **force a file protocol**, your extraction will be junk. This version forces it.
- If you inject huge files, the “examples” will dominate and your actual prompt gets ignored. This code truncates per file, but not per total; add a “total budget” later if needed.
- If you want PDFs/DOCX, you’re leaving “simple land.” Doable, but it’s a different complexity class.

---

### Next upgrade path (choose a direction)
1) **Zip export button**: after writing outputs, also create `out.zip` and offer it for download in Gradio.
2) **Preview extracted filenames before writing** (guardrail against hallucinated paths).
3) **PDF/DOCX ingestion** with `python-docx` and `pypdf`.

If you say “zip export,” I’ll drop in the exact code changes (minimal) to produce a downloadable zip artifact from Gradio.
```
