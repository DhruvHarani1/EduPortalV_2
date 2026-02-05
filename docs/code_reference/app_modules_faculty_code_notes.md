# detailed_technical_reference: app/modules/faculty/routes.py

## File Overview
The Faculty Module is the "Input Terminal" of the system. It handles high-volume data entry (Attendance, Marks) and communication. The code is optimized for **Batch Processing** to minimize database transactions.

---

## Route: `/attendance` (GET, POST)

### Purpose
A dual-mode interface for viewing history and performing bulk attendance marking.

### Logic Breakdown

#### Mode 1: Marking (POST)
*   **Batch Key Parsing**:
    *   The form submits radio buttons named dynamically as `status_{student_id}` (e.g., `status_101='Present'`, `status_102='Absent'`).
    *   **Algorithm**:
        *   Iterate `request.form` keys.
        *   If key starts with `status_`:
            *   Extract `student_id`.
            *   Check if `Attendance` record exists for `(Student, Subject, Date)`.
            *   **Upsert Logic**:
                *   If Exists: Update `.status`.
                *   If New: Create `Attendance()` object.
*   **Result**: Redirects back to the same view ("Sticky Form") to allow rapid adjustments.

#### Mode 2: Low Attendance Analysis
*   Calculates the "Red List" (Students < 75%) dynamically on the marking page.
*   **Algorithm**:
    *   Fetches ALL attendance records for the selected subject.
    *   Aggregates in Python: `{ student_id: { 'total': X, 'present': Y } }`.
    *   Filters students where `(Y/X) < 0.75`.
    *   *Display*: Highlights these students in the marking list to alert the faculty.

---

## Route: `/marks` (GET, POST)

### Purpose
Bulk entry of exam scores.

### Logic Breakdown
1.  **Security Scope**:
    *   Filters `ExamPaper` list to only show subjects **taught by the logged-in faculty**.
    *   Prevents faculty from modifying marks for subjects they don't own.
2.  **Batch Entry (POST)**:
    *   Similar to attendance, inputs are named `marks_{student_id}`.
    *   **Validation**:
        *   Checks if `Input Marks` > `Paper.total_marks`.
        *   If invalid, flashes error and skips that specific record (doesn't crash entire batch).
3.  **Fail Status Calculation**:
    *   System automatically sets `is_fail=True` if `Marks < (Total * 0.33)`.
    *   This logic is centralized here to ensure consistency across all exams.

---

## Route: `/dashboard` (GET)

### Purpose
Landing page logic.

### Logic
*   **Today's Schedule**:
    *   Fetches `Timetable` for `Current Weekday`.
    *   **Attendance Check**:
        *   For each class slot, queries `Attendance` table for `date=today`.
        *   Sets `entry.attendance_marked = True` if records exist.
        *   *UI Effect*: Shows a green checkmark or red "Mark Now" button.
