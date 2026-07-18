# Banking Web Application — Implementation Plan

---

## 1. Solution Overview

### Objective

Deliver a lightweight, browser-based banking application that allows customers to securely log in, view their account balance, and perform basic fund transactions (deposit and withdrawal) through a clean web interface.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and logout | Customer registration / self-enrolment |
| Dashboard with account summary | Multi-account management |
| View current balance | Inter-account transfers |
| Deposit funds | Loan or credit features |
| Withdraw funds | Admin / back-office portal |
| Session management | Third-party payment gateway integration |

### Users

- **Bank Customer** — the sole end-user persona. Authenticated individuals who interact with their own account data via the web browser.

### Functional Requirements

1. A registered customer can log in with a username and password.
2. After login, the customer is directed to a personalised dashboard.
3. The dashboard displays the customer's current account balance.
4. The customer can deposit a positive monetary amount into their account.
5. The customer can withdraw a monetary amount, subject to sufficient balance.
6. The customer can log out, which terminates the session.
7. Unauthenticated requests to protected pages are redirected to the login page.

### Non-Functional Requirements

| Category | Requirement |
|---|---|
| Security | Passwords stored as hashed values (e.g. bcrypt); sessions use server-side tokens |
| Usability | Responsive layout via Bootstrap; works on desktop and mobile browsers |
| Reliability | Transactions are atomic; partial writes must not corrupt the balance |
| Maintainability | Clear separation between frontend, backend, and database layers |
| Performance | Page responses under 500 ms for all standard operations on local deployment |

### Assumptions

- The application is intended for local or internal deployment; TLS termination is out of scope for this phase.
- Customer accounts are pre-seeded in the database; self-registration is not required.
- A single currency with no formatting localisation is assumed.
- SQLite is sufficient for the expected low-concurrency, single-node deployment.
- Python 3.10+ and a modern evergreen browser are available in the target environment.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                        BROWSER                           │
│                                                          │
│   ┌──────────────────────────────────────────────────┐   │
│   │              FRONTEND  (HTML + Bootstrap)        │   │
│   │                                                  │   │
│   │  Login Page │ Dashboard │ Deposit │ Withdraw     │   │
│   └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼────────────────────────────────┘
                          │  HTTP Requests
                          │  (form submissions / fetch)
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    BACKEND  (Python Flask)               │
│                                                          │
│   Auth Routes │ Dashboard Route │ Transaction Routes     │
│                                                          │
│   ┌──────────────────────────────────────────────────┐   │
│   │              Session & Business Logic            │   │
│   └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼────────────────────────────────┘
                          │  SQL Queries (via SQLite3 / ORM)
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   DATABASE  (SQLite)                     │
│                                                          │
│        Customers Table  │  Transactions Table           │
└──────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

| Layer | Technology | Role |
|---|---|---|
| Frontend | HTML + Bootstrap | Renders UI, captures user input, sends HTTP requests |
| Backend | Python Flask | Validates input, enforces business rules, manages session, queries DB |
| Database | SQLite | Persists customer records and transaction history |

The frontend and backend communicate exclusively over HTTP. The backend is the sole layer that reads from or writes to the database. The frontend never interacts with the database directly.

### Request Lifecycle

```
1. Customer submits a form (e.g. Deposit)
        │
        ▼
2. Browser sends HTTP POST to Flask route (e.g. /deposit)
        │
        ▼
3. Flask middleware checks session → redirect to /login if unauthenticated
        │
        ▼
4. Route handler validates and sanitises input
        │
        ▼
5. Business logic layer applies rules (e.g. sufficient balance check)
        │
        ▼
6. Database layer executes atomic read-modify-write
        │
        ▼
7. Flask renders updated template and returns HTTP response
        │
        ▼
8. Browser displays updated page (e.g. Dashboard with new balance)
```

---

## 3. Component Design

### Frontend Responsibilities

- **Presentation** — Render pages using Bootstrap-styled HTML templates served by Flask (Jinja2).
- **User Input** — Provide forms for login credentials and transaction amounts.
- **Navigation** — Link between Dashboard, Deposit, Withdraw, and Logout actions.
- **Feedback** — Display success and error messages returned from the backend.
- **Session Awareness** — Conditionally show/hide elements based on authentication state reflected in the rendered template.

> The frontend contains no business logic and no direct data access. All state changes are driven by server responses.

### Backend Responsibilities

