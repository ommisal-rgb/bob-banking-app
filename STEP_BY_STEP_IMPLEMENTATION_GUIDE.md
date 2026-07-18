# Banking Web Application — Step-by-Step Implementation Guide

> **Purpose:** Plain-English instructions explaining *how* to build each part of the banking application.
> This guide does **not** contain ready-to-run code. It explains the logic, decisions, and sequence
> you need to follow so you can write the code yourself or guide a developer through the build.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing a single line of code, confirm the following tools are installed on your machine:

- **Python 3.10 or higher** — the runtime for the Flask backend. Verify by running `python --version` in a terminal.
- **pip** — Python's package manager, bundled with Python. Used to install all third-party libraries.
- **A code editor** — VS Code or PyCharm are recommended for Python and HTML work.
- **A modern browser** — Chrome, Firefox, or Edge for testing the UI.

---

### 1.2 Create the Project Folder Structure

Create the top-level project folder (`Banking Workshop/`) and then manually create the following sub-directories inside it. Having the right structure before writing any files prevents confusion later.

```
Banking Workshop/
├── FRONTEND/
│   ├── templates/
│   └── static/
│       ├── css/
│       └── js/
└── BACKEND/
    ├── routes/
    ├── services/
    └── database/
```

Every folder listed above should be created as an empty directory at this point. Files will be added to them in later steps.

---

### 1.3 Set Up a Python Virtual Environment

A virtual environment isolates your project's dependencies from every other Python project on your machine. This prevents version conflicts and keeps the project self-contained.

**How to do it:**

1. Open a terminal inside the `Banking Workshop/` folder.
2. Create the virtual environment by telling Python to generate a folder (conventionally named `venv`) that will hold a private copy of Python and pip.
3. Activate the virtual environment. Once active, any packages you install go into the `venv` folder, not system Python.
4. You will know the environment is active because the terminal prompt will show `(venv)` at the start.

> Always activate the virtual environment before running the application or installing packages. Deactivate it when you are done by typing `deactivate`.

---

### 1.4 Install Required Dependencies

With the virtual environment active, install the following packages using pip:

| Package | Why it is needed |
|---|---|
| `flask` | The web framework that handles routing, templates, and sessions |
| `werkzeug` | Ships with Flask; provides the password hashing utilities (`generate_password_hash`, `check_password_hash`) |

Install all of them in one pip install command. After installation, freeze the list of installed packages into a `requirements.txt` file inside `BACKEND/`. This file lets any other developer reproduce your exact environment by running `pip install -r requirements.txt`.

---

### 1.5 Verify the Flask Installation

Create a temporary `hello.py` file anywhere in the project, write the minimal three lines needed to create a Flask app and run it, then visit `http://127.0.0.1:5000` in your browser. If you see any response from Flask, your environment is correctly set up. Delete `hello.py` before proceeding.

---

## 2. Backend Implementation

### 2.1 Configuration File — `BACKEND/config.py`

This file is the single place where all environment-specific settings live. Nothing else in the codebase should hard-code sensitive values.

**What to store here:**

- **Secret key** — a long, random string that Flask uses to cryptographically sign session cookies. If this key is ever changed, all existing sessions are invalidated. Pick something long (at least 24 random characters) and treat it like a password.
- **Database path** — the file path pointing to where `banking.db` will be created on disk. Using a config variable means you can swap in a different database file for testing without touching application code.
- **Debug flag** — a boolean that enables verbose error pages when `True`. Must be `False` in any non-development environment.

---

### 2.2 Database Layer — `BACKEND/database/db.py`

This file is the only place in the entire application that talks directly to SQLite. No other file should import the `sqlite3` module or issue SQL statements.

**Responsibilities of this file:**

1. **Open a connection** — provide a function that opens and returns an SQLite connection to `banking.db`. Configure the connection so it returns rows as dictionary-like objects (using `row_factory = sqlite3.Row`), which makes it easy to access columns by name rather than index.

