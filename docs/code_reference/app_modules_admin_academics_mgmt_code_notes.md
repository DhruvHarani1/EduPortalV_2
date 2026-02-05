# detailed_technical_reference: app/modules/admin/academics_mgmt.py

## File Overview
This module handles the **manual management** of academic records, primarily focused on **Attendance Aggregation** for admin review and manual overrides.

---

## Route: `/attendance` (GET)

### Purpose
Displays a master list of all students with their aggregate attendance percentages.

### Logic Breakdown (SQL Aggregation)
Instead of iterating objects in Python (which is slow for N students), this route uses efficient **SQLAlchemy Grouping**.

1.  **The Query**:
    ```python
    db.session.query(
        Attendance.student_id,
        func.count(Attendance.id).label('total'),
        func.sum(case((Attendance.status == 'Present', 1), else_=0)).label('present')
    ).group_by(Attendance.student_id)
    ```
    *   `func.count`: Counts total rows per student.
    *   `func.sum(case(...))`: Conditional Sum. Adds 1 if status is 'Present', else 0.
2.  **Data Mapping**:
    *   Converts the raw SQL tuples into a dictionary: `{ student_id: {'total': 50, 'present': 40} }`.
    *   Iterates `StudentProfile` list and merges this data to calculate `%`.

---

## Route: `/attendance/mark` (POST)

### Purpose
Manual Admin Override for marking attendance (e.g., retroactively fixing a mistake).

### Logic Breakdown
*   **Inputs**: `student_id`, `course_name`, `date`, `status`.
*   **Validation**: Attempts to parse the date string.
*   **Action**: Creates a single, standalone `Attendance` record.
*   *Note*: Unlike the Faculty batch marker, this creates records one-by-one.
