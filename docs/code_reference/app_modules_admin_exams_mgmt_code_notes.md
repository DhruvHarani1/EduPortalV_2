# detailed_technical_reference: app/modules/admin/exams_mgmt.py

## File Overview
This module manages the entire Examination Lifecycle. It handles the definition of high-level **Events** (e.g., "Winter 2024"), the granular scheduling of **Papers** (Subjects), and the final **Publishing** and **Reporting** of results.

---

## Route: `/exams/create` (POST)

### Purpose
Initializes a new Exam Event.

### Logic Breakdown
1.  **Inputs**: `name`, `course`, `semester`, `dates`.
2.  **Validation**:
    *   **Date Integrity**: Checks `if end_date < start_date`. Flashes error if the timeline is impossible.
3.  **Persistence**:
    *   Creates an `ExamEvent` record.
    *   **Redirect**: Immediately pushes the user to the *Schedule* page (`/exams/<id>/schedule`) to begin adding papers.

---

## Route: `/exams/<id>/schedule` (GET, POST)

### Purpose
The core scheduling interface. Allows Admin to defining the date, time, and marks for every subject in the event's semester.

### Logic Breakdown (Batch Processing)
1.  **Pre-computation**:
    *   Fetches all `Subjects` associated with the Event's `(Course, Semester)`.
    *   Matches existing `ExamPapers` (if any) to these subjects to pre-fill the form.
2.  **Form Processing (POST)**:
    *   Iterates through *every* subject available for the semester.
    *   **Input Naming Convention**: `date_{sub_id}`, `start_{sub_id}`, `marks_{sub_id}`.
    *   **Upsert Logic**:
        *   If inputs exist for a subject:
        *   Checks if `ExamPaper` exists.
        *   **Update**: Modifies Date/Time/Marks.
        *   **Insert**: Creates new `ExamPaper`.
    *   **Defaulting**: If 'marks' is left blank, defaults to **100**.
3.  **Publishing Workflow**:
    *   Checks for a specific button action: `request.form.get('action') == 'publish'`.
    *   **Effect**: Sets `event.is_published = True`.
    *   **Significance**: Only published events are visible to Faculty (for mark entry) and Students (for results).

---

## Route: `/exams/export` (POST)

### Purpose
Generates a dynamic CSV Matrix of results for offline processing.

### Logic Breakdown

#### 1. Header Generation
*   **Static Columns**: `Enrollment No`, `Name`.
*   **Dynamic Columns**:
    *   Fetches all `ExamPapers` for the event.
    *   Sorts them by `Date`.
    *   Extracts `Subject Names` to create columns: `[Maths, Physics, Chem, ...]`.
*   **Summary Columns**: `Total Marks`, `Obtained Marks`, `Percentage`, `Status`.

#### 2. Data Matrix Construction
*   Iterates through **All Students** in the cohort.
*   For each student:
    *   Initializes a row `[Enrollment, Name]`.
    *   Iterates the *Sorted Papers* list.
    *   **Lookup**: Queries `StudentResult` for `(Student, Paper)`.
    *   **Cell Value**: Appends `marks_obtained` (or empty string if missing).
    *   **Aggregation**: Accumulates `Total Max Marks` and `Total Obtained` on the fly.
*   **Output**: Streaming `Response` with mimetype `text/csv`.

---

## Route: `/exams/<id>/recandidates` (GET)

### Purpose
Exception Reporting. Identifies students who Failed or were Absent.

### Logic Breakdown
*   **Query Filtering**:
    *   Joins `StudentResult` with `ExamPaper`.
    *   **Filter Condition**: `(Result.is_fail == True) OR (Result.status == 'Absent')`.
*   **Usage**: Used by Admins to plan Re-exams or remedial classes.