2. **Initialise the schema** — provide a function that creates the two tables below if they do not already exist. Call this once at application startup.

   **`customers` table** — stores one row per registered bank customer.

   | Column | Type | Notes |
   |---|---|---|
   | `id` | Integer, primary key | Auto-incremented unique identifier |
   | `username` | Text, unique, not null | The value the customer types to log in |
   | `password_hash` | Text, not null | The bcrypt/werkzeug hash of the password, never plain text |
   | `full_name` | Text, not null | Display name shown on the dashboard |
   | `balance` | Real, default 0.0 | Current account balance |

   **`transactions` table** — stores one row for every deposit or withdrawal ever made.

   | Column | Type | Notes |
   |---|---|---|
   | `id` | Integer, primary key | Auto-incremented |
   | `customer_id` | Integer, foreign key | References `customers.id` |
   | `type` | Text | Either `'deposit'` or `'withdrawal'` |
   | `amount` | Real, not null | The amount moved in this transaction |
   | `timestamp` | Text | ISO-format date-time string recorded at write time |

3. **Seed a test customer** — provide a function that inserts one customer record only if the `customers` table is empty. This gives you a known username/password to log in with during development without needing a registration form.

4. **Query helpers** — provide small wrapper functions (`get_one`, `execute_write`) that centralise error handling around database calls and ensure connections are always closed after use.

---

### 2.3 Flask Application Entry Point — `BACKEND/app.py`

This is the file you run to start the application. Think of it as the wiring diagram that pulls every piece together.

**What it does, in order:**

1. Import Flask and create the application instance.
2. Load settings from `config.py` into the Flask app's configuration dictionary.
3. Tell Flask where to find HTML templates — point it at `FRONTEND/templates/`.
4. Tell Flask where to find static files (CSS, JS) — point it at `FRONTEND/static/`.
5. Call the database initialisation function so tables and seed data exist before any request arrives.
6. Import and register each Blueprint (auth, dashboard, transactions) so Flask knows about all the URL routes.
7. Add a root route (`/`) that immediately redirects visitors to `/login`.
8. At the bottom, include the standard `if __name__ == '__main__': app.run(...)` block so the app starts when you run the file directly.

---

### 2.4 Routes

Routes are the HTTP address-to-function mappings. Flask uses **Blueprints** to group related routes into separate files so the codebase stays organized. Each route file is a thin layer — it receives the HTTP request, calls a service function to do the actual work, and returns an HTTP response (either a rendered HTML page or a redirect).

#### Auth Routes — `BACKEND/routes/auth.py`

Create a Blueprint named `auth` with the URL prefix `/`.

**`GET /login`**
- Purpose: Show the login form to the user.
- Logic: If the user is already logged in (session contains a `user_id`), redirect them directly to `/dashboard` so they do not see a login form they do not need. Otherwise, render `login.html`.

**`POST /login`**
- Purpose: Process the submitted login form.
- Logic: Read the `username` and `password` fields from the form. Pass them to the auth service for verification. If the service confirms they are valid, store the returned customer ID and full name in the Flask session, then redirect to `/dashboard`. If verification fails, re-render the login page with a clear error message.

**`GET /logout`**
- Purpose: End the user's session.
- Logic: Call `session.clear()` to wipe all session data, then redirect to `/login`. No template rendering needed.

---

#### Dashboard Route — `BACKEND/routes/dashboard.py`

Create a Blueprint named `dashboard` with the URL prefix `/`.

**`GET /dashboard`**
- Purpose: Show the authenticated customer their account summary.
- Logic: Apply the session guard (see Section 2.6). Read the `customer_id` from the session. Call the account service to retrieve the current balance and customer name. Pass those values to `dashboard.html` for rendering.

---

#### Transaction Routes — `BACKEND/routes/transactions.py`

Create a Blueprint named `transactions` with the URL prefix `/`.

**`GET /deposit`**
- Purpose: Show the deposit form.
- Logic: Apply the session guard. Render `deposit.html`.

**`POST /deposit`**
- Purpose: Process a deposit submission.
- Logic: Apply the session guard. Read the `amount` field from the form. Pass it and the `customer_id` from the session to the account service. If the service returns success, flash a success message and redirect to `/dashboard`. If the service returns a validation error, re-render the deposit form with the error message displayed.

**`GET /withdraw`**
- Purpose: Show the withdrawal form.
- Logic: Same pattern as GET /deposit but renders `withdraw.html`.

**`POST /withdraw`**
- Purpose: Process a withdrawal submission.
- Logic: Same pattern as POST /deposit but calls the withdrawal function in the account service, which includes a balance sufficiency check.

---

### 2.5 Services

Service files contain all business logic. Routes call services; services call the database layer. Services have no knowledge of HTTP — they neither read Flask's `request` object nor call `render_template`. This separation means you can test the business rules without spinning up a web server.

#### Auth Service — `BACKEND/services/auth_service.py`

