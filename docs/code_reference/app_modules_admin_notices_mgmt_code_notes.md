# detailed_technical_reference: app/modules/admin/notices_mgmt.py

## File Overview
This module manages the **Notification System**, handling the creation and targeting of alerts. It supports a sophisticated targeting mechanism (Broadcast vs. Cohort-Specific vs. Individual).

---

## Route: `/notices` (GET)

### Purpose
View all active notices in the system.

### Logic
*   **Ordering**: `order_by(Notice.created_at.desc())` ensures the newest announcements appear at the top.

---

## Route: `/notices/add` (POST)

### Purpose
The notification publishing engine.

### Logic Breakdown (Targeting System)
The system determines the `target_type` based on the selected `category`:

1.  **Broadcast (Category: 'general')**
    *   **Logic**: `target_type = 'all'`.
    *   **Effect**: Visible to every user in the system.

2.  **Cohort Targeting (Category: 'course')**
    *   **Input**: `target_course` (e.g., "B.Tech").
    *   **Logic**:
        *   Sets `target_type = 'class'`.
        *   Stores `target_course` in the record.
    *   **Effect**: Only students matching `Student.course_name == target_course` will see this.

3.  **Faculty Targeting (Category: 'faculty')**
    *   **Input**: `target_faculty_id`.
    *   **Logic**:
        *   Sets `target_type = 'faculty'`.
        *   Stores `target_faculty_id`.
    *   **Effect**: Only the specific faculty member (or all faculty if ID is null/special) receives the message.

### Validation
*   **Guard Clauses**: Prevents creating a "Course" notice without selecting a course, or a "Faculty" notice without selecting a recipient.
*   **Debug Logging**: Contains a `print()` statement for tracing flow during development.
