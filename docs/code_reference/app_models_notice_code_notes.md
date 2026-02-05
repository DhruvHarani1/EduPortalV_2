# detailed_technical_reference: app/models/notice.py

## File Overview
This module defines the **Notification Entity**, which supports a complex **Polymorphic Targeting System** to deliver alerts to specific subsets of users.

---

## Class: `Notice` (db.Model)

### Purpose
A system-wide or targeted announcement.

### Targeting Logic (Polymorphism)
Instead of a separate link table for targets, this model uses a **Single Table Inheritance** style strategy for targeting columns:

1.  **Broadcast Mode**:
    *   `target_type = 'all'`.
    *   All "Target" FK columns are NULL.
    *   *Query*: `Notice.query.filter_by(target_type='all')`.

2.  **Cohort Mode (Class)**:
    *   `target_type = 'class'`.
    *   `target_course`: Populated (e.g., "B.Tech").
    *   `target_semester`: Optional.
    *   *Query*: `Notice.query.filter(target_course=student.course_name)`.

3.  **Faculty Mode**:
    *   `target_type = 'faculty'`.
    *   `target_faculty_id`: Populated (Specific) OR None (All Faculty).
    *   *Query*: `Notice.query.filter(target_faculty_id=current_user.id)`.

4.  **Individual Mode**:
    *   `target_type = 'individual'`.
    *   `target_student_id`: Populated.

### Relationships
*   `sender`: Links to `FacultyProfile`. If NULL, the sender is assumed to be the **System Admin**.
*   `target_student` / `target_faculty`: Helper relationships to fetch the actual recipient object if needed.
