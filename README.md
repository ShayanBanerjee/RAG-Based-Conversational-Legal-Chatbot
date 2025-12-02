# ⚖️ Bharat Law Bot – RAG-Based Conversational Legal Chatbot (India)

A **Retrieval-Augmented Generation (RAG)**–based chatbot that explains **Indian law** in simple language.

It uses:

- **Flask** as the backend API (serving both the chatbot and the built frontend)
- **React + Vite** as a modern Microsoft Copilot–style UI
- **LangChain + Pinecone + OpenAI** for retrieval + answer generation
- **Sentence Transformers** for embeddings
- A **single Docker image** that bundles both frontend + backend for easy CI/CD on AWS EC2

---

## 🧱 Architecture Overview

```text
.
├── app.py                  # Flask app (serves API + built React)
├── Dockerfile              # Builds frontend + backend into one container
├── setup.py                # Python package config
├── requirements.txt        # Uses "-e ." to install this package
├── .env                    # Secrets (OpenAI, Pinecone, etc.) for local dev
├── store_index.py          # Ingest PDF data to Pinecone
├── data/                   # Your legal PDFs go here
├── src/
│   ├── helper.py           # Embedding, Pinecone, utility functions
│   ├── prompt.py           # System prompt for Bharat Law Bot
│   └── ...                 # Other Python modules
├── frontend/
│   ├── index.html
│   ├── vite.config.js      # Vite dev server + proxy config
│   ├── package.json
│   └── src/
│       ├── main.jsx        # React entrypoint
│       ├── App.jsx         # Main chat UI
│       ├── App.css         # Copilot-style theming
│       └── components/
│           ├── ChatMessage.jsx
│           └── SuggestionChips.jsx
└── .github/
    └── workflows/
        └── cicd.yaml       # Single CI/CD pipeline (Docker + EC2)
```

---

## 🧩 Tech Stack

- **Backend**: Flask, LangChain, Pinecone, OpenAI
- **Frontend**: React + Vite (Copilot-style UI)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: Pinecone index (`INDEX_NAME`)
- **Deployment**: Single Docker image via AWS ECR + EC2 + GitHub Actions

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
# .venv\Scriptsctivate       # Windows (PowerShell/CMD)
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

### 4. Environment variables (`.env`) – local development

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

### 1. Install frontend dependencies

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

### 2. Dev-time proxy (Vite → Flask)

`frontend/vite.config.js` configures a proxy so that during development:

- React dev server runs at `http://localhost:5173`
- API calls to `/api/...` and `/get?...` are forwarded to Flask at `http://localhost:8080`

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

3. Open in your browser:

   ```text
   http://localhost:5173
   ```

The React app will show the Copilot-style **Bharat Law Bot** UI and talk to Flask via the `/api/chat` proxy.

---

## 🏗️ Production Build & Serving via Flask (without Docker)

Once you are happy with the UI, you can build the frontend and let Flask serve the static files:

```bash
cd frontend
npm run build
cd ..
```

This creates `frontend/dist/` with:

- `index.html`
- `assets/` (JS, CSS, etc.)

`app.py` is configured like:

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

---

## 🐳 Docker – Single Image (Frontend + Backend)

For production, Bharat Law Bot is packaged as a **single Docker image** that:

- Builds the React/Vite frontend in a Node stage.
- Copies the build output into the Python/Flask image.
- Runs `app.py` which serves both the UI and the `/api/chat` endpoint.

### Dockerfile (root of repo)

```dockerfile
# Stage 1: Build React (Vite) frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy rest of frontend source and build
COPY frontend/ .
RUN npm run build

# Stage 2: Python + Flask backend (serves built frontend)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (adjust if you need more)
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential   && rm -rf /var/lib/apt/lists/*

# Copy entire project (Python code, app.py, src/, requirements.txt, etc.)
COPY . .

# Overwrite / ensure we have the fresh built frontend dist from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Install Python dependencies (requirements.txt uses "-e ." -> setup.py)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Flask will listen on port 8080 inside the container
EXPOSE 8080

# Make sure app.py runs on host="0.0.0.0", port=8080
CMD ["python", "app.py"]
```

> Note: `app.py` should contain something like:
>
> ```python
> if __name__ == "__main__":
>     app.run(host="0.0.0.0", port=8080, debug=False)
> ```

### Build & run locally via Docker

```bash
# From repo root
docker build -t bharatlawbot:latest .

# Map host port 80 to container port 8080
docker run -d --name bharatlawbot   -e PINECONE_API_KEY=...   -e OPENAI_API_KEY=...   -e INDEX_NAME=legal-chatbot   -p 80:8080   bharatlawbot:latest
```

