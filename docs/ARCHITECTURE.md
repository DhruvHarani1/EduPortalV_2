# System Architecture Documentation

## 1. High Level Overview

**EduPortal** is a monolithic web application built on the **Flask** microframework (Python). It utilizes a **Server-Side Rendering (SSR)** architecture where the backend generates HTML templates via **Jinja2**, styled with **TailwindCSS**.

### Core Technology Stack
*   **Backend Runtime**: Python 3.9+
*   **Web Framework**: Flask 2.3+
*   **Database ORM**: SQLAlchemy (with SQLite/PostgreSQL support)
*   **Frontend**: Jinja2 Templates + TailwindCSS (via CDN)
*   **Authentication**: Flask-Login (Session based)

---

## 2. Directory Structure & Organization

The codebase follows the **Application Factory Pattern** to ensure scalability and easier testing.

```text
EDU-PORTAL/
├── app/
│   ├── __init__.py         # App Factory (create_app function)
│   ├── extensions.py       # Global extensions (db, login_manager, migrate)
│   ├── models/             # Database Models (ORM Definitions)
│   │   ├── user.py         # Auth System
│   │   ├── profiles.py     # Student/Faculty Profiles
│   │   └── academics.py    # Exams, Attendance, Subjects
│   ├── admin/              # [Blueprint] Admin Module
│   │   ├── routes.py       # Controllers for Admin
│   │   └── templates/      # Admin Views
│   ├── auth/               # [Blueprint] Authentication Module
│   ├── student/            # [Blueprint] Student Portal
│   └── faculty/            # [Blueprint] Faculty Portal
├── docs/                   # Documentation
├── scripts/                # Utility Scripts (Seeding, Resets)
├── config.py               # Environment Configuration
└── run.py                  # Entry Point (WSGI)
```

### Key Design Decisions

#### The Application Factory (`app/__init__.py`)
Instead of a global `app` object, we define a function `create_app(config_name)`.
*   **Why?**: Allows creating multiple instances of the app with different configs (e.g., `TestConfig` vs `DevConfig`).
*   **Flow**:
    1.  Initialize Flask.
    2.  Load Config from `config.py`.
    3.  Initialize Extensions (`db.init_app(app)`).
    4.  Register Blueprints (`app.register_blueprint(admin_bp)`).

#### Blueprints (Modular Architecture)
The app is sliced into functional domains:
*   **Auth**: Login, Logout, Password Reset.
*   **Admin**: Global control, report generation, user management.
*   **Student/Faculty**: Specific role-based views.

**Benefit**: Code isolation. `admin/routes.py` only handles admin logic, preventing a massive 5000-line `app.py` file.

---

## 3. Data Flow Architecture

### Request-Response Cycle
1.  **Incoming Request**: Nginx/Gunicorn -> Flask WSGI.
2.  **Routing**: Flask URL Map matches `/admin/dashboard` -> `admin.dashboard` view function.
3.  **Middleware (Decorators)**:
    *   `@login_required`: Checks `session['user_id']`.
    *   `@role_required('admin')`: customized decorator checks `current_user.role`.
4.  **Controller Logic**:
    *   Query Database via **SQLAlchemy Session**.
    *   Perform Business Logic (e.g., Calculate 'Equity Score').
5.  **View Rendering**:
    *   Controller passes a Context Dictionary (vars) to `render_template`.
    *   Jinja2 compiles HTML.
6.  **Response**: HTML sent to browser.

---

## 4. Database Design Strategy

We use **Code-First Migrations** via Flask-Migrate (Alembic).

### Core Relationships
*   **User (Auth)** Is Parent of **Profile (Data)**.
    *   `User.id` 1:1 `StudentProfile.user_id`
*   **Faculty** 1:N **Subject**
    *   Faculty teaches many subjects.
*   **Student** has Many **Attendance Records**
*   **ExamEvent** 1:N **ExamPaper** 1:N **Result**

*See `DATABASE_SCHEMA.md` for indepth model breakdown.*