**`verify_login(username, password)`**
- Look up the customer record in the database by `username`.
- If no record is found, return a failure result immediately (do not reveal which part was wrong — say "invalid credentials" generically to avoid leaking information).
- If a record is found, use Werkzeug's `check_password_hash` to compare the submitted password against the stored hash.
- If they match, return the customer's `id` and `full_name` so the route can store them in the session.
- If they do not match, return a failure result.

**`hash_password(plain_text_password)`**
- A utility used during database seeding. Call Werkzeug's `generate_password_hash` and return the result. Never store the plain text password anywhere.

---

#### Account Service — `BACKEND/services/account_service.py`

**`get_balance(customer_id)`**
- Query the `customers` table for the row matching `customer_id`.
- Return the `balance` column value.

**`deposit(customer_id, amount)`**
- Validate that `amount` is a positive number greater than zero. If not, return an error result.
- Read the current balance from the database.
- Add `amount` to the current balance.
- Write the new balance back to the database (UPDATE statement).
- Insert a new row into the `transactions` table with type `'deposit'`, the amount, and the current timestamp.
- Both writes must happen inside a single database transaction so that if the log write fails, the balance update is also rolled back.
- Return a success result.

**`withdraw(customer_id, amount)`**
- Validate that `amount` is a positive number greater than zero. If not, return an error result.
- Read the current balance from the database.
- Check that `balance >= amount`. If not, return an "insufficient funds" error.
- Subtract `amount` from the current balance.
- Write the new balance back to the database.
- Insert a row into `transactions` with type `'withdrawal'`.
- Again, both writes in one atomic database transaction.
- Return a success result.

---

### 2.6 Session Management

Flask's built-in `session` object is a server-signed cookie stored in the browser. Because it is signed with the secret key, the client cannot tamper with its contents.

**What to store in the session:**
- `session['user_id']` — the integer primary key of the logged-in customer.
- `session['full_name']` — the display name, used in templates without an extra DB query.

**The session guard (login-required decorator):**

Write a reusable Python decorator called `login_required`. When applied to a route function, it runs before the route's own logic and checks whether `session['user_id']` exists. If it does, the route runs normally. If it does not, the decorator immediately redirects the request to `/login`. Apply this decorator to every route except the login and logout routes.

**Session expiry:**

Set Flask's `PERMANENT_SESSION_LIFETIME` in `config.py` to a reasonable duration (e.g. 30 minutes). Call `session.permanent = True` after a successful login to enable the timeout.

---

### 2.7 Error Handling

Register custom error handlers in `app.py` for the two most common HTTP error codes:

- **404 Not Found** — render a simple "Page not found" page with a link back to the dashboard.
- **500 Internal Server Error** — render a "Something went wrong" page that does not expose stack traces to the user.

In development mode, Flask's default error pages (which include stack traces) are more useful — the custom handlers only matter when `DEBUG = False`.

For user-facing errors such as invalid form input or failed transactions, use Flask's `flash()` mechanism: store the message in the session, then display it at the top of the next rendered page. This pattern works cleanly with the redirect-after-POST approach.

---

## 3. Frontend Implementation

All HTML files live in `FRONTEND/templates/`. Flask's Jinja2 engine renders them on the server and sends finished HTML to the browser. The frontend never makes background API calls — every interaction is a standard form submission followed by a full page load.

### 3.1 Base Layout — `base.html`

This is the master template that every other page inherits from. Building it first means you only write the common structure once.

**What to include:**

1. **HTML5 doctype and `<head>`** — include the Bootstrap CSS link (via CDN or a local file placed in `FRONTEND/static/css/`), the page title (using a Jinja2 block so each child page can set its own title), and a link to `custom.css`.

2. **Navigation bar** — a Bootstrap `navbar` that shows the application name on the left. On the right, conditionally show either a "Logout" link (when a user is logged in) or nothing. Use Jinja2's `{% if session['user_id'] %}` conditional to drive this visibility.

3. **Flash message area** — loop over any messages stored by Flask's `flash()` function and render each one as a Bootstrap alert (`alert-success` for success, `alert-danger` for errors). Place this block below the navbar so it appears at the top of every page.

4. **Content block** — a `{% block content %}{% endblock %}` placeholder where child templates inject their page-specific HTML.

5. **Footer** — a minimal footer with the bank name and year.

---

### 3.2 Login Page — `login.html`

**Purpose:** Collect a username and password and submit them to `POST /login`.

**Layout logic:**