Then open:

```text
http://localhost/
```

The same container serves both the **UI** and the **/api/chat** endpoint.

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

## ☁️ CI/CD on AWS EC2 with GitHub Actions (Single Image)

The project includes a GitHub Actions workflow at:

```text
.github/workflows/cicd.yaml
```

It performs:

1. **CI (build + push)**
2. **CD (pull + run on EC2 self-hosted runner)**

### 1. Prerequisites

- **AWS ECR** repository, e.g.:  
  `680528876031.dkr.ecr.eu-north-1.amazonaws.com/legalchatbot`  
  (repo name: `legalchatbot`)
- **EC2 (Ubuntu)** instance with:
  - Docker installed
  - Open **port 80** in its security group (HTTP from `0.0.0.0/0` or your IP)
  - Configured as a **self-hosted GitHub Actions runner** for this repo

On EC2 (once):

```bash
sudo apt-get update -y
sudo apt-get upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker
```

### 2. GitHub Secrets

Add these in **Repo → Settings → Secrets and variables → Actions**:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` → e.g. `eu-north-1`
- `ECR_REPO` → `legalchatbot`  (just the repo name)
- `PINECONE_API_KEY`
- `OPENAI_API_KEY`
- `INDEX_NAME` → `legal-chatbot` (or your actual index name)

### 3. Workflow: `.github/workflows/cicd.yaml`

```yaml
name: CI/CD - Bharat Law Bot (Single Image)

on:
  push:
    branches: [ main ]

jobs:
  build-and-push:
    name: Build & Push Docker Image to ECR
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_DEFAULT_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to Amazon ECR
        id: build-image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: ${{ secrets.ECR_REPO }}   # legalchatbot
          IMAGE_TAG: latest
        run: |
          echo "Building image $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
          docker build -t "$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" .
          docker push "$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> "$GITHUB_OUTPUT"

  deploy:
    name: Deploy to EC2 (self-hosted runner)
    needs: build-and-push
    runs-on: self-hosted

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_DEFAULT_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Pull and run Docker container
        shell: bash
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: ${{ secrets.ECR_REPO }}
          IMAGE_TAG: latest
        run: |
          IMAGE="$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

          echo "Pulling image $IMAGE"
          docker pull "$IMAGE"

          echo "Stopping old container if running..."
          docker stop bharatlawbot || echo "No existing container to stop"

          echo "Removing old container if present..."
          docker rm bharatlawbot || echo "No existing container to remove"

          echo "Starting new container..."
          docker run -d --name bharatlawbot             -e AWS_ACCESS_KEY_ID="${{ secrets.AWS_ACCESS_KEY_ID }}"             -e AWS_SECRET_ACCESS_KEY="${{ secrets.AWS_SECRET_ACCESS_KEY }}"             -e AWS_DEFAULT_REGION="${{ secrets.AWS_DEFAULT_REGION }}"             -e PINECONE_API_KEY="${{ secrets.PINECONE_API_KEY }}"             -e OPENAI_API_KEY="${{ secrets.OPENAI_API_KEY }}"             -e INDEX_NAME="${{ secrets.INDEX_NAME }}"             -p 80:8080             "$IMAGE"

          echo "Deployment complete."
```

After a successful push to the `main` branch:

- GitHub Actions builds the Docker image from the repo root.
- Pushes it as `legalchatbot:latest` to ECR.
- The EC2 runner pulls and runs it as the `bharatlawbot` container.
- Your app is available at: `http://<EC2_PUBLIC_IP>/` (or your domain pointing to that EC2).

---

## 📘 System Prompt (Bharat Law Bot)

`src/prompt.py` contains a **detailed system prompt** that:

- Sets the persona: *“Bharat Law Bot – India’s Legal Help Chatbot”*
- Ensures:
  - Clear headings & bullet-based structure
  - Separation between **short answer**, **details**, **practical notes**, **disclaimer**
  - Strong **disclaimers**: this is general information, not personalised legal advice
- Forces the model to rely on the retrieved `{context}` and avoid hallucination

You can tweak `prompt.py` to adjust tone, length, and structure without changing the pipeline.

---

## ⚠️ Legal Disclaimer

Bharat Law Bot provides **general legal information for Indian law**, based on the ingested documents and model outputs.  

It **does not**:

- Replace a **qualified advocate**,
- Provide **personalised legal advice**,
- Predict or guarantee case outcomes.

For specific cases, always consult a practising lawyer with all documents and facts.

---

## 📄 License

MIT License © 2025 Shayan Banerjee

Feel free to fork, extend, and adapt for other jurisdictions and use-cases.