- **Routing** — Map URL endpoints to handler functions for each feature.
- **Authentication** — Verify credentials at login; issue and validate session cookies.
- **Authorisation** — Protect all non-login routes behind a session guard.
- **Business Logic** — Enforce rules such as minimum deposit amounts and withdrawal limits.
- **Data Access** — Execute parameterised queries against SQLite; return results to routes.
- **Template Rendering** — Pass context data to Jinja2 templates for HTML generation.
- **Error Handling** — Return meaningful feedback for invalid inputs or failed operations.

### Database Responsibilities

- **Persistence** — Store customer credentials (hashed passwords), profile data, and account balances.
- **Transaction Log** — Record every deposit and withdrawal with amount, type, and timestamp.
- **Integrity** — Enforce constraints to prevent negative balances or corrupt records at the storage level.

---

## 4. Folder Structure

```
Banking Workshop/
│
├── IMPLEMENTATION_PLAN.md          ← This document
│
├── FRONTEND/                       ← All client-side assets
│   ├── templates/                  ← Jinja2 HTML templates
│   │   ├── base.html               ← Shared layout (Bootstrap, nav, flash messages)
│   │   ├── login.html              ← Login form page
│   │   ├── dashboard.html          ← Account summary and quick-action links
│   │   ├── deposit.html            ← Deposit form page
│   │   └── withdraw.html           ← Withdrawal form page
│   └── static/                     ← Static files served directly by Flask
│       ├── css/
│       │   └── custom.css          ← App-specific style overrides
│       └── js/
│           └── app.js              ← Minimal client-side helpers (optional)
│
└── BACKEND/                        ← All server-side code and data
    ├── app.py                      ← Flask application entry point; app factory
    ├── routes/                     ← Route/controller layer
    │   ├── auth.py                 ← Login and logout endpoints
    │   ├── dashboard.py            ← Dashboard view endpoint
    │   └── transactions.py         ← Deposit and withdraw endpoints
    ├── services/                   ← Business logic layer
    │   ├── auth_service.py         ← Credential validation, session helpers
    │   └── account_service.py      ← Balance retrieval, deposit, withdrawal logic
    ├── database/                   ← Data access layer
    │   ├── db.py                   ← Connection management and query helpers
    │   └── banking.db              ← SQLite database file (runtime-generated)
    └── config.py                   ← Environment configuration (secret key, DB path)
```

### Responsibility of Each Folder

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | Jinja2 HTML pages; presentational only, no logic |
| `FRONTEND/static/` | Bootstrap CSS/JS and custom overrides served as-is |
| `BACKEND/app.py` | Initialises Flask app, registers blueprints, sets config |
| `BACKEND/routes/` | Maps HTTP verbs + URLs to handler functions; thin controllers |
| `BACKEND/services/` | Implements all business rules independently of HTTP layer |
| `BACKEND/database/` | Encapsulates all SQL; no business logic lives here |
| `BACKEND/config.py` | Centralises secrets and environment-specific settings |

---

## 5. Module Breakdown

### Authentication Module

**Purpose:** Control who can access the application.

| Component | Responsibility |
|---|---|
| Login Page (`login.html`) | Collect username and password |
| Auth Route (`auth.py`) | Accept POST, delegate to service, set/clear session |
| Auth Service (`auth_service.py`) | Hash comparison, session token creation |
| Session Guard | Decorator applied to all protected routes |
| Logout Route | Clear server-side session and redirect to login |

**Key interactions:** Login route → Auth Service → DB (customer lookup) → set session → redirect to Dashboard.

---

### Dashboard Module

**Purpose:** Provide the customer with an at-a-glance account summary after login.

| Component | Responsibility |
|---|---|
| Dashboard Page (`dashboard.html`) | Display customer name, current balance, and action links |
| Dashboard Route (`dashboard.py`) | Fetch account data and pass to template |
| Account Service (`account_service.py`) | Retrieve current balance for the logged-in customer |

**Key interactions:** GET /dashboard → session check → Account Service → DB (balance query) → render dashboard.

---

### Account Management Module

**Purpose:** Expose the current account balance as a discrete, reusable capability consumed by the Dashboard and Transaction modules.

| Component | Responsibility |
|---|---|
| Account Service | Centralise all reads/writes to the customer account record |
| DB Layer (`db.py`) | Execute balance SELECT and UPDATE queries |

**Key interactions:** Any module needing balance data calls Account Service, never the DB layer directly.

---

### Transactions Module

**Purpose:** Allow the customer to change their account balance via deposit or withdrawal.

