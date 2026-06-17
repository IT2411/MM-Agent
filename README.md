# Multi-Modal Agent Application - Phase 1 (Text Core)

A modular, agentic backend application designed to handle unstructured text queries, analyze user intent, run specialized processing tools, and enforce structured interaction behaviors (such as the mandatory follow-up rule for ambiguous requests). This phase is built with FastAPI and integrated with the modern Google `google-genai` SDK using the Gemini model family.

---

## Current Architecture & Design Decisions

- **FastAPI Backend**: Provides clean, structured API endpoints (`/api/chat` and `/health`) with automatic documentation via Swagger UI.
- **Orchestration & Planning**: Before executing any operations, the inputs are passed to a planner powered by `gemini-1.5-flash`. The planner evaluates user intent, identifies potential ambiguities, and either selects the best tool or asks for clarification.
- **Mandatory Follow-up Question Rule**: If a user submits raw text or code without clear intent, the agent pauses and returns a clarifying question instead of guessing.
- **Tool Registry Pattern**: Tools are decoupled from the agent execution core. New tools can be easily registered without modifying the runner logic.

---

## Prerequisites

- **Python**: Version `3.10` is recommended and supported.
- **Gemini API Key**: A valid API key from Google AI Studio.

---

## Installation & Setup

1. **Clone or navigate to the project directory**:
   ```bash
   cd MM-Agent
   ```

2. **Create a virtual environment using Python 3.10**:
   - **Windows**:
     ```bash
     py -3.10 -m venv .venv
     ```
   - **macOS / Linux**:
     ```bash
     python3.10 -m venv .venv
     ```

3. **Activate the virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Create a file named `.env` in the root folder (where this README is located) and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Running the Application

Start the local development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`. You can monitor log activity and potential reloads directly inside your terminal window.

---

## Verifying and Testing the APIs

You can interact with and test the agent directly using the interactive OpenAPI documentation:

👉 Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** in your browser.

### Test Payload Examples

#### 1. Clear Request (Sentiment Analysis Tool)
Sends clear instructions along with the content payload.
- **Endpoint**: `POST /api/chat`
- **Request Body**:
  ```json
  {
    "query": "Can you analyze the sentiment of this text?",
    "extracted_text": "I absolutely love how simple and straightforward this setup is! It works incredibly well."
  }
  ```

#### 2. Ambiguous Request (Triggers Mandatory Follow-up)
Sends code/text but leaves the target action unspecified.
- **Endpoint**: `POST /api/chat`
- **Request Body**:
  ```json
  {
    "query": "",
    "extracted_text": "def calculate_sum(a, b):\n    return a + b"
  }
  ```