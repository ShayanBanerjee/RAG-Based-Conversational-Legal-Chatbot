# ⚖️ Bharat Law Bot – RAG-Based Conversational Legal Chatbot (India)

A **Retrieval-Augmented Generation (RAG)**–based chatbot that explains **Indian law** in simple language.

It uses:

- **Flask** as the backend API (serving both the chatbot and the built frontend)
- **React + Vite** as a modern Microsoft Copilot–style UI
- **LangChain + Pinecone + OpenAI** for retrieval + answer generation
- **Sentence Transformers** for embeddings

---

## 🧱 Architecture Overview

```text
.
├── app.py                  # Flask app (serves API + built React)
├── setup.py                # Python package config
├── requirements.txt        # Uses "-e ." to install this package
├── .env                    # Secrets (OpenAI, Pinecone, etc.)
├── store_index.py          # Ingest PDF data to Pinecone
├── data/                   # Your legal PDFs go here
├── src/
│   ├── helper.py           # Embedding, Pinecone, utility functions
│   ├── prompt.py           # System prompt for Bharat Law Bot
│   └── ...                 # Other Python modules
└── frontend/
    ├── index.html
    ├── vite.config.js      # Vite dev server + proxy config
    ├── package.json
    └── src/
        ├── main.jsx        # React entrypoint
        ├── App.jsx         # Main chat UI
        ├── App.css         # Copilot-style theming
        └── components/
            ├── ChatMessage.jsx
            └── SuggestionChips.jsx
```

---

## 🧩 Tech Stack

- **Backend**: Flask, LangChain, Pinecone, OpenAI
- **Frontend**: React + Vite
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: Pinecone index (`INDEX_NAME`)
- **Deployment**: Can run locally or via Docker / AWS EC2 + ECR + GitHub Actions

---

## 🔧 Backend Setup (Flask + LangChain + Pinecone)

### 1. Clone the repo

```bash
git clone https://github.com/ShayanBanerjee/RAG-Based-Conversational-Legal-Chatbot.git
cd RAG-Based-Conversational-Legal-Chatbot
```

### 2. Create & activate a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows (PowerShell/CMD)
```

### 3. Install backend dependencies

`requirements.txt` contains `-e .`, so it will use `setup.py`:

```bash
pip install -r requirements.txt
```

This installs:

- `flask`, `flask-cors`
- `langchain`, `langchain-pinecone`, `langchain-openai`, `langchain-community`
- `sentence-transformers`, `pypdf`, `python-dotenv`
- and the local package `rag_legal_chatbot` (from `src/`)

### 4. Environment variables (`.env`)

Create a `.env` file at the project root:

```ini
PINECONE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
INDEX_NAME=legal-chatbot       # or your actual Pinecone index name
```

The backend uses `load_dotenv()` in `app.py` to load these.

### 5. Load your legal data & build the Pinecone index

1. Put your PDFs inside the `data/` folder.
2. Run the embedding/indexing script:

```bash
python store_index.py
```

This will:

- Read PDFs from `data/`
- Create embeddings with `sentence-transformers/all-MiniLM-L6-v2`
- Upload to the Pinecone index (`INDEX_NAME`)

---

## 🎨 Frontend Setup (React + Vite)

### 1. Init / install frontend dependencies

From the project root:

```bash
cd frontend
npm install
```

If you haven’t created the Vite app earlier, it should already exist as part of this repo. If you ever need to recreate:

```bash
npm create vite@latest frontend -- --template react
```

Then bring back `src/App.jsx`, `src/main.jsx`, `src/App.css`, etc. as per this project.

### 2. Important frontend files

#### `frontend/vite.config.js` (with dev proxy)

For local development with the Flask server running on `http://localhost:8080`, use a proxy:

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
      },
      "/get": {
        target: "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
});
```

This means:

- React dev server runs at `http://localhost:5173`
- API calls to `/api/...` and `/get?...` are forwarded to Flask at `http://localhost:8080`

---

## ▶️ Running in Development (Two-Process Dev)

1. **Start the Flask backend** in one terminal:

   ```bash
   cd RAG-Based-Conversational-Legal-Chatbot
   source .venv/bin/activate
   python app.py
   ```

   This serves:
   - `http://localhost:8080/api/chat`
   - `http://localhost:8080/get`

