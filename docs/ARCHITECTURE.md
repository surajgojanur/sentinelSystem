# Architecture

## Repository Shape

- `backend/`: Flask application, models, services, tests
- `frontend/`: React/Vite SPA
- `docs/`: documentation
- `.github/workflows/ci.yml`: CI
- `compose.yaml`: local container orchestration

## Backend Architecture

### Stack

- Flask app factory in [`backend/app/__init__.py`](/home/god/GitRepos/sentinelSystem/backend/app/__init__.py)
- SQLAlchemy ORM
- JWT auth via Flask-JWT-Extended
- Socket.IO realtime layer
- SQLite by default

### Entry And Boot Sequence

The backend starts from [`backend/app.py`](/home/god/GitRepos/sentinelSystem/backend/app.py), which creates the app and runs Socket.IO.

On startup, the app factory:

- loads env vars
- configures Flask, JWT, SQLAlchemy, CORS, Socket.IO
- registers route blueprints
- imports models
- calls `db.create_all()`
- mutates schema ad hoc using `_ensure_*` helpers
- seeds roles and demo users

This means there is **no migration framework**. Schema evolution is currently handled by startup-time SQL `ALTER TABLE` logic plus `create_all()`.

### Route Modules

- [`backend/app/routes/auth.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/auth.py)
- [`backend/app/routes/admin.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/admin.py)
- [`backend/app/routes/chat.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/chat.py)
- [`backend/app/routes/logs.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/logs.py)
- [`backend/app/routes/users.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/users.py)
- [`backend/app/routes/messages.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/messages.py)
- [`backend/app/routes/attendance.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/attendance.py)
- [`backend/app/routes/work_management.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/work_management.py)
- [`backend/app/routes/roles.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/roles.py)
- [`backend/app/routes/socket_events.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/socket_events.py)
- demo add-ons: [`backend/ghost_routes.py`](/home/god/GitRepos/sentinelSystem/backend/ghost_routes.py), [`backend/attack_routes.py`](/home/god/GitRepos/sentinelSystem/backend/attack_routes.py)

### Business Logic Placement

Business logic is mostly not in controllers only. The key logic lives in:

- [`backend/app/services/governance.py`](/home/god/GitRepos/sentinelSystem/backend/app/services/governance.py)
  Role-aware filtering, risk scoring, explainability signals
- [`backend/app/services/ai_service.py`](/home/god/GitRepos/sentinelSystem/backend/app/services/ai_service.py)
  Provider fallback, local question-bank operations, unanswered queue, analytics helpers
- [`backend/app/services/face_attendance.py`](/home/god/GitRepos/sentinelSystem/backend/app/services/face_attendance.py)
  Lightweight image embedding and match logic
- [`backend/app/routes/work_management.py`](/home/god/GitRepos/sentinelSystem/backend/app/routes/work_management.py)
  KPI aggregation, board-state mapping, capacity-risk logic, escalation flow

### Persistence Patterns

There are three active storage modes:

- SQLite for users, logs, assignments, messaging, attendance, escalations
- JSON files for the question bank, question history, and unanswered queue
- in-memory process state for chat histories, Socket.IO online presence, and ghost logs

This is flexible for a demo app but not operationally consistent.

## Frontend Architecture

### Stack

- React 18
- React Router
- Axios
- Tailwind CSS
- Framer Motion
- Socket.IO client
- Recharts
- DnD Kit

### App Structure

The SPA starts in [`frontend/src/App.jsx`](/home/god/GitRepos/sentinelSystem/frontend/src/App.jsx) and is organized around page routes.

Key pages:

- governed chat
- dashboard
- question bank
- work assignments
- work board
- work escalations
- attendance
- face unlock
- messaging
- admin user access
- ghost mode
- attack simulation

### State And Data Fetching

- auth state is stored in [`frontend/src/context/AuthContext.jsx`](/home/god/GitRepos/sentinelSystem/frontend/src/context/AuthContext.jsx)
- most API calls go through [`frontend/src/utils/api.js`](/home/god/GitRepos/sentinelSystem/frontend/src/utils/api.js)
- messaging realtime uses [`frontend/src/utils/socket.js`](/home/god/GitRepos/sentinelSystem/frontend/src/utils/socket.js)

The frontend is mostly page-local state. There is no shared query/cache layer.

## Data Model

### Primary Entities

- `Role`
- `User`
- `AuditLog`
- `QuestionFeedback`
- `FavoriteQuestion`
- `Message`
- `FaceProfile`
- `AttendanceRecord`
- `WorkAssignment`
- `WorkProgressUpdate`
- `WorkEscalation`

### Important Relationships

- `User` belongs to `Role`
- `AuditLog` belongs to `User`
- `QuestionFeedback` belongs to `AuditLog` and `User`
- `Message` links sender and receiver users
- `FaceProfile` is one-to-one with `User`
- `AttendanceRecord` belongs to `User`
- `WorkAssignment` links assigning user and assignee user
- `WorkProgressUpdate` belongs to `WorkAssignment` and reporting user
- `WorkEscalation` belongs to `WorkAssignment` and creator user

## Auth And Access Design

### Implemented

- JWT bearer auth for most backend routes
- admin-only checks in some routes
- admin-or-HR checks in assignment and attendance manager flows
- role-aware filtering in governed chat

### Not Centralized

Authorization is implemented with repeated helper functions and role string checks inside route files. There is no centralized policy layer or permission map.

### Important Limitation

The frontend has a face-unlock page, but the backend does not require face verification to access sensitive endpoints. Face unlock is currently a **UI-level gate**, not a server-enforced access layer.

## Risk, Governance, And Escalation Design

### AI Governance

The governance engine currently provides:

- keyword/rule-based blocking for intern users
- redaction for HR responses
- risk scoring and low/medium/high classification
- validator notes based on suspicious term groups
- suspicious-query user counters

### Workforce Risk

Assignment risk is derived from:

- KPI completion ratio
- due date proximity
- overdue status
- recent attendance absence
- incomplete-work volume for the assignee

### Escalation Model

Escalations are simple:

- one assignment
- one creator
- one reason
- open or resolved

There is no SLA, assignee, severity taxonomy, ownership workflow, or resolution narrative yet.

## Integration Points

- optional OpenAI provider
- optional Gemini provider
- Socket.IO realtime messaging
- browser camera access for attendance and face verify

## Technical Debt Areas

- startup-time schema mutation instead of migrations
- mixed SQLite, JSON, and in-memory persistence
- permissive CORS and demo secrets by default
- unauthenticated demo routes
- UI surfaces that are disconnected from the main API host
- large frontend production bundle
- duplicated role checks across backend routes

## Growth Readiness

The repo is modular enough for incremental growth because the main concerns are already separated into routes, services, models, and pages.

It is not yet modular enough for aggressive scale because:

- authorization is ad hoc
- persistence patterns are mixed
- admin/governance logic is not normalized into reusable domain services
- demo and core product surfaces still coexist in the same app layer