- Extend `base.html`.
- Center the form on the page using Bootstrap's grid system (`col-md-4 offset-md-4` or similar).
- The form contains two input fields: one for username (type `text`) and one for password (type `password`).
- A submit button labelled "Sign In".
- The form's `action` attribute points to the login URL and the `method` is `POST`.
- Display any error messages passed from the backend (via `flash` or a template variable) above the form in a red Bootstrap alert.
- No link to a registration page is needed (registration is out of scope).

---

### 3.3 Dashboard Page — `dashboard.html`

**Purpose:** Greet the logged-in customer and show their current balance with action buttons.

**Layout logic:**

- Extend `base.html`.
- At the top, show a welcome message using the customer's full name (passed from the route as a template variable).
- Display the current balance prominently — use a large Bootstrap card or jumbotron-style container. Format the number to two decimal places.
- Below the balance, show two Bootstrap buttons: "Deposit" (links to `/deposit`) and "Withdraw" (links to `/withdraw`).
- The dashboard is read-only — it shows data but has no forms of its own.

---

### 3.4 Deposit Form — `deposit.html`

**Purpose:** Allow the customer to enter a deposit amount and submit it.

**Layout logic:**

- Extend `base.html`.
- Center the form, similar to the login page.
- A single numeric input field for the amount. Use `type="number"` with `step="0.01"` and `min="0.01"` attributes to discourage non-positive entries at the browser level (backend validation is the real guard).
- A submit button labelled "Deposit".
- The form posts to `/deposit`.
- Show any error or success messages from the backend above the form.
- A "Back to Dashboard" link below the form for easy navigation.

---

### 3.5 Withdraw Form — `withdraw.html`

**Purpose:** Allow the customer to enter a withdrawal amount and submit it.

**Layout logic:**

- Identical structure to `deposit.html` with two differences: the heading says "Withdraw Funds", the form posts to `/withdraw`, and the submit button is labelled "Withdraw".

---

### 3.6 Bootstrap Layout Principles

- Use Bootstrap's 12-column grid (`container`, `row`, `col-*`) for all page layouts.
- Form elements should use Bootstrap's `form-control` class for consistent styling.
- Buttons should use `btn btn-primary` (blue, for the main action) and `btn btn-secondary` (grey, for secondary links).
- All flash messages use `alert alert-dismissible` with a close button so the user can dismiss them.
- The application should look reasonable on mobile by using responsive column classes (e.g. `col-12 col-md-6`).

---

## 4. Integration Steps

### 4.1 Connect Frontend Templates to Flask Routes

Templates and routes are connected through Flask's `url_for()` function. Instead of hard-coding URLs like `/login` in your HTML, write `url_for('auth.login')`. This means if you ever rename a route, links throughout the application update automatically.

**Key integration points to verify:**

- The login form's `action` attribute uses `url_for('auth.login')`.
- The logout link in `base.html` uses `url_for('auth.logout')`.
- The "Deposit" and "Withdraw" buttons on the dashboard use `url_for('transactions.deposit')` and `url_for('transactions.withdraw')`.
- After a successful POST (login, deposit, withdraw), the route uses `redirect(url_for(...))` rather than rendering a template directly. This prevents duplicate form submissions on browser refresh (the POST-Redirect-GET pattern).

---

### 4.2 Connect Flask to SQLite

The database connection is established in `db.py` and consumed by the service layer. The integration works as follows:

1. When `app.py` starts, it calls `init_db()` from `db.py`. This creates `banking.db` on disk (if it does not already exist) and runs the `CREATE TABLE IF NOT EXISTS` statements.
2. The `seed_db()` function in `db.py` is called right after `init_db()`. It checks whether the `customers` table is empty, and if so, inserts one test user with a hashed password.
3. Every service function that needs database access calls `get_connection()` from `db.py`, uses the returned connection, and closes it before returning.
4. To avoid leaving connections open on errors, use Python's `try/finally` pattern: do the database work in the `try` block, and call `connection.close()` in the `finally` block so it runs regardless of whether an error occurred.

---

### 4.3 Register Flask Blueprints

In `app.py`, import each Blueprint object from its route file and register it with the Flask `app` object. This step is what makes Flask aware of the routes defined in `auth.py`, `dashboard.py`, and `transactions.py`. Forgetting to register a Blueprint is a common mistake that causes 404 errors — if a route is unreachable, check that its Blueprint is registered here.

---

### 4.4 Template Folder and Static Folder Configuration

