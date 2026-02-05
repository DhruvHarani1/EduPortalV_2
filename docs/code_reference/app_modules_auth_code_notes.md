# detailed_technical_reference: app/modules/auth/routes.py

## File Overview
This module guards the application gates. It handles **Identity Verification** and **Role-Based Access Control (RBAC)** enforcement during the login process.

---

## Route: `/login` (POST)

### Purpose
Authenticates users and directs them to their specific portal (Admin vs Faculty vs Student).

### Logic Breakdown

#### 1. Input Processing
*   **Hidden Field**: The form submits a hidden `role` field (e.g., 'student'). This is set by the initial GET request query param (`?role=student`).

#### 2. Authentication
*   **User Lookup**: `User.query.filter_by(email=email).first()`.
*   **Hash Verification**: `user.check_password(password)` (Uses `werkzeug.security.check_password_hash`).

#### 3. Authorization (Strict RBAC)
*   **The Check**: `if user.role != role:`
*   **Why**: Defines the security boundary.
    *   *Scenario*: A valid Student credentials (email/pass) *cannot* be used to log in via the Faculty Login page.
    *   *Action*: Flashes "Access Denied" even if the password is correct, preventing role confusion or privilege escalation attacks via the wrong portal.

#### 4. Redirection Logic
*   Routes the user based on their stored `user.role`:
    *   `admin` -> `admin.dashboard`
    *   `faculty` -> `faculty.dashboard`
    *   `student` -> `student.dashboard`

---

## Route: `/logout` (GET)

### Purpose
Session termination.

### Logic
*   Calls `logout_user()` (Flask-Login).
*   Clears the session cookie.
*   Redirects to the public landing page.
