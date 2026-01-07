# HireSight – AI-Powered Resume Screener

**HireSight** is an open-source, full-stack application that automates resume screening for recruiters. It parses resumes (PDF/DOCX), extracts structured information, and ranks candidates against a job description using advanced NLP and semantic similarity—delivering actionable insights, reducing bias, and saving hours in the hiring process.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Roadmap](#roadmap)
- [Similar Projects](#similar-projects)
- [Learning Outcomes](#learning-outcomes)
- [Contributing](#contributing)
- [License](#license)

## Features
- Upload and parse multiple resumes (PDF/DOCX).
- Input job description (text or file).
- Rank candidates with match scores and explanations.
- Interactive dashboard with charts (e.g., skill gaps, experience distribution).
- Export reports (Excel/PDF) for top candidates.
- Future: Email notifications, user authentication, multi-job support.

## Tech Stack
(Open to suggestions—optimized for accuracy and ease of development)

| Layer                  | Technology                                      | Notes |
|------------------------|-------------------------------------------------|-------|
| Frontend/UI           | React                                          | Rapid prototyping with built-in uploads/charts |
| Backend               | FastAPI                                        | Async, performant API |
| Database              | PostgreSQL (SQLite for local dev)              | Structured storage of parsed data |
| Resume Parsing        | pyresparser + PyMuPDF                          | Reliable structured extraction (name, skills, experience) |
| NLP & AI              | spaCy + Sentence Transformers                  | Semantic embeddings for nuanced matching |
| Visualization         | Plotly/Altair (via Streamlit)                  | Interactive charts |
| Reporting             | pandas + openpyxl                              | Excel exports; WeasyPrint for PDF |

## Installation
```bash
git clone https://github.com/yourusername/HireSight.git
cd HireSight
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

USAGE

Start the backend (if separate): uvicorn backend.app.main:app --reload
Ensure the spaCy model is available: `python -m spacy download en_core_web_sm` (the app now checks for it automatically on startup and will download it if missing).
Run the frontend: npm run dev
In the app:
Upload resumes.
Paste/upload job description.
View ranked list with scores and insights.
Export reports.

For a production-friendly developer loop:
- `cd backend` (if you keep it separate) and `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`.
- `cd frontend`, install dependencies (`npm install`) and start Vite (`npm run dev`). The UI reads `VITE_API_BASE_URL` (defaults to `http://localhost:8000/api`) and the backend exposes CORS to `http://localhost:3000` and `http://localhost:5173` (override `ALLOWED_ORIGINS` if you build for another host).

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 ---to start backend

npm run dev to start the frontend

Example: Handles 50+ resumes in seconds; scores based on cosine similarity of embeddings.

Roadmap

Phase 1: Robust parsing & database storage.
Phase 2: Semantic matching & scoring (core MVP).
Phase 3: Interactive dashboard & visualizations.
Phase 4: Report generation.
Phase 5+: Authentication, email notifications, bias audits, deployment (Docker).

Similar Projects
Inspired by open-source tools like Resume-Matcher and pyresparser—HireSight focuses on a full-stack, user-friendly experience.

Learning Outcomes

Full-stack integration (API + UI).
Advanced NLP: Entity extraction, embeddings, similarity metrics.
Handling unstructured data (PDFs/DOCX).
Building practical AI tools with real-world implications (e.g., fair hiring).

al-world implications (e.g., fair hiring).

Contributing
Contributions welcome! Fork, branch (feature/your-feature), and submit a PR. Follow PEP8; add tests where possible. Open issues for discussions.

License
MIT License © 2026 Jamesuchechi. See LICENSE for details.
