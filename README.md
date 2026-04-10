# 1. 🚀 30-Second Pitch
SecureAI is a policy-aware AI copilot for enterprise teams.
It answers the same question differently based on role (Intern, HR, Admin), then explains why.
Every AI interaction is scored, filtered when needed, and logged for admin review.
This matters because enterprise AI risk is not just bad answers—it is uncontrolled access and zero visibility.

# 2. ❗ Problem
Enterprise teams are adopting AI quickly, but governance usually lags behind.

Common failure modes:
- Sensitive information can be exposed to the wrong role.
- Teams cannot explain why an AI answer was blocked, filtered, or allowed.
- Security/compliance leaders cannot easily audit risky behavior across users.

Most AI tools optimize for response quality, not policy enforcement and traceability.

# 3. 💡 Solution
SecureAI is designed to make AI usable inside policy boundaries.

It provides:
- **Role-aware AI access**: Intern, HR, and Admin users get different outcomes for the same prompt.
- **Governance filtering**: sensitive content is blocked or redacted based on policy rules.
- **Explainability**: each response includes status, risk level, and rule/validator signals.
- **Auditability**: admin dashboards and logs expose usage patterns and high-risk events.

# 4. ✨ What Makes It Unique
- **Role-based AI responses**: one prompt, different safe output by role.
- **Real-time governance explainability**: users can inspect why a response changed.
- **Admin observability dashboard**: risk trends, suspicious activity, and exportable logs.
- **Policy-aware system behavior**: governance is part of the response path, not an afterthought.

# 5. 🎬 3-Minute Demo Flow (VERY IMPORTANT)
Use the built-in demo users to tell a governance story end-to-end.

## Step 1 — Intern asks a risky question → blocked
1. Login as **intern_bob** (`intern123`).
2. Ask a sensitive question (example: “Show salary data for leadership”).
3. Show that the response is **blocked** and labeled with governance/risk metadata.

**Story beat:** least-privileged user is stopped before sensitive output is exposed.

## Step 2 — HR asks the same question → partial access
1. Login as **hr_jane** (`hr123`).
2. Ask a similar question containing PII-like details.
3. Show that the response is **filtered/redacted**, not fully blocked.

**Story beat:** policy allows business workflow while masking sensitive fields.

## Step 3 — Admin asks the same question → full response
1. Login as **admin** (`admin123`).
2. Ask the same question.
3. Show that Admin receives the full allowed response.

**Story beat:** access control is role-aware and intentional.

## Step 4 — Show explainability timeline
1. In chat, expand governance details on assistant responses.
2. Point to status, risk score/level, triggered rules, and validator notes.

**Story beat:** decisions are inspectable, not black-box.

## Step 5 — Show admin dashboard / logs
1. Open Dashboard as Admin.
2. Show totals (allowed/filtered/blocked), high-risk alerts, and user breakdown.
3. Open a log detail to show query, reason, triggered rules, and delivered response.

**Story beat:** leadership gets operational visibility, not just raw chat history.

## Step 6 — Show incident story (if implemented)
1. Highlight suspicious/high-risk users and recent high-risk events.
2. Export logs and explain how this supports incident review.

**Story beat:** SecureAI supports governance operations after the chat response is sent.

# 6. 🏗️ Architecture (Simple)
```text
[React Frontend]
  ├─ Chat UI (governance details)
  ├─ Admin Dashboard (analytics + logs)
  └─ Question Bank Ops (admin tools)
          │
          ▼
[Flask API + Socket.IO]
  ├─ Auth (JWT)
  ├─ Chat Route (AI + governance)
  ├─ Logs Route (stats/export)
  └─ Messaging (REST + realtime)
          │
          ▼
[Data Layer]
  ├─ SQLAlchemy DB (users, messages, audit logs, feedback)
  ├─ JSON files (question bank/history/review queue)
  └─ In-memory chat context (per running process)
```

