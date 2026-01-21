# Leads Checking Tool - Non-Leaked Email Filter System

A tool to filter leaked/used emails from marketing leads by comparing against existing email databases.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEW VPS                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   React     │  │   FastAPI   │  │   MongoDB   │              │
│  │  Frontend   │──│   Backend   │──│  (New DB)   │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
│                          │                                       │
│                   ┌──────┴──────┐                                │
│                   │    Redis    │                                │
│                   │   (Queue)   │                                │
│                   └──────┬──────┘                                │
│                          │                                       │
│         ┌────────────────┼────────────────┐                      │
│         │                │                │                      │
│    ┌────┴────┐     ┌────┴────┐     ┌────┴────┐                  │
│    │ Worker 1│     │ Worker 2│     │ Worker N│                  │
│    └─────────┘     └─────────┘     └─────────┘                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ READ ONLY
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING VPS (VPS2-VPS8)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   VPS2 DB   │  │   VPS3 DB   │  │   VPS4 DB   │  ...         │
│  │  (Emails)   │  │  (Emails)   │  │  (Emails)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
leads-checker-tool/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Config, security
│   │   ├── db/               # Database connections
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   ├── workers/          # Celery workers
│   │   └── main.py           # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## Tech Stack

- **Backend**: FastAPI + Celery + Redis
- **Database**: MongoDB
- **Frontend**: React + TailwindCSS
- **Task Queue**: Celery with Redis broker

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (running locally or remote)
- Redis (running locally or remote)

## Setup & Run Instructions

### Step 1: Configure Environment

```bash
cd leads-checker-tool

# Copy environment file
copy .env.example .env

# Edit .env with your configurations (see below)
```

### Step 2: Start Backend

```powershell
# Open Terminal 1 - Backend API
cd "d:\Patmar Properties\leads-checker-tool\backend"

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Run FastAPI server (auto-migration runs on startup)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Start Celery Worker

```powershell
# Open Terminal 2 - Celery Worker
cd "d:\Patmar Properties\leads-checker-tool\backend"

# Activate virtual environment
.\venv\Scripts\activate

# Run Celery worker
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### Step 4: Start Frontend

```powershell
# Open Terminal 3 - Frontend
cd "d:\Patmar Properties\leads-checker-tool\frontend"

# Install dependencies (first time only)
npm install

# Run development server
npm run dev
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Environment Variables Configuration

Copy values from your `privatedatachecker/backend/.env`:

| From privatedatachecker | To leads-checker-tool |
|------------------------|----------------------|
| `EMAIL_AG_MONGO_URI` | `VPS2_MONGODB_URL` |
| `EMAIL_AG_MONGO_DB` | `VPS2_MONGODB_DATABASE` |
| `EMAIL_HN_MONGO_URI` | `VPS3_MONGODB_URL` |
| `EMAIL_HN_MONGO_DB` | `VPS3_MONGODB_DATABASE` |
| `EMAIL_OU_MONGO_URI` | `VPS4_MONGODB_URL` |
| `EMAIL_OU_MONGO_DB` | `VPS4_MONGODB_DATABASE` |
| `EMAIL_VZ_MONGO_URI` | `VPS5_MONGODB_URL` |
| `EMAIL_VZ_MONGO_DB` | `VPS5_MONGODB_DATABASE` |
| `EMAIL_GMAIL_MONGO_URI` | `VPS6_MONGODB_URL` |
| `EMAIL_GMAIL_MONGO_DB` | `VPS6_MONGODB_DATABASE` |
| `EMAIL_HOTMAIL_MONGO_URI` | `VPS7_MONGODB_URL` |
| `EMAIL_HOTMAIL_MONGO_DB` | `VPS7_MONGODB_DATABASE` |
| `EMAIL_YAHOO_AOL_MONGO_URI` | `VPS8_MONGODB_URL` |
| `EMAIL_YAHOO_AOL_MONGO_DB` | `VPS8_MONGODB_DATABASE` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/verify-key` | Verify device key |
| POST | `/api/leads/upload` | Upload leads.txt file |
| GET | `/api/leads/download-result/{task_id}` | Download filtered results |
| GET | `/api/leads/task-status/{task_id}` | Check processing status |
| POST | `/api/admin/generate-key` | Generate new device key |
| GET | `/api/admin/keys` | List all device keys |
| PATCH | `/api/admin/keys/{key_id}` | Enable/disable key |
| GET | `/api/admin/leads-by-date` | Download leads by date range |

## Scaling Workers

Run multiple worker processes for faster processing:

```powershell
# Terminal 2, 3, 4... - Additional workers
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

## Auto-Migration

Database indexes are automatically created when the backend starts. No manual migration needed.

## License

Internal use only.
