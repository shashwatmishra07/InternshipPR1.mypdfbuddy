# InternshipPR1.mypdfbuddy
================================================================================
PROJECT SUBMISSION REPORT: DOCUMENT Q&A ASSISTANT (RAG PIPELINE)
================================================================================

Student Name / Roll No : [Your Name / Roll No]
Project Title          : Document Q&A Assistant
Course / Subject       : [Subject Name / Code]
Repository Link        : [Paste your GitHub Repository URL here]
Submission Target      : Instructor Evaluation Google Form


--------------------------------------------------------------------------------
1. PROJECT OVERVIEW
--------------------------------------------------------------------------------
This project is a full-stack Retrieval-Augmented Generation (RAG) system 
designed to allow users to ask natural-language questions over contextual 
documents and receive grounded, factual answers.

The application couples a fast, modern React single-page frontend with an 
asynchronous Python FastAPI backend that manages document chunking, vector 
embeddings, and similarity search.


--------------------------------------------------------------------------------
2. TECH STACK
--------------------------------------------------------------------------------
- Frontend:
    * React
    * Vite
    * CSS3
- Backend:
    * Python 3
    * FastAPI
    * Uvicorn (ASGI web server)
- Pipeline & Retrieval:
    * Custom document chunking and vector indexing (rag_pipeline.py)
    * Language model integration for contextual answer generation
- Environment & Dependency Management:
    * python-dotenv
    * pip (requirements.txt)
    * npm (frontend/package.json)


--------------------------------------------------------------------------------
3. SYSTEM ARCHITECTURE & WORKFLOW
--------------------------------------------------------------------------------
The complete query lifecycle operates through five core stages:

1. Ingestion & Indexing:
   - Target documents are ingested and divided into manageable text chunks.
   - Text chunks are converted into dense vector embeddings and indexed 
     inside the retrieval pipeline (rag_pipeline.py).

2. User Query:
   - The user enters a question into the React interface.
   - The frontend issues an asynchronous HTTP POST request to the backend.

3. Context Retrieval:
   - FastAPI receives the request in api.py and passes the query to the 
     RAG engine.
   - The vector search identifies the top matching chunks based on semantic 
     similarity.

4. Augmented Generation:
   - The user query and the retrieved context passages are assembled into a 
     structured prompt.
   - The model generates an answer strictly constrained by the provided source 
     context.

5. Response Delivery:
   - The backend delivers the answer payload via JSON back to the React UI.
   - The frontend renders the response cleanly for the user.


--------------------------------------------------------------------------------
4. REPOSITORY STRUCTURE
--------------------------------------------------------------------------------
my-pdf-buddy/
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React application logic and UI state
│   │   └── styles.css        # Clean custom styles
│   ├── index.html            # Frontend entry layout
│   ├── package.json          # Node dependencies and scripts
│   └── vite.config.js        # Vite bundler configuration
├── .env.example              # Template for required environment variables
├── .gitignore                # Exclusion rules for git tracking
├── api.py                    # FastAPI server routes and endpoints
├── rag_pipeline.py           # Core text processing, embeddings, and retrieval
├── requirements.txt          # Python dependencies
└── README.md                 # Humanized repository summary and setup guide


--------------------------------------------------------------------------------
5. LOCAL SETUP AND INSTALLATION GUIDE
--------------------------------------------------------------------------------

A. Backend Setup (FastAPI):
   1. Open a terminal in the root project folder.
   2. Create a virtual environment:
      python -m venv venv

   3. Activate the virtual environment:
      - Windows:
        venv\Scripts\activate
      - macOS / Linux:
        source venv/bin/activate

   4. Install dependencies:
      pip install -r requirements.txt

   5. Setup environment variables:
      cp .env.example .env
      (Open .env in any editor and insert your API keys)

   6. Start the backend server:
      uvicorn api:app --reload

   The API will be available at: http://localhost:8000

B. Frontend Setup (React / Vite):
   1. Open a second terminal window and navigate to the frontend folder:
      cd frontend

   2. Install frontend packages:
      npm install

   3. Run the development server:
      npm run dev

   The user interface will be available at: http://localhost:5173


--------------------------------------------------------------------------------
6. PRE-SUBMISSION CHECKLIST FOR GOOGLE FORM
--------------------------------------------------------------------------------
[ ] 1. Repository Visibility: Set to Public on GitHub so the teacher can view 
       and clone it without needing permission requests.
[ ] 2. Secrets Protected: Ensure .env is NOT tracked or pushed to Git. Only 
       .env.example with placeholder names should be visible.
[ ] 3. Clean Tree: Ensure venv/, __pycache__/, and frontend/node_modules/ are 
       ignored via .gitignore.
[ ] 4. Tested Execution: Verified that both `uvicorn api:app --reload` and 
       `npm run dev` start without missing dependency errors.
[ ] 5. Direct Link: Ensure you copy the main repository URL 
       (e.g., https://github.com/your-username/my-pdf-buddy) for the Google Form.

================================================================================
                              END OF DOCUMENT
================================================================================
