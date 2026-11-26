# Elderease – Intelligent Family Care Coordination

## 🌐 Live Website
[Visit ElderEase](https://elder-ease-kappa.vercel.app)
Elderease is a hackathon MVP for family care coordination. The repository has separate React/Vite, FastAPI REST, and MCP interfaces. The REST health route and MCP health tool call the same backend service function. The Phase 6 refill assistant uses the official Google Gen AI SDK and an MCP client connection to the existing FastMCP server; Telegram integration is not implemented.

## Project structure

```text
project-root/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/routers/
│   │   ├── core/
│   │   ├── database/
│   │   ├── mcp/tools/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── data/
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── context/
    │   ├── hooks/
    │   ├── pages/
    │   ├── services/
    │   └── utils/
    ├── .env.example
    └── package.json
```

## Prerequisites

- Node.js 20+ (recommended) and npm
- Python 3.10+

## Run the backend (PowerShell)

From the project root:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The REST health endpoint is available at `http://127.0.0.1:8000/api/health`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

## Initialize and seed the database

After installing the backend dependencies, run these commands from the `backend` directory with its virtual environment activated:

```powershell
python -m app.database.init_db
python -m app.database.seed
```

Both commands are safe to run again. Initialization creates missing tables using the existing SQLAlchemy engine. Seeding upserts synthetic data for one demo care-profile context, three caregivers, four medicines, today's dose schedules, two upcoming appointments, stock transactions, and notifications. It does not create an additional care-recipient table. Scheduled times are JSON arrays of 24-hour `HH:MM` strings. Seed datetimes are generated as UTC; SQLite stores them without timezone offsets, so the application should interpret stored datetimes as UTC.

The database contains six tables: `caregivers`, `medicines`, `dose_logs`, `appointments`, `notifications`, and `stock_transactions`. Caregivers are related to assigned medicines, dose logs, appointments, notifications, and recorded stock transactions. Medicines are related to dose logs and stock transactions. Dose logs uniquely identify a medicine's scheduled dose, preventing duplicate logs for the same medicine and scheduled time. Foreign keys and database constraints protect the relationships, status values, and stock transaction signs.

## Phase 3 REST API

All REST routes are under `/api`. FastAPI provides interactive documentation at `http://127.0.0.1:8000/docs` and the OpenAPI schema at `http://127.0.0.1:8000/openapi.json`.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/dashboard/overview` | Live medicine, dose, appointment, low-stock, and recent-activity metrics |
| GET, POST | `/api/medicines` | List or create medicines |
| GET, PUT, DELETE | `/api/medicines/{medicine_id}` | Read, update details, or delete a medicine without dose/stock history |
| GET, POST | `/api/medicines/{medicine_id}/stock` | Read stock history or record a purchase/correction |
| GET | `/api/medicines/refill-forecast` | Forecast refills for all medicines |
| GET | `/api/medicines/{medicine_id}/refill-forecast` | Forecast a medicine refill |
| POST | `/api/assistant/chat` | Ask Groq about refill status using the `check_refill_status` MCP tool |
| GET | `/api/doses/today` | List today's scheduled doses |
| POST | `/api/doses/{dose_id}/log` | Log pending, confirmed, delayed, or skipped status |
| GET, POST, PUT, DELETE | `/api/appointments` and `/api/appointments/{appointment_id}` | Manage appointments and caregiver assignments |
| GET | `/api/caregivers` and `/api/caregivers/{caregiver_id}` | List or read caregivers |
| GET | `/api/notifications` | List notifications |
| PATCH | `/api/notifications/{notification_id}/acknowledge` | Acknowledge a notification |

Collection responses use `{ "items": [...], "total": n, "offset": n, "limit": n }`. Errors use an `error` object with a code and message. Datetimes accepted by appointment creation/update must include a timezone and are normalized to UTC. SQLite stores datetime values without the timezone offset; API responses identify stored values as UTC.

Medicine stock is changed through stock transactions, not through medicine `PUT`. Creating a medicine with opening stock requires an assigned caregiver so the stock can be recorded. Confirming a dose consumes `units_per_dose` once in the same transaction as the dose update. Repeated confirmation is idempotent; confirmed doses cannot be reverted. Pending, delayed, and skipped doses do not consume stock, and pending doses are not automatically treated as missed.

## Phase 4 refill forecasts

The refill forecast endpoints estimate consumption over the next seven days from each medicine's `scheduled_times` and `units_per_dose`. The forecast treats `medicines.current_stock` as authoritative; purchase, correction, and confirmed-dose transactions have already updated that balance and are not added or subtracted a second time. Confirmed and skipped scheduled dose logs are excluded from projected consumption. Pending, delayed, and unlogged scheduled doses remain included, with elapsed unconfirmed doses projected from the current time rather than marked missed.

The response includes the upcoming scheduled doses, expected seven-day consumption, estimated remaining supply, estimated depletion date/time, threshold, urgency, and calculation explanation. `CRITICAL` means no stock or insufficient stock for the next scheduled dose; `URGENT` means current stock is at or below the threshold; `UPCOMING` means projected stock after seven days is at or below the threshold; otherwise urgency is `SAFE`. Invalid or missing schedules return an unavailable forecast with a warning instead of an invented estimate. Forecasts are calculated on request, are not stored, and are estimates rather than medical advice.

## Phase 6 refill assistant

The Assistant page sends chat messages to `POST /api/assistant/chat`. The backend checks `GROQ_API_KEY` from `backend/.env`, starts an MCP stdio client connection to the existing FastMCP server, discovers and calls `check_refill_status`, then asks Groq to explain that returned forecast through the Responses API using the OpenAI Python SDK. The response includes the assistant message, tool name, and actual tool result; the frontend displays the result alongside Groq’s explanation. Missing Groq configuration or MCP/Groq failures return explicit errors rather than generated fallback answers. Groq credentials remain on the backend.

Set `GROQ_API_KEY` in `backend/.env` before using the assistant. `GROQ_BASE_URL` defaults to `https://api.groq.com/openai/v1`; `GROQ_MODEL` defaults to `openai/gpt-oss-20b`. Both can be changed without editing code. Copying `backend/.env.example` to `backend/.env` provides placeholders, not a working API key.

## Run backend tests

From the `backend` directory with the virtual environment activated:

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

## Run the frontend (a second PowerShell terminal)

From the project root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`). The interactive dashboard loads the configured REST API and shows a connection status in the navigation sidebar.

## Phase 5 interactive dashboard

The frontend includes responsive Overview, Medications, Care calendar, Family coordination, and AI assistant pages. The Overview and care pages read from the documented REST endpoints; medicine, appointment, dose confirmation, stock adjustment, and notification acknowledgement actions refresh affected data after success. The medicine chart visualizes the seven-day refill forecasts returned by the backend. The AI assistant uses the Phase 6 Groq/MCP workflow and displays the actual tool result.

The frontend uses React Router, Lucide icons, and Recharts. The API base URL can be set with `VITE_API_BASE_URL` in `frontend/.env`; the default is `http://127.0.0.1:8000`.

## Run the MCP server (optional, separate terminal)

After setting up and activating the backend virtual environment:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.mcp.server
```

The MCP server uses the Python MCP SDK over stdio and exposes health and refill-status tools that reuse backend service functions. It is a separate interface from the REST API; the assistant connects to it through an MCP client.

## Configuration and scope

- Copy each `.env.example` to `.env` and supply credentials locally. Never commit `.env` files.
- `GROQ_API_KEY` is a backend-only secret used by the Phase 6 refill assistant; `GROQ_MODEL` selects the model and `GROQ_BASE_URL` configures the OpenAI-compatible Groq API endpoint. Telegram variables remain reserved placeholders.
- Seed names, appointments, messages, and inventory are synthetic demo data, not real medical records. Refill forecasts are calculated on request and not stored.
- SQLite configuration and SQLAlchemy sessions are centralized in `backend/app/database/`.
- The backend CORS allowlist is configured through `CORS_ORIGINS` in `backend/.env`.
- The frontend uses Tailwind CSS 4's Vite plugin (`@tailwindcss/vite`).