2. **Start the React dev server** in another terminal:

   ```bash
   cd RAG-Based-Conversational-Legal-Chatbot/frontend
   npm run dev
   ```

3. Open:

   ```text
   http://localhost:5173
   ```

The React app will show the Copilot-style **Bharat Law Bot** UI and talk to Flask via the `/api/chat` proxy.

---

## 🏗️ Building & Serving Frontend with Flask (Production-style)

Once you are happy with the UI:

### 1. Build the React app

```bash
cd frontend
npm run build
cd ..
```

This creates `frontend/dist/` with:

- `index.html`
- `assets/` (JS, CSS, etc.)

### 2. Flask `app.py` serving the built frontend

Your `app.py` is configured like:

```python
app = Flask(
    __name__,
    static_folder="frontend/dist/assets",
    static_url_path="/assets",
    template_folder="frontend/dist",
)

@app.route("/")
def serve_react_index():
    return render_template("index.html")
```

So when you run:

```bash
python app.py
```

You can directly open:

```text
http://localhost:8080
```

Flask will:

- Serve `frontend/dist/index.html` at `/`
- Serve JS/CSS from `/assets/...`
- Expose APIs under:
  - `POST /api/chat`
  - `GET  /get?msg=...`

No dev proxy needed in production; everything is on port 8080.

---

## 💬 API Endpoints

### `POST /api/chat`

**Request body:**

```json
{
  "message": "What are my rights as a tenant in India?"
}
```

**Response:**

```json
{
  "response": "In general, tenants in India are protected under..."
}
```

### `GET /get?msg=...` (legacy)

```bash
curl "http://localhost:8080/get?msg=What%20are%20my%20tenant%20rights"
```

Response:

```json
{ "response": "..." }
```

---

## 📘 System Prompt (Bharat Law Bot)

`src/prompt.py` contains a **detailed system prompt** that:

- Sets the persona: *“Bharat Law Bot – India’s Legal Help Chatbot”*
- Ensures:
  - Clear headings & bullet-based structure
  - Distinction between **general info** and **case-like / defence-oriented** analysis
  - Strong **disclaimers**: this is general information, not personalised legal advice
- Forces the model to rely on the retrieved `{context}` and avoid hallucination

You can tweak `prompt.py` to adjust style and strictness.

---

## ⚠️ Legal Disclaimer

Bharat Law Bot provides **general legal information for Indian law**, based on the ingested documents and model outputs.  

It **does not**:

- Replace a **qualified advocate**,
- Provide **personalised legal advice**,
- Predict or guarantee case outcomes.

For specific cases, always consult a practising lawyer with all documents and facts.

---

## ☁️ AWS CI/CD Deployment with GitHub Actions (Optional)

The repo can be deployed via **AWS EC2 + ECR + GitHub Actions**.

High-level steps:

1. **Login to AWS console**.
2. **Create IAM user** with:
   - `AmazonEC2FullAccess`
   - `AmazonEC2ContainerRegistryFullAccess`
3. **Create ECR repo** (e.g. `680528876031.dkr.ecr.eu-north-1.amazonaws.com/legalchatbot`).
4. **Create EC2 (Ubuntu)** instance, install Docker:

   ```bash
   sudo apt-get update -y
   sudo apt-get upgrade -y
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   newgrp docker
   ```

5. **Configure EC2 as a self-hosted GitHub Actions runner**:
   - Repo → Settings → Actions → Runners → New self-hosted runner (Linux)
   - Follow GitHub’s commands (`config.sh`, `run.sh`).

6. **Open port 8080** in the EC2 security group (Custom TCP 8080, source `0.0.0.0/0`).

7. **GitHub Secrets** for CI/CD:

   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`
   - `ECR_REPO`
   - `PINECONE_API_KEY`
   - `OPENAI_API_KEY`

    For backend:
    - `ECR_REPO_BACKEND (e.g. bharatlawbot-backend)`

    For frontend:
    - `ECR_REPO_FRONTEND (e.g. bharatlawbot-frontend)`

8. The GitHub Actions workflow can:
   - Build Docker image
   - Push to ECR
   - SSH / trigger pull + run on EC2

---

## 📄 License

MIT License © 2025 Shayan Banerjee

Feel free to fork, extend, and adapt for other jurisdictions and use-cases.
