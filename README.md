
# Agentic Workspace - Phase 2 (Document Analysis & Robustness Core)

An extensible, agentic web application designed to handle unstructured multi-input analysis, orchestrate task-specific tools, manage conversation state, and securely parse uploaded files (PDF, DOCX, CSV). This platform is built using **FastAPI** for the backend engine and integrates with Google’s official **`google-genai` SDK** (configured for `gemini-3.1-flash-lite`).

---

## 1. Feature Map vs. Evaluation Rubric

This implementation is structured directly around the assignment evaluation criteria:

- **Autonomy & Planning (20 Points)**: The agent planner inspects both incoming files and text queries, decides whether more context is required, and dynamically routes to the appropriate tool using structured JSON mode.
- **Robustness & Error Handling (15 Points)**:
  - *Automatic Retry Engine*: Implements exponential backoff retries to handle `429 RESOURCE_EXHAUSTED` rate limits gracefully.
  - *Graceful Document Degradation*: Parser exceptions (such as corrupted files, old `.doc` formats, or structural issues) are caught safely. The server remains online, logging the error and informing the user gracefully instead of returning an HTTP 500 crash.
  - *OCR Fallback*: If programmatic PDF parsing returns empty text (e.g. scanned documents), the system falls back to Gemini's native document processing to extract the text using vision.
- **Explainability (10 Points)**: Every action displays the agent's step-by-step reasoning trail and tool trace inside a dedicated UI logging panel.
- **UX & Conversational Memory (10 Points)**: Features a responsive ChatGPT-style interface that maintains rolling conversational history, allowing natural follow-up questions to resolve pronouns and ellipsis contextually.

---

## 2. Project Directory Structure

```text
MM-Agent/
├── app/
│   ├── config.py           # Configuration and environment loaders
│   ├── main.py             # FastAPI multipart form endpoints & UI routes
│   ├── agent/
│   │   ├── planner.py      # Conversation-aware intent & planning loop
│   │   └── executor.py     # Context-aware tool execution pipeline
│   ├── templates/
│   │   └── index.html      # Responsive ChatGPT-style frontend UI
│   ├── utils/
│   │   ├── extractor.py    # Robust text & table extractor (PDF, DOCX, CSV)
│   │   └── retry.py        # Exponential backoff auto-retry wrapper
│   └── tools/
│       ├── base.py         # Abstract base classes for custom tools
│       ├── registry.py     # Self-initializing tool registry singleton
│       └── text_tools.py   # Context-aware text tools (Conversational, Summarize, etc.)
├── .env                    # Environment variables (ignored by Git)
├── .gitignore              # Git ignore rules
├── requirements.txt        # Backend dependencies
└── README.md               # System documentation
```

---

## 3. Installed Core Tools

1. **Conversational Answering (`conversational_answering`)**
   - *Context-Aware*: Receives conversation history to handle follow-up queries naturally.
2. **Summarization (`summarization`)**
   - *Strict Format*: Outputs exactly a 1-line summary, 3 bullet points, and a 5-sentence paragraph.
3. **Sentiment Analysis (`sentiment_analysis`)**
   - *Output*: Provides a sentiment classification label, confidence score, and one-line justification.
4. **Code Explanation (`code_explanation`)**
   - *Output*: Identifies syntax, explains functionality, checks for vulnerabilities, and outlines Big O complexity.

---

## 4. Setup & Installation

### Prerequisites
- **Python**: Version `3.10`
- **Gemini API Key**: Generated from Google AI Studio.

### Step 1: Virtual Environment Preparation
Create and activate a clean virtual environment:

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
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the root folder of the project:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

---

## 5. Running the Application

To start the server and automatically launch the UI:
```bash
uvicorn app.main:app --reload
```
Once initialized, your default web browser will automatically open to **`http://127.0.0.1:8000`**.

---

## 6. Verification and Verification Scenarios

### Test Scenario A: Conversational Memory & Pronoun Resolution
1. **Input**: `"Who was the first person to walk on the moon?"`
2. **Output**: Neil Armstrong.
3. **Input**: `"Who was the second?"`
4. **Output**: Buzz Aldrin. (Verifies that both the planner and tool correctly utilize history context to resolve ellipsis references).

### Test Scenario B: Document Upload & Native Parsing
(**Note**: The doc/docx files require more testing)
1. **Action**: Attach a compliant `.pdf`, `.docx`, or `.csv` file using the paperclip icon.
2. **Input**: `"Summarize this paper in short."`
3. **Output**: The right sidebar logs the parsing trace, and the summary displays in the main chat.