By default, Flask looks for templates in a `templates/` folder next to `app.py`. Because this project keeps templates under `FRONTEND/templates/`, you must explicitly pass the path when creating the Flask app instance using the `template_folder` and `static_folder` parameters. Use Python's `os.path` utilities (or `pathlib`) to build these paths relative to `app.py`'s location so the application works regardless of where it is run from.

---

## 5. Validation Rules

Validation happens at two levels: the browser (HTML attributes, basic UX) and the server (Flask route / service, security). The server-side rules are authoritative — browser validation can be bypassed.

### 5.1 Login Validation

| Rule | Where enforced | What happens on failure |
|---|---|---|
| Username field must not be empty | Server (auth service) | Re-render login with "Please enter a username" |
| Password field must not be empty | Server (auth service) | Re-render login with "Please enter a password" |
| Username must exist in the database | Server (auth service) | Re-render login with "Invalid username or password" |
| Password must match stored hash | Server (auth service) | Re-render login with "Invalid username or password" |

> **Security note:** Always use the same generic error message for both "username not found" and "wrong password". A specific message would tell an attacker whether a username exists.

---

### 5.2 Balance Validation

| Rule | Where enforced | Notes |
|---|---|---|
| Balance displayed on dashboard is always read fresh from the DB | Account service | Prevents stale data being shown after a transaction |
| Balance column in DB has a default of 0.0 and cannot be NULL | Database schema | Prevents NULL arithmetic errors |

---

### 5.3 Deposit Validation

| Rule | Where enforced | What happens on failure |
|---|---|---|
| Amount field must not be empty | Server (account service) | Re-render deposit form with error |
| Amount must be a valid number | Server (route, before passing to service) | Re-render with "Please enter a valid amount" |
| Amount must be greater than zero | Server (account service) | Re-render with "Deposit amount must be positive" |
| Amount must not exceed a reasonable maximum (optional, e.g. 1,000,000) | Server (account service) | Re-render with "Amount exceeds maximum limit" |

---

### 5.4 Withdrawal Validation

| Rule | Where enforced | What happens on failure |
|---|---|---|
| Amount field must not be empty | Server (account service) | Re-render withdraw form with error |
| Amount must be a valid number | Server (route) | Re-render with "Please enter a valid amount" |
| Amount must be greater than zero | Server (account service) | Re-render with "Withdrawal amount must be positive" |
| `current_balance >= amount` | Server (account service) | Re-render with "Insufficient funds" |

> **Concurrency note:** The balance check and the balance update must happen inside a single SQLite transaction (using `BEGIN`/`COMMIT`). This prevents a race condition where two simultaneous withdrawal requests both see a sufficient balance and both succeed, resulting in a negative balance.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests verify individual functions in isolation without a running web server or real database.

**What to write unit tests for:**

- `verify_login` in `auth_service.py` — test with a correct password, a wrong password, and a non-existent username. Each should return the expected result.
- `hash_password` — verify the returned value is not the plain text and that `check_password_hash` against it returns `True`.
- `deposit` in `account_service.py` — test with valid positive amounts, zero, negative numbers, and non-numeric strings.
- `withdraw` in `account_service.py` — test with valid amounts, insufficient balance, zero, and negative numbers.

**How to isolate from the database:**

Use Python's `unittest.mock` library to replace the `get_connection()` database calls with mock objects that return pre-set data. This lets you test service logic without touching any real database file.

---

### 6.2 Integration Tests

Integration tests verify that the full request-response cycle works correctly, from HTTP request through Flask routing and service logic down to an actual (test) database.

**How to set up:**

Use Flask's built-in `test_client()`. Before each test, call `init_db()` against a temporary in-memory SQLite database (`:memory:`), then seed it with a known test user. After each test, tear down the database. This ensures every test starts from a clean, predictable state.

**What to write integration tests for:**

- `GET /login` returns a 200 status and the login form is present in the HTML.
- `POST /login` with correct credentials redirects to `/dashboard`.
- `POST /login` with incorrect credentials returns the login page with an error.
- `GET /dashboard` without a session redirects to `/login`.
- `GET /dashboard` with a valid session returns 200 and shows the balance.
- `POST /deposit` with a valid amount updates the balance and redirects to `/dashboard`.
- `POST /deposit` with an invalid amount (negative, zero, text) returns the deposit form with an error.
- `POST /withdraw` with sufficient funds updates the balance and redirects.
- `POST /withdraw` with insufficient funds returns the form with "Insufficient funds".
- `GET /logout` clears the session and redirects to `/login`.

