# ✦ Pitch Visualizer — AI Storyboard Generator

> Transform narrative text into cinematic visual storyboards using Claude + DALL-E 3 / Imagen 3

![Version](https://img.shields.io/badge/version-2.0.0-6366F1?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/react-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)

---

## What It Does

Pitch Visualizer takes a block of narrative text — a customer success story, a product pitch, a journey — and transforms it into a multi-panel visual storyboard using a 6-stage AI pipeline:

1. **Intelligent Segmentation** — spaCy NLP splits text into meaningful visual scenes
2. **Narrative Arc Detection** — Claude analyses story structure and assigns each panel a role (setup/tension/climax/resolution) and emotional intensity score
3. **LLM Prompt Engineering** — Claude converts each segment into a rich, cinematically-aware visual prompt informed by the arc data
4. **Style Consistency Engine** — a style profile (Cinematic, Corporate, Futuristic, etc.) is woven into every prompt ensuring visual coherence across all panels
5. **Image Generation** — DALL-E 3 or Google Imagen 3 generates each panel in parallel
6. **Storyboard Assembly** — panels are assembled with metadata into a live UI and exportable HTML file

---

## Features

- 🎬 **6 visual style profiles** — Cinematic, Corporate, Storybook, Minimal, Futuristic, Documentary
- 🤖 **Dual image models** — DALL-E 3 (OpenAI) and Gemini-3.1-flash-image-preview (Google Gemini), user-selectable
- 📖 **Narrative Arc Detection** — Claude maps story structure to visual intensity per panel
- ⚡ **Real-time panel streaming** — panels appear one-by-one as they generate
- ✏️ **Panel editor** — edit prompts inline, preview with Claude, regenerate individual panels
- 💾 **HTML export** — self-contained storyboard file with base64-embedded images
- 🖨️ **Print / PDF** — browser print view optimised for PDF export
- 🏗️ **Production-grade backend** — FastAPI, async pipeline, Pydantic validation, structured logging, full test suite

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI — Prompts** | Anthropic Claude (claude-opus-4-5) |
| **AI — Images** | OpenAI DALL-E 3 / Google Imagen 3 |
| **NLP** | spaCy, scikit-learn (TF-IDF) |
| **Frontend** | React 18, Vite, Tailwind CSS |
| **State** | Zustand, TanStack Query |
| **Animations** | Framer Motion |
| **Storage** | Local filesystem + FastAPI StaticFiles |
| **Containers** | Docker + Docker Compose |

---

## Quick Start (Docker — Recommended)

### Prerequisites
- Docker + Docker Compose
- API keys for Anthropic, OpenAI, and/or Google AI

### 1. Clone and configure

```bash
git clone https://github.com/yourname/pitch-visualizer.git
cd pitch-visualizer

cp backend/.env.example backend/.env
```

### 2. Add your API keys to `backend/.env`

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-google-ai-key-here   # Only needed if using Gemini-3.1-flash-image-preview
```

### 3. Launch

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

That's it. No database. No Redis. No cloud accounts.

---

## Manual Setup (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Create storage directory
mkdir -p storage/images

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

npm install

# Create env file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

npm run dev
```

Frontend runs at http://localhost:3000

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | — | Claude API key (prompt engineering + arc detection) |
| `OPENAI_API_KEY` | ✅* | — | OpenAI key (* required if using DALL-E 3) |
| `GOOGLE_API_KEY` | ✅* | — | Google AI key (* required if using gemini-3.1-flash-image-preview) |
| `CLAUDE_MODEL` | No | `claude-opus-4-5` | Claude model to use |
| `DALLE_QUALITY` | No | `hd` | `standard` or `hd` (affects cost) |
| `DEFAULT_PANELS` | No | `5` | Default panel count |
| `MAX_PANELS` | No | `8` | Maximum panels per storyboard |
| `STORAGE_PATH` | No | `./storage/images` | Where images are saved |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## API Reference

Full interactive documentation at `/docs` (Swagger UI) and `/redoc`.

### Key Endpoints

```
POST   /api/v1/projects                          Create project + start generation
GET    /api/v1/projects                          List all projects
GET    /api/v1/projects/{id}                     Full project detail
GET    /api/v1/projects/{id}/status              Poll generation progress (lightweight)
DELETE /api/v1/projects/{id}                     Delete project
POST   /api/v1/projects/{id}/regenerate          Regenerate entire storyboard

POST   /api/v1/projects/{id}/panels/{n}/regenerate   Regenerate one panel
PATCH  /api/v1/projects/{id}/panels/{n}/prompt        Update panel prompt
POST   /api/v1/preview-prompt                    Preview Claude prompt (no image gen)

GET    /api/v1/projects/{id}/export/html         Download HTML storyboard
GET    /api/v1/projects/{id}/export/json         Export raw JSON

GET    /api/v1/styles                            List style profiles
GET    /api/v1/models                            List image models
GET    /health                                   Health check
```

### Example: Create a Storyboard

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Acme Corp Success Story",
    "input_text": "Acme Corp was struggling with disconnected systems, losing hours every day. They found our platform and unified everything in one place. Within 90 days, productivity jumped 40%. Today they are our most successful enterprise client.",
    "style_profile": "cinematic",
    "options": {
      "max_panels": 4,
      "image_model": "dalle3",
      "image_quality": "hd",
      "detect_arc": true
    }
  }'