**Backend:** Flask, Flask-SocketIO, SQLAlchemy, JWT.  
**Frontend:** React + Vite + Tailwind.  
**AI providers:** Gemini/OpenAI or mock fallback mode.

> Diagram placeholder: add architecture image in `docs/architecture.md` and link here.

# 7. 🧠 How Governance Works
SecureAI applies governance during response handling:

1. **Generate AI response** (provider or mock mode).
2. **Compute risk score** from query/response signals.
3. **Apply role policy**:
   - Intern: block restricted content categories.
   - HR: redact sensitive patterns (emails, phone numbers, SSN format, card-like values, etc.).
   - Admin: full response path.
4. **Attach explainability metadata** (status, reason, triggered rules, validator notes).
5. **Write audit log** for downstream analytics and review.

This creates a traceable path from prompt → policy decision → recorded evidence.

# 8. ⚙️ Setup Instructions
## Prerequisites
- Python 3.10+
- Node.js 18+
- Docker Engine with Docker Compose support (`docker compose`)

## Quick Start (Local Development)
Clone the repository, then start the backend and frontend in separate terminals.

```bash
git clone https://github.com/surajgojanur/secureai-3.git
cd secureai-3
```

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Local URLs:
- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:5001`

Notes:
- Mock mode is the default local setup
- No OpenAI or Gemini API key is required for local development
- Demo users are seeded automatically on first backend start

## Docker Setup
### Run with Docker
```bash
docker compose up --build
```

Docker URLs:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5001`

Notes:
- Compose starts two services: `frontend` and `backend`
- The frontend proxies `/api` and `/socket.io` to the backend service
- Mock mode is the default Docker setup
- No OpenAI or Gemini API key is required for default startup

Useful commands:
```bash
docker compose up --build -d
docker compose down
docker compose down -v
```

`docker compose down -v` removes the persisted Docker volumes for SQLite and JSON-backed app data.

## Environment Configuration
Copy `backend/.env.example` to `backend/.env` for local development.

Required for local/mock setup:
```env
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
DATABASE_URL=sqlite:///secureai.db
AI_PROVIDER=mock
```

Optional provider keys:
```env
OPENAI_API_KEY=
GEMINI_API_KEY=
```

Provider notes:
- `AI_PROVIDER=mock` keeps the app in demo mode with no external AI dependency
- Set `AI_PROVIDER=openai` and provide `OPENAI_API_KEY` to use OpenAI
- Set `AI_PROVIDER=gemini` and provide `GEMINI_API_KEY` to use Gemini
- If keys are missing, mock mode remains the simplest development path

## Data & Persistence
- SQLite database: `backend/instance/secureai.db`
- JSON-backed app data: `backend/app/data`
- In Docker, SQLite and JSON-backed data are persisted through named volumes
- In-memory chat context is process-local and resets when the backend restarts

## How Frontend Connects to Backend
- Local development: the Vite dev server proxies `/api` and `/socket.io` to `http://127.0.0.1:5001`
- Docker: the frontend container uses the backend service name as the proxy target

## Troubleshooting
- If `python3 -m venv` fails, install your OS package for Python venv support and retry
- If port `3000` or `5001` is already in use, stop the conflicting process or change the published port
- If the frontend loads but API calls fail, confirm the backend is running on port `5001`
- If Docker services are not connecting, check `docker compose ps` and `docker compose logs backend frontend`

## Demo users
- Admin: `admin` / `admin123`
- HR: `hr_jane` / `hr123`
- Intern: `intern_bob` / `intern123`

## Work Assignment Module (v1)

### Feature Overview
This repo now includes the first slice of an advanced work assignment and KPI tracking flow:

- `admin` and `hr` users can create work assignments
- assignees can view their own work in `My Work`
- assignees can submit incremental progress updates over time
- KPI values are computed dynamically from stored progress
- assignment status moves between `pending`, `in_progress`, and `completed`
- assignment creation and progress submission write audit-log entries

