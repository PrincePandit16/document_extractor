# 📄 DocExtractor — Intelligent Document Extraction Platform

> OCR + LLM-powered extraction for Indian documents (Aadhaar, Driving Licence, Passport, Invoice) using Tesseract, Groq (LLaMA), FastAPI, and Streamlit.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup (Without Docker)](#local-setup-without-docker)
- [Docker Setup (Recommended)](#docker-setup-recommended)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

**DocExtractor** is a full-stack document intelligence platform. Upload a scanned image or PDF of an Indian identity document or invoice, and it automatically:

1. Extracts raw text via **Tesseract OCR** (supports English + Hindi)
2. Parses and structures the fields using **Groq LLM (LLaMA 3)**
3. Stores results in **PostgreSQL** with full extraction logs
4. Serves data through a **FastAPI** REST API
5. Presents everything in a clean **Streamlit** web UI

---

## Features

- 🪪 **Aadhaar Card** — UID number, name, DOB, gender, address
- 🚗 **Driving Licence** — Licence no, name, DOB, expiry, vehicle classes
- 📘 **Passport** — Passport no, name, DOB, expiry, MRZ line
- 🧾 **Invoice / GST Bill** — Invoice no, seller, buyer, GSTIN, total amount
- 🤖 **Auto-detect** document type (no manual selection needed)
- 📊 **Confidence scoring** per extraction
- 📝 **Raw OCR text** view for debugging
- 📜 **Per-document processing logs** (stage-by-stage)
- 🔍 **Full document history** with delete support
- ❤️ **Health check endpoint** — OCR + LLM + DB status at a glance
- 🐳 **Docker Compose** — one command to run everything

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Backend | FastAPI + Uvicorn |
| Frontend UI | Streamlit |
| OCR Engine | Tesseract (eng + hin) |
| LLM | Groq API (LLaMA 3) |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2 + Alembic |
| Image Processing | OpenCV, Pillow |
| PDF Support | pdf2image + Poppler |
| Containerisation | Docker + Docker Compose |
| Testing | Pytest + pytest-asyncio |
| Logging | Loguru |

---

## Project Structure

```
document_extractor/
├── app/
│   ├── api/
│   │   └── routes.py          # All FastAPI route handlers
│   ├── db/
│   │   └── database.py        # SQLAlchemy engine + session
│   ├── models/                # DB models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # OCR, LLM, extraction logic
│   └── utils/
│       └── logging.py         # Loguru setup
├── config/
│   └── settings.py            # Pydantic-settings env config
├── migrations/                # Alembic migration scripts
├── tests/                     # Pytest test suite
├── main.py                    # FastAPI app entry point
├── streamlit_app.py           # Streamlit UI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── pytest.ini
```

---

## Prerequisites

Make sure you have the following installed before starting:

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Git | any | `git --version` |
| Docker Desktop | 4.x+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Tesseract OCR | 4.x+ | `tesseract --version` *(local only)* |
| Groq API Key | — | [console.groq.com](https://console.groq.com) |

---

## Local Setup (Without Docker)

Use this if you want to run and debug code directly on your machine.

### Step 1 — Clone the repository

```bash
git clone https://github.com/PrincePandit16/document_extractor.git
cd document_extractor
```

### Step 2 — Install Tesseract OCR

**Ubuntu / Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng poppler-utils
```

**macOS (Homebrew):**
```bash
brew install tesseract
brew install poppler
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
Then add Tesseract to your `PATH`.

### Step 3 — Create a virtual environment

```bash
python -m venv venv

# Activate:
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### Step 4 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Create your `.env` file

```bash
cp .env.example .env    # if .env.example exists, otherwise create manually
```

Edit `.env` with your values (see [Environment Variables](#environment-variables) section below).

### Step 6 — Start PostgreSQL locally

If you have Docker available just for the DB:
```bash
docker run -d \
  --name doc_extractor_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=doc_extractor \
  -p 5432:5432 \
  postgres:15-alpine
```

Or use any existing PostgreSQL instance and update `DATABASE_URL` in `.env`.

### Step 7 — Run database migrations

```bash
alembic upgrade head
```

### Step 8 — Start the FastAPI backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API is now live at: **http://localhost:8000**
Swagger docs at: **http://localhost:8000/docs**

### Step 9 — Start the Streamlit UI (new terminal)

```bash
streamlit run streamlit_app.py --server.port 8501
```

UI is now live at: **http://localhost:8501**

---

## Docker Setup (Recommended)

The cleanest way to run everything — one command spins up PostgreSQL, the FastAPI backend, and the Streamlit UI.

### Step 1 — Clone the repository

```bash
git clone https://github.com/PrincePandit16/document_extractor.git
cd document_extractor
```

### Step 2 — Create your `.env` file

```bash
# Create .env in the project root
touch .env
```

Add the following to `.env` (see full list in [Environment Variables](#environment-variables)):

```env
GROQ_API_KEY=your_groq_api_key_here
APP_NAME=DocExtractor
APP_VERSION=1.0.0
DATABASE_URL=postgresql://postgres:password@localhost:5432/doc_extractor
```

> ⚠️ The `DATABASE_URL` in `.env` uses `localhost` — Docker Compose will automatically override it to use `postgres` (the service name) inside the containers. You do not need to change it.

### Step 3 — Build and start all services

```bash
docker compose up --build
```

Or run in the background (detached):
```bash
docker compose up --build -d
```

### Step 4 — Access the applications

| Service | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |
| ReDoc API Docs | http://localhost:8000/redoc |

### Step 5 — Stop all services

```bash
docker compose down

# To also remove the database volume:
docker compose down -v
```

### Rebuilding after code changes

```bash
docker compose up --build
```

---

## Environment Variables

Create a `.env` file in the project root with these variables:

```env
# ── Application ───────────────────────────────────────────
APP_NAME=DocExtractor
APP_VERSION=1.0.0

# ── Database ──────────────────────────────────────────────
# Use localhost for local dev; Docker Compose overrides this automatically
DATABASE_URL=postgresql://postgres:password@localhost:5432/doc_extractor

# ── Groq LLM ─────────────────────────────────────────────
# Get your free key at: https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Optional OCR ─────────────────────────────────────────
# Only needed on Windows if Tesseract is not in PATH
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health — OCR, LLM, DB status |
| `POST` | `/documents/upload` | Upload a document and extract fields |
| `GET` | `/documents` | List all documents (`?limit=50`) |
| `GET` | `/documents/{id}` | Get a single document with extracted data |
| `DELETE` | `/documents/{id}` | Delete a document record |
| `GET` | `/documents/{id}/logs` | Get processing logs for a document |

**Upload a document (curl example):**

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@aadhaar.jpg" \
  -F "doc_type=auto"
```

**Sample response:**

```json
{
  "id": 1,
  "original_filename": "aadhaar.jpg",
  "doc_type": "aadhaar",
  "status": "completed",
  "confidence_score": 0.91,
  "extracted_data": {
    "name": "Rahul Sharma",
    "uid_number": "1234 5678 9012",
    "dob": "01/01/1990",
    "gender": "Male",
    "address": "123, MG Road, Mumbai - 400001"
  },
  "raw_ocr_text": "...",
  "created_at": "2026-05-08T10:30:00"
}
```

Full interactive docs available at **http://localhost:8000/docs**

---

## Running Tests

```bash
# Make sure your virtual environment is active
pytest

# With verbose output:
pytest -v

# Run a specific test file:
pytest tests/test_extraction.py -v

# With coverage report:
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

---

## Troubleshooting

**`tesseract: command not found` inside Docker**
The Dockerfile installs Tesseract automatically. If you see this error locally, install it via apt/brew (see Step 2 in Local Setup).

**`connection refused` on port 5432**
PostgreSQL isn't running. Start it via Docker (see Step 6 in Local Setup) or check your `DATABASE_URL` in `.env`.

**Streamlit UI shows "API not reachable"**
The FastAPI server is not running or the `API_BASE_URL` env var is wrong. Verify `http://localhost:8000/` returns a response.

**LLM extraction fails / returns empty fields**
Your `GROQ_API_KEY` is missing or invalid. Get a free key at https://console.groq.com and add it to `.env`.

**`delegated` volume error on Docker build**
Update to Docker Desktop 4.x+. Also remove `:delegated` from volume mounts in `docker-compose.yml` (see fix in previous section).

**Container exits immediately after starting**
The `CMD` instruction is missing from the `Dockerfile`. Add this as the last line:
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**PDF files not processing**
Ensure `pdf2image` is in `requirements.txt` and `poppler-utils` is in the Dockerfile's apt install block.

---

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please make sure all tests pass before submitting a PR:
```bash
pytest -v
```

---

## License

This project is open source. See [LICENSE](LICENSE) for details.

---

<div align="center">
  Built with ❤️ using FastAPI • Streamlit • Tesseract • Groq
</div>