```

Response (202 Accepted):
```json
{
  "project_id": "f7a3b2c1-...",
  "status": "queued",
  "poll_url": "/api/v1/projects/f7a3b2c1-.../status"
}
```

Then poll the status endpoint every 1-2 seconds until `status === "completed"`.

---

## Project Structure

```
pitch-visualizer/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # Route handlers (projects, panels, exports, styles)
│   │   ├── core/             # AI Pipeline (6 stages)
│   │   │   ├── segmentation.py       Stage 1: spaCy NLP
│   │   │   ├── arc_detector.py       Stage 2: Claude arc detection ★
│   │   │   ├── style_engine.py       Stage 3: Style profiles
│   │   │   ├── prompt_engine.py      Stage 4: Claude prompt engineering
│   │   │   ├── image_service.py      Stage 5: DALL-E 3 + Imagen 3
│   │   │   ├── storyboard_builder.py Stage 6: Assembly + HTML export
│   │   │   └── pipeline.py           Master orchestrator
│   │   ├── models/           # Pydantic domain models + API schemas
│   │   ├── store/            # BaseStore interface + InMemoryStore
│   │   ├── utils/            # Logging, errors, cost estimator
│   │   ├── templates/        # Jinja2 HTML export template
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   ├── config.py         # Pydantic settings
│   │   └── main.py           # App factory
│   ├── tests/
│   │   ├── unit/             # Segmentation, arc detection, store tests
│   │   └── integration/      # Full API endpoint tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, Create, Generating, StoryboardView, PanelEditor, ExportView
│   │   ├── components/       # Layout, panels, storyboard, UI primitives
│   │   ├── hooks/            # useGenerationPolling, useProjectDetail, useProjects
│   │   ├── stores/           # Zustand (generation state, UI state)
│   │   ├── api/              # Axios client with all typed API methods
│   │   └── utils/            # Formatting helpers
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Running Tests

```bash
cd backend

# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_segmentation.py -v
```

---

## Design Decisions

### Why Narrative Arc Detection?
The challenge brief calls for "intelligent prompt engineering." Most solutions will simply pass each sentence verbatim to an image model. We go deeper: Claude analyses the *entire story* first, classifying each panel's narrative role (setup/tension/climax/resolution) and emotional intensity (0–1.0). This context is then injected into every individual prompt — so panel 1 gets soft establishing light and panel 3 gets maximum cinematic drama. The result is a storyboard that feels like a coherent visual narrative, not a collection of random images.

### Why In-Memory Store Instead of MongoDB?
This build prioritises zero-friction setup. The `InMemoryStore` implements the same `BaseStore` abstract interface as a hypothetical `MongoStore`. Swapping to MongoDB requires changing exactly one line in `dependencies.py`. State is lost on server restart — this is documented and acceptable for a demo/hackathon context.

### Why FastAPI BackgroundTasks Instead of Celery?
Image generation for 4–6 panels takes 30–90 seconds. `BackgroundTasks` runs the pipeline asynchronously without blocking the HTTP response. The frontend polls `/status` every 1.5 seconds. This produces identical UX to a Celery-based system without requiring Redis.

### Why Parallel Image Generation?
`asyncio.gather()` fires all panel image generation calls simultaneously (Stages 3–5). This reduces total wall-clock time by ~60% compared to sequential generation, while staying within typical API rate limits.

### Why Two Image Models?
DALL-E 3 and Imagen 3 have different aesthetic strengths. DALL-E 3 excels at creative, dramatic, and illustrative styles. Imagen 3 produces superior photorealistic results. Giving the user a choice per-project makes the tool genuinely more useful rather than artificially constraining output.

### Style Suffix Strategy
Rather than asking Claude to describe a style in every prompt (expensive and inconsistent), each style profile has a pre-crafted, carefully tested visual suffix that is appended to every engineered prompt. This guarantees visual consistency across panels and reduces prompt token usage.

---

## Cost Estimates

| Configuration | Per Storyboard |
|---|---|
| 5 panels · DALL-E 3 HD · Arc detection | ~$0.45–$0.55 |
| 5 panels · Imagen 3 · Arc detection | ~$0.25–$0.35 |
| 3 panels · DALL-E 3 Standard | ~$0.20–$0.25 |

Claude costs (arc detection + prompt engineering) are ~$0.03–$0.08 per storyboard.

---

## Upgrade Path to Full Production

| MVP (this build) | Production upgrade | Change required |
|---|---|---|
| `InMemoryStore` | MongoDB + Motor | Implement `MongoStore(BaseStore)`, swap in `dependencies.py` |
| Local filesystem | AWS S3 + CloudFront | Implement `S3StorageBackend`, swap storage config |
| `BackgroundTasks` | Celery + Redis | Wrap `pipeline.run()` in `@celery_app.task` |
| No auth | JWT + user model | Add auth middleware + user_id to project models |
| Browser print PDF | WeasyPrint server PDF | Add `/export/pdf` endpoint |

---

## License

MIT