# File: `app/__init__.py`

## Overview
This file serves as the **Application Factory** for the Flask application. It initializes the app, configuring extensions, blueprints, and template filters.

## Functions

### `create_app(config_name='default')`
*   **Purpose**: Creates and configures the Flask application instance.
*   **Arguments**:
    *   `config_name` (str): The configuration environment to use (default: 'default').
*   **Process**:
    1.  Initializes `Flask` app.
    2.  Loads configuration from `config.py`.
    3.  Initializes extensions (`db`, `migrate`, `login_manager`).
    4.  Registers template filter `b64encode`.
    5.  Registers Blueprints (`main`, `auth`, `admin`, `faculty`, `student`).
*   **Returns**: The configured `app` instance.

### `b64encode_filter(data)`
*   **Purpose**: Custom Jinja2 filter to base64 encode binary data (used for image rendering).
*   **Arguments**: `data` (bytes).
*   **Returns**: UTF-8 string of base64 encoded data.

## Blueprints Registered
*   `main_bp`: `/`
*   `auth_bp`: `/auth`
*   `admin_bp`: `/admin`
*   `faculty_bp`: `/faculty`
*   `student_bp`: `/student`
