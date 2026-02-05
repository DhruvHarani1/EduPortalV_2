# File: `app/modules/admin/subjects_mgmt.py`

## Overview
CRUD for **Subjects** (Modules). Handles creation and assignment to Faculty.

## Routes

### `/subjects` (GET)
*   **Purpose**: List subjects.
*   **Returns**: `subject_list.html` (Modal support).

### `/subjects/create` (POST)
*   **Purpose**: Quick-add a subject (Name + Course/Sem).

### `/subjects/assign` (POST)
*   **Purpose**: Update a subject's mapping (Course/Sem). (Note: Faculty assignment is usually done in `faculty_mgmt`, but this updates the academic metadata).

### `/subjects/delete/<id>` (POST)
*   **Purpose**: Delete subject.
