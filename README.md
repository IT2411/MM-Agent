
# Multi-Modal Agentic Workspace

An extensible, agentic web application designed to analyze unstructured multi-input sources (Text, Documents, Images, Audio, and YouTube URLs), orchestrate task-specific tools, manage stateful conversation memory across turns, and execute complex multi-step reasoning chains.

Built using **FastAPI** for the backend engine and integrated with Google’s official, modern **`google-genai` SDK** (configured for `gemini-3.1-flash-lite`).

---

## 1. Project Directory Structure

```text
MM-Agent/
├── app/
│   ├── config.py           # Configuration and environment variable loaders
│   ├── main.py             # FastAPI multipart form endpoints & static UI routing
│   ├── agent/
│   │   ├── planner.py      # Conversation-aware intent evaluation & safeguard loop
│   │   └── executor.py     # Context-aware unified payload execution engine
│   ├── templates/
│   │   └── index.html      # Responsive ChatGPT-style HTML5/JS frontend UI
│   ├── utils/
│   │   ├── extractor.py    # Robust multimodal extractor (PDF, DOCX, CSV, TXT, Images, Audio)
│   │   └── retry.py        # Exponential backoff auto-retry wrapper (Robustness)
│   └── tools/
│       ├── base.py         # Abstract base class definitions
│       ├── registry.py     # Self-initializing tool registry singleton
│       └── text_tools.py   # Context-aware text tools (Conversational, Summarize, Sentiment, Code, YouTube)
├── .env                    # System secrets (ignored by Git)
├── .gitignore              # Git ignore rules
├── requirements.txt        # System requirements and library dependencies
└── README.md               # System documentation
```

---

## 2. Setup & Installation

### Step 1: Virtual Environment Preparation
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
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a file named `.env` in the root folder of the project:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

---

## 4. Running the Application

Start the local server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
Once Uvicorn compiles, the lifespan listener will print confirmation logs prints the link to the chat interface in ther terminal.
```bash
👉 Click here to open the Agentic Workspace: http://127.0.0.1:8000
```

---

## 5. Verification Scenarios & Test Cases

Verify your installation using the core scenarios defined in the guidelines:

### Test Case 1: Audio Transcription + Summary
- **Input**: Upload an `.mp3`, `.wav`, or `.m4a` file.
- **Query**: `"Summarize this audio."`
- **Output**: The summarization tool generates a structured summary with the precise calculated audio duration appended at the very end.

### Test Case 2: PDF + Natural Language Query (Action Items)
- **Input**: Upload `Meeting-Notes.pdf`.
- **Query**: `"What are the action items?"`
- **Output**: The planner bypasses the summary tool and routes directly to the conversational answering tool to extract and output **only** the list of action items.

### Test Case 3: Image with Code (OCR + Explanation)
- **Input**: Upload a screenshot of a code snippet (`code_snippet.png`).
- **Query**: `"Explain"`
- **Output**: The vision OCR extracts the text, detects Python, and outputs the detailed logic explanation, bug/vulnerability warnings, and time/space complexity.

### Test Case 4: Cross-Input Multi-Tool Chain (PDF with YouTube URL)
- **Input**: Upload a PDF containing a YouTube link.
- **Query**: `"Hit the YT URL in this PDF and give me a summary of it."`
- **Output**: The agent parses the PDF, extracts the YouTube URL, downloads the transcript via the YouTube tool, and programmatically dispatches the `SummarizeTool` to generate the strict 3-part summary.

### Test Case 5: Multi-File Unified Query (Audio + PDF Comparison)
- **Input**: Upload an audio file and a PDF resume.
- **Query**: `"Do the audio and the document discuss the same topic?"`
- **Output**: The agent transcribes the audio, extracts the PDF text, compares their semantic themes, and writes a detailed comparative analysis in English.

### Test Case 6: Mandatory Follow-Up Question (Ambiguity Handling)
- **Input**: Upload a document file with **no text query** in the box.
- **Output**: The programmatic check intercepts the request. The agent immediately outputs the mandatory follow-up question asking what you would like to do with the extracted content.
- **Follow-up**: Type *"summarize"* (without uploading the file again). The client automatically re-submits the retained text in the form, and the agent completes the summary successfully.

### Test Case 7: Image/PDF Text Extraction with OCR Confidence
- **Input**: Upload an image receipt.
- **Query**: `"Extract the text from this image."`
- **Output**: The agent transcribes the text and appends the estimated character OCR confidence rating.

### Test Case 8: Sentiment Analysis
- **Input**: Upload `feedback.txt`.
- **Query**: `"Analyze the sentiment of this feedback."`
- **Output**: The agent reads the text content and outputs the Sentiment Label, Confidence Score, and One-Line Justification in English.