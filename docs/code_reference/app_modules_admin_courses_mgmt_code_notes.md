# File: `app/modules/admin/courses_mgmt.py`

## Overview
CRUD operations for **Courses** (Degree Programs like B.Tech, MBA).

## Routes

### `/courses` (GET)
*   **Purpose**: List all courses ordered by code.
*   **Returns**: `courses_list.html`.

### `/courses/add` (GET, POST)
*   **Purpose**: Add a new degree program.
*   **Logic**:
    *   Checks if `code` already exists (Unique constraint).
    *   Creates `Course` object with `duration_years` and `total_semesters`.
*   **Returns**: Redirects to list on success.

### `/courses/delete/<int:id>` (POST)
*   **Purpose**: Delete a course.
*   **Logic**: DB Session delete. (Note: May fail if foreign keys exist, needs handling).