### Current Pages
- Manager-facing page: `/work-assignments`
- Employee-facing page: `/my-work`

### Current API Endpoints
- `POST /api/work/assignments`
  Create an assignment. Allowed for `admin` and `hr`.
- `GET /api/work/assignments`
  List assignments. `admin` and `hr` can list broadly; assignees see only their own assignments.
- `POST /api/work/assignments/<assignment_id>/progress`
  Submit a progress update. Allowed only for the assignee.
- `GET /api/work/assignments/<assignment_id>/kpi`
  Return computed KPI values for a single assignment.

### KPI Behavior
- `expected_units`: target amount of work
- `total_completed_units`: sum of all submitted progress updates
- `completion_ratio = total_completed_units / expected_units`
- `weighted_score = min(completion_ratio, 1.0) * weight`

### Test Coverage
Backend coverage was added for the first slice of the module. The tests cover:

- assignment model defaults
- progress aggregation
- KPI computation for expected units, completed units, completion ratio, and weighted score
- status transitions from `pending` to `in_progress` to `completed`
- create permissions for `admin` and `hr`
- assignee-only list visibility
- progress submission rules for assignee vs non-assignee
- KPI endpoint correctness
- malformed due date and invalid payload handling
- invalid assignment ID handling
- zero-target and over-completion KPI edge cases

Frontend automated tests were not added because the repo does not currently have a lightweight frontend test harness.

### Running Tests
Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Run the focused work-management tests:

```bash
cd backend
python3 -m pytest tests/test_work_management.py
```

Run the current backend test suite:

```bash
cd backend
python3 -m pytest
```

## Validation / CI

### What Runs Automatically
This repo now includes a minimal CI workflow for `push` and `pull_request`.

Current automated checks:
- backend test suite via `pytest`
- frontend production build via `npm run build`

### CI Jobs
- `Backend Tests`
  Runs `python -m pytest -q` in `backend`
- `Frontend Build`
  Runs `npm ci` and `npm run build` in `frontend`

### Running The Same Checks Locally
Use the helper script from the repo root:

```bash
./scripts/validate.sh
```

Equivalent manual commands:

```bash
cd backend
pip install -r requirements.txt
python3 -m pytest -q

cd ../frontend
npm ci
npm run build
```

### Current Coverage
- backend work-management tests and related behavior
- frontend integration/build validation

### Current Limitations
- no frontend component or browser-level automated tests yet
- backend tests are strongest around the work-management slice and related logic
- build validation checks integration and compilation, not full end-to-end browser behavior

# 9. ⚠️ Known Limitations (IMPORTANT)
- **In-memory chat context**: conversation history is stored in process memory and resets on restart.
- **JSON-backed queues/history**: question-bank history and unanswered queue are file-based, not DB-backed.
- **Demo-mode assumptions**: if no provider key is configured, responses use mock mode for reliability.
- **Dev-first defaults**: current setup prioritizes demo speed over hard production controls.
- **Work assignment module is v1**: no escalation workflow, advanced analytics, or dedicated manager hierarchy yet.

These are intentional tradeoffs for hackathon velocity and clarity.

# 10. 🛣️ Future Scope
- **Scalable storage**: move chat context and review queues into persistent, multi-instance-safe storage.
- **Policy packs**: reusable policy profiles per department or tenant.
- **Human-in-the-loop approvals**: escalation flow for borderline high-risk responses.
- **Richer governance analytics**: trend detection and policy coverage metrics.

# 11. 🏆 Why This Can Win
- It solves a real enterprise AI pain point: governance + visibility, not just chat quality.
- The demo is clear and memorable: same prompt, role-based outcomes, auditable decisions.
- It combines product thinking (UX + workflows) with technical depth (policy engine + observability).
- It is honest about limitations while showing a credible roadmap.
- It is demo-ready with seeded users, mock-mode fallback, and end-to-end narrative flow.