| Component | Responsibility |
|---|---|
| Deposit Page (`deposit.html`) | Form for entering a deposit amount |
| Withdraw Page (`withdraw.html`) | Form for entering a withdrawal amount |
| Transaction Route (`transactions.py`) | Accept POST, validate input, delegate to service |
| Account Service | Apply deposit/withdrawal; enforce business rules |
| DB Layer | Persist balance update and append transaction log record atomically |

**Key interactions:** POST /deposit or /withdraw → route validates input → Account Service applies rule → DB atomic write → redirect to Dashboard with confirmation message.

---

## 6. Implementation Roadmap

### Development Phases

```
Phase 1 — Project Scaffolding
Phase 2 — Authentication
Phase 3 — Dashboard & Balance View
Phase 4 — Transactions (Deposit & Withdraw)
Phase 5 — Integration, Testing & Polish
```

---

#### Phase 1 — Project Scaffolding

**Goal:** Establish folder structure, dependencies, and a running "hello world" Flask app.

| Task | Effort |
|---|---|
| Create folder structure (`FRONTEND/`, `BACKEND/`) | 0.5 h |
| Set up Python virtual environment and install Flask | 0.5 h |
| Create `app.py` with Flask factory and `config.py` | 1 h |
| Create `base.html` with Bootstrap layout | 1 h |
| Initialise SQLite DB file and `db.py` connection helper | 1 h |

**Estimated phase effort:** ~4 hours
**Dependencies:** Python 3.10+, pip, Bootstrap CDN or local bundle

---

#### Phase 2 — Authentication

**Goal:** Working login and logout flow with session protection.

| Task | Effort |
|---|---|
| Create `login.html` form | 1 h |
| Implement `auth.py` login/logout routes | 1.5 h |
| Implement `auth_service.py` with password hashing | 1.5 h |
| Add session guard decorator | 1 h |
| Seed one test customer account in DB | 0.5 h |

**Estimated phase effort:** ~5.5 hours
**Dependencies:** Phase 1 complete; `bcrypt` or `werkzeug.security` library

---

#### Phase 3 — Dashboard & Balance View

**Goal:** Authenticated customers see their balance on the dashboard.

| Task | Effort |
|---|---|
| Create `dashboard.html` template | 1 h |
| Implement `dashboard.py` route | 1 h |
| Implement balance retrieval in `account_service.py` | 1 h |

**Estimated phase effort:** ~3 hours
**Dependencies:** Phase 2 complete (session guard available)

---

#### Phase 4 — Transactions (Deposit & Withdraw)

**Goal:** Customers can deposit and withdraw funds; balance updates correctly.

| Task | Effort |
|---|---|
| Create `deposit.html` and `withdraw.html` forms | 1.5 h |
| Implement `transactions.py` routes for both actions | 2 h |
| Implement deposit and withdraw logic in `account_service.py` | 2 h |
| Add transaction log write to `db.py` | 1 h |
| Validate edge cases (negative input, overdraft) | 1 h |

**Estimated phase effort:** ~7.5 hours
**Dependencies:** Phase 3 complete (account service base in place)

---

#### Phase 5 — Integration, Testing & Polish

**Goal:** End-to-end flow verified; UI consistent; edge cases handled.

| Task | Effort |
|---|---|
| End-to-end manual walkthrough of all user flows | 1 h |
| Fix identified bugs and edge cases | 2 h |
| Add Bootstrap flash message display in `base.html` | 1 h |
| Code review and inline documentation | 1.5 h |
| Final folder and file clean-up | 0.5 h |

**Estimated phase effort:** ~6 hours
**Dependencies:** Phases 1–4 complete

---

### Summary

| Phase | Description | Estimated Effort |
|---|---|---|
| 1 | Project Scaffolding | ~4 h |
| 2 | Authentication | ~5.5 h |
| 3 | Dashboard & Balance View | ~3 h |
| 4 | Transactions | ~7.5 h |
| 5 | Integration & Polish | ~6 h |
| **Total** | | **~26 hours** |

---

### Dependency Graph

```
Phase 1 (Scaffolding)
    └── Phase 2 (Authentication)
            └── Phase 3 (Dashboard)
                    └── Phase 4 (Transactions)
                                └── Phase 5 (Integration & Polish)
```

Each phase is a strict prerequisite for the next. No parallel tracks are assumed given the single-developer scope of this project.

---

*Document scope: planning only. No database schema, SQL scripts, API contracts, or implementation code are included.*
