# My PDF Buddy

A React + FastAPI PDF RAG chatbot. This package intentionally excludes the Streamlit frontend.

## Project structure

- `frontend/` - React/Vite frontend with HTML, CSS, and JavaScript/JSX
- `api.py` - FastAPI API bridge
- `rag_pipeline.py` - PDF extraction, chunking, local embeddings, ChromaDB retrieval, and Groq generation

## Requirements

- Python 3.10+
- Node.js 18+
- A Groq API key

## Backend setup

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GROQ_API_KEY`. Do not commit `.env` or expose the key publicly.

Start the API:

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```

## Frontend setup

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend uses these API routes:

- `GET /api/health`
- `GET /api/documents`
- `POST /api/documents`
- `DELETE /api/documents`
- `POST /api/chat`

Indexed ChromaDB data is stored locally in `data/chroma/`, which is intentionally ignored by Git.
