# detailed_technical_reference: app/models/academics.py

## File Overview
This is the **Core Schema** file for the application. It defines the educational entities, their relationships, and the rules of engagement (Time, Attendance, Exams).

---

## Class: `Course`
*   **Purpose**: Represents a Degree Program (e.g., B.Tech, MBA).
*   **Key Fields**:
    *   `duration_years`: Default 4.
    *   `total_semesters`: Default 8.
*   **Constraint**: `name` and `code` must be Unique.

## Class: `Subject`
*   **Purpose**: Represents a specific module (e.g., Data Structures).
*   **Assignments**: can be optionally linked to a `Course` and `Semester`.
*   **Relationships**:
    *   `faculty`: Many-to-One. A subject belongs to *one* primary faculty (though the system logic might allow overrides in Timetable, this is the default owner).

## Class: `Attendance`
*   **Purpose**: A single attendance record.
*   **Grain**: One row per Student per Subject per Date.
*   **Foreign Keys**:
    *   `student_id`: Links to `StudentProfile`.
    *   `subject_id`: Links to `Subject`.
    *   `faculty_id`: Captures *who* marked the attendance.

## Class: `Timetable` & `ScheduleSettings`
*   **Timetable**: Represents a single "Cell" in the weekly grid.
    *   `day_of_week`, `period_number`.
    *   `room_number`: Default 'Room 101'.
*   **ScheduleSettings**: Configuration for the Timetable Generator.
    *   **Method**: `get_period_times(period_number)`:
        *   **Algorithm**:
            1.  Calculates `Total Minutes = (End - Start) - Recess`.
            2.  `Slot Duration = Total / Slots Per Day`.
            3.  Calculates exact start time: `Start + (i * duration)`.
            4.  Adds Recess offset calculation if the slot is after the break.

## Class: `ExamEvent` & `ExamPaper`
*   **Hierarchy**:
    *   `ExamEvent`: The umbrella (e.g., "Winter 2024").
    *   `ExamPaper`: The specific scheduled test (e.g., "Maths on Dec 12").
*   **Cascade**: `cascade="all, delete-orphan"`.
    *   *Effect*: If an Exam Event is deleted, all its defined Papers are automatically deleted by the database to prevent orphaned records.

## Class: `StudentResult`
*   **Purpose**: Link Table between `Student` and `ExamPaper`.
*   **Fields**:
    *   `marks_obtained`: Float.
    *   `is_fail`: Boolean flag derived from business logic (Marks < 33%).
