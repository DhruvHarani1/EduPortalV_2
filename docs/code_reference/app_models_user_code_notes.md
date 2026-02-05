# File: `app/models/user.py`

## Overview
Defines the `User` model, which handles authentication and authorization. It separates high-level auth credentials from specific role-based profiles.

## Functions

### `load_user(user_id)`
*   **Decorator**: `@login_manager.user_loader`
*   **Purpose**: Callback for Flask-Login to reload the user object from the user ID stored in the session.
*   **Returns**: `User` object.

## Classes

### `User(UserMixin, db.Model)`
*   **Table Name**: `users`
*   **Description**: The core identity entity.

#### Attributes (Columns)
*   `id` (Integer, PK): Unique identifier.
*   `email` (String, Unique): Username/Login email.
*   `password_hash` (String): Securely hashed password.
*   `role` (String): Authorization level ('admin', 'student', 'faculty').

#### Methods
*   `set_password(password)`: Hashes and stores the password.
*   `check_password(password)`: Verifies a plaintext password against the hash (Returns `True`/`False`).
*   `__repr__()`: String representation (`<User email>`).