---

### 6.3 Manual Testing Checklist

Run through this checklist in the browser before considering the application complete.

**Authentication flow:**
- [ ] Visiting `/dashboard` without logging in redirects to `/login`.
- [ ] Logging in with incorrect credentials shows an error and stays on `/login`.
- [ ] Logging in with correct credentials redirects to `/dashboard` and shows the customer's name and balance.
- [ ] Clicking "Logout" clears the session; pressing the browser back button after logout does not restore the authenticated state.

**Deposit flow:**
- [ ] Navigating to `/deposit` while logged in shows the deposit form.
- [ ] Submitting a positive amount updates the balance on the dashboard (reload to confirm).
- [ ] Submitting an empty form shows a validation error.
- [ ] Submitting a negative number shows a validation error.
- [ ] Submitting text (e.g. "abc") shows a validation error.

**Withdrawal flow:**
- [ ] Submitting a valid amount less than the balance updates the balance correctly.
- [ ] Submitting an amount equal to the balance brings the balance to exactly 0.00.
- [ ] Submitting an amount greater than the balance shows "Insufficient funds".
- [ ] Submitting zero or a negative number shows a validation error.

**UI/UX checks:**
- [ ] All pages render correctly at a standard desktop width.
- [ ] All pages render usably on a mobile-sized viewport (use browser DevTools to simulate).
- [ ] Flash messages appear after deposit and withdrawal and are dismissible.
- [ ] Navigation links (Deposit, Withdraw, Logout) work from the dashboard.

---

## 7. Deployment

### 7.1 Run Locally

Running locally means the application is accessible only on your own machine. This is the default development workflow.

**Steps:**

1. Open a terminal and navigate to the `BACKEND/` folder.
2. Activate the virtual environment.
3. Run `python app.py`.
4. Flask will print the local URL (typically `http://127.0.0.1:5000`).
5. Open that URL in your browser.
6. To stop the server, press `Ctrl + C` in the terminal.

**Debug mode:**

While developing, set `DEBUG = True` in `config.py`. This enables:
- Automatic server restart when you save a Python file (so you do not need to manually stop and restart).
- Detailed in-browser error pages showing the full stack trace.

**Important:** Always set `DEBUG = False` before sharing the application with anyone or deploying it to any non-local environment.

---

### 7.2 Production Considerations

Flask's built-in development server is not suitable for production use. It is single-threaded, unoptimised, and lacks security hardening. Before running this application for real users, address the following points.

**Use a production WSGI server:**

Replace `python app.py` with a production-grade server such as **Gunicorn** (Linux/macOS) or **Waitress** (Windows). These servers can handle multiple concurrent requests and are designed for stability under real traffic. You install them with pip and point them at the Flask app object in `app.py`.

**Move secrets out of code:**

The secret key in `config.py` must not be committed to version control (Git). Move it to an environment variable and read it at runtime using `os.environ.get('SECRET_KEY')`. Use a `.env` file and a library like `python-dotenv` to load it locally, but never commit the `.env` file.

**Add HTTPS:**

All traffic between the browser and server should be encrypted. For a local internal deployment, use a reverse proxy such as **Nginx** in front of Gunicorn/Waitress and terminate TLS at the proxy. Self-signed certificates are acceptable for internal use; Let's Encrypt provides free certificates for public domains.

**Database considerations:**

SQLite is sufficient for a single-server deployment with low concurrent users. If traffic grows or you need multi-server redundancy, migrate to PostgreSQL. The service/database layer separation in this architecture makes that migration straightforward — only `db.py` needs to change.

**Session security in production:**

- Keep `SESSION_COOKIE_HTTPONLY = True` (prevents JavaScript from reading the session cookie).
- Set `SESSION_COOKIE_SECURE = True` when HTTPS is available (prevents the cookie being sent over plain HTTP).
- Set `SESSION_COOKIE_SAMESITE = 'Lax'` to mitigate cross-site request forgery (CSRF) risks.

**Logging:**

Configure Python's standard `logging` module to write errors and important events to a log file. In production, you want a record of failed login attempts, transaction errors, and unexpected exceptions so you can diagnose problems without a debugger.

---

*End of Step-by-Step Implementation Guide.*
*Refer to `IMPLEMENTATION_PLAN.md` for the high-level architecture and phased roadmap that this guide is based on.*
