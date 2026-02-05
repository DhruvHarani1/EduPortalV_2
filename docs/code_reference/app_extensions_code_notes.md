# File: `app/extensions.py`

## Overview
This file serves as a central registry for Flask extensions. By initializing them here without the `app` object, we avoid circular import dependencies (the "Application Factory" pattern).

## Variables / Extensions

### `db`
*   **Type**: `SQLAlchemy()`
*   **Purpose**: The Overarching ORM object. Used to define models (`db.Model`) and execute queries (`db.session`).

### `migrate`
*   **Type**: `Migrate()`
*   **Purpose**: Handles database migrations using Alembic. Linked to `app` and `db` in `__init__.py`.

### `login_manager`
*   **Type**: `LoginManager()`
*   **Purpose**: Manages user session management (logging in/out).
*   **Configuration**:
    *   `login_view = 'auth.login'`: Redirects unauthorized users to the login page.
