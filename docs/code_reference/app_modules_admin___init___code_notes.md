# File: `app/modules/admin/__init__.py`

## Overview
Initializes the **Admin Blueprint** and registers its sub-modules (routes and separate management files).

## Variables
*   `admin_bp`: The Flask Blueprint object for the admin module.
*   **Sub-Blueprints Registered**:
    *   `exams_bp` (from `exams_mgmt`)
    *   `subjects_bp` (from `subjects_mgmt`)
    *   `reports_bp` (from `reports_mgmt`)

## Usage
Imported by `app/__init__.py` to mount the admin dashboard at `/admin`.
