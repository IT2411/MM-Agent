# Agentic Workspace - Phase 1 (Conversational Core)

An extensible, agentic web application designed to handle unstructured query analysis, orchestrate task-specific tools, and manage conversation state. This platform is built using **FastAPI** for the backend engine and integrates with Google’s official modern **`google-genai` SDK** (using `gemini-2.5-flash`).

The current phase establishes the core routing infrastructure, real-time thought tracing, dynamic client-side conversational memory, and a ChatGPT-style conversational user interface.

---

## 1. Project Directory Structure

```text
MM-Agent/
├── app/
│   ├── __init__.py
│   ├── config.py           # Environment variables & system configuration
│   ├── main.py             # FastAPI entrypoint & UI route definitions
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── planner.py      # Intent understanding & mandatory follow-up logic
│   │   └── executor.py     # Execution loop orchestration
│   ├── templates/
│   │   └── index.html      # Responsive ChatGPT-like frontend interface
│   └── tools/
│       ├── __init__.py
│       ├── base.py         # Abstract base classes for custom tools
│       ├── registry.py     # Central decoupled tool registration engine
│       └── text_tools.py   # Implementations of Phase 1 core text tools
├── .env                    # System secrets (ignored by Git)
├── .gitignore              # Files to exclude from version control
├── requirements.txt        # Backend dependencies
└── README.md               # System documentation
```

---

## 2. Core Architecture & System Flow

```text
                  +-----------------------------------+
                  |           Client UI               |
                  |  (Chat Feed + Real-time Logs)     |
                  +-----------------+-----------------+
                                    |
                       HTTP POST    |  (User query, optional context
                       /api/chat    |   & message history)
                                    v
                  +-----------------------------------+
                  |            FastAPI                |
                  |         (app/main.py)             |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |         Agent Executor            |
                  |      (app/agent/executor.py)      |
                  +-----------------+-----------------+
                                    |
                      Step 1: Plan  |  Step 2: Dispatch Tool
                      (LLM JSON)    v  (Dynamic Routing)
                +-------------------+-------------------+
                |                                       |
                v                                       v
    +-----------------------+               +-----------------------+
    |     Agent Planner     |               |     Tool Registry     |
    | (app/agent/planner.py)|               |(app/tools/registry.py)|
    +-----------------------+               +-----------+-----------+
                                                        |
                                                        v
                                            +-----------------------+
                                            |     Selected Tool     |
                                            | (app/tools/*tools.py) |
                                            +-----------------------+
```

### Key Architectural Concepts
- **Decoupled Tool Registry**: Tools inherit from a common `BaseTool` class. They self-describe their functionality via descriptions and register themselves. The planner reads these registration records at runtime to make routing decisions.
- **Intent Planning with JSON Output**: The agent core utilizes Gemini's native structured JSON mode to validate instructions. If the planner determines there is insufficient context to make a tool decision, it sets `is_clear: false` and stops to request clarification.
- **Conversational State Tracking**: Rolling history is preserved and sent back to the backend. This enables the agent to remember the subject of conversation when answering follow-up instructions (e.g., resolving commands like "now explain it" or "summarize that instead").

---

## 3. Installed Core Tools

1. **Conversational Answering (`conversational_answering`)**
   - *Description*: Handles general chats, pleasantries, or general knowledge questions.
2. **Summarization (`summarization`)**
   - *Description*: Processes long text and returns a strict 3-part layout: a 1-line summary, 3 key bullet points, and a 5-sentence paragraph.
3. **Sentiment Analysis (`sentiment_analysis`)**
   - *Description*: Examines the emotional tone of text, outputting a clear classification label, a confidence score (0.0 to 1.0), and a brief justification.
4. **Code Explanation (`code_explanation`)**
   - *Description*: Detects programming language, analyzes code functionality, checks for common bugs/vulnerabilities, and documents Big O complexity.

---

## 4. Setup & Installation

### Prerequisites
- **Python**: Version `3.10`
- **Gemini API Key**: From Google AI Studio.

### Step 1: Environment Preparation
Create and activate a clean virtual environment using Python 3.10:

- **Windows**:
  ```bash
  py -3.10 -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  python3.10 -m venv .venv
  source .venv/bin/activate
  ```

### Step 2: Install Dependencies
Upgrade pip and install the package requirements:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a file named `.env` in the root folder of the project:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## 5. Usage

To run the application locally:
```bash
uvicorn app.main:app --reload
```

### Auto-Launch Feature
FastAPI utilizes a lifespan context manager to launch your default browser to `http://127.0.0.1:8000` automatically once the server is ready. 

If the browser does not open automatically, navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 6. Verification and Testing Scenarios

Use the interface to verify the primary architectural features:

### Test Scenario A: Conversational Fallback
- **Input**: `"Who was the first person to walk on the moon?"`
- **Expected Behavior**: The right sidebar should show `Selected Tool: conversational_answering`. The response will print a friendly conversational output.

### Test Scenario B: Strict Tool Formatting
- **Input**: `"Summarize this text: [Paste article text here]"`
- **Expected Behavior**: The right sidebar shows `Selected Tool: summarization`. The response will match the required layout (1-line, 3 bullets, and exactly 5 sentences).

### Test Scenario C: Mandatory Follow-up & Memory
1. **First Input**: Paste a code snippet alone without commands (e.g., `def add(a, b): return a + b`).
2. **Expected Behavior**: The agent stops execution, registers `is_clear: false`, sets the selected tool to `None`, and asks: *"It looks like you've provided some code. What would you like me to do with it?"*
3. **Second Input**: Type *"Explain it to me"*.
4. **Expected Behavior**: The agent reads the conversation history, maps your instruction to the code snippet provided in step 1, dispatches the `code_explanation` tool, and outputs the code breakdown.