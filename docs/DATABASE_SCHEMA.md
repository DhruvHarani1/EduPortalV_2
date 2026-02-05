# Database Schema Documentation

## Overview
The EduPortal database is built on **PostgreSQL** and uses **SQLAlchemy** as the ORM. The schema is normalized to **3NF** standards to ensure data integrity, with strict Foreign Key constraints and `ON DELETE CASCADE` rules to prevent orphaned records.

## 1. Authentication & Profiles (Core)

### `users`
*   **Purpose**: Central authentication table. Stores login credentials for all roles.
*   **Fields**:
    *   `id` (PK): Serial.
    *   `email`: Unique String (Indexed).
    *   `password_hash`: Scrypt hashed string.
    *   `role`: Enum ('admin', 'student', 'faculty').

### `faculty_profile`
*   **Purpose**: Extended profile for faculty members.
*   **Relationships**:
    *   `user_id` (FK): Links to `users.id` (**Cascade Delete**).
*   **Fields**: `designation`, `department`, `specialization`, `experience`, `photo_data`.

### `student_profile`
*   **Purpose**: extended profile for students. Includes academic linkage.
*   **Relationships**:
    *   `user_id` (FK): Links to `users.id` (**Cascade Delete**).
    *   `mentor_id` (FK): Links to `faculty_profile.id` (Set Null).
*   **Fields**: `enrollment_number` (Unique), `course_name`, `semester` (Int), `batch_year`, `guardian_name`.

---

## 2. Academic Management

### `course`
*   **Purpose**: Defines degrees/programs (e.g., "B.Tech", "MBA").
*   **Fields**: `name`, `code`, `department`, `total_semesters`.

### `subject`
*   **Purpose**: Individual subjects being taught. Linked to Faculty.
*   **Fields**: `name`, `semester`, `credits`, `weekly_lectures`.
*   **FKs**: `faculty_id` (Set Null).

### `syllabus`
*   **Purpose**: PDF files for subject syllabus.
*   **FKs**: `subject_id` (**Cascade Delete**).
*   **Fields**: `file_data` (Binary), `filename`.

### `timetable`
*   **Purpose**: Weekly schedule slots.
*   **Fields**: `day_of_week` (Mon-Fri), `period_number` (1-8), `room_number`.
*   **FKs**: 
    *   `subject_id` (**Cascade Delete**).
    *   `faculty_id` (**Cascade Delete**).

### `schedule_settings`
*   **Purpose**: Configuration for the timetable generator (start time, recess duration).
*   **Fields**: `slots_per_day`, `recess_after_slot`.

### `attendance`
*   **Purpose**: Daily attendance logs.
*   **Fields**: `date`, `status` (Present/Absent).
*   **FKs**: `student_id` (**Cascade Delete**), `subject_id`, `faculty_id`.

---

## 3. Examination System

### `exam_event`
*   **Purpose**: The "Season" or high-level event (e.g., "Winter Semester Finals 2025").
*   **Fields**: `start_date`, `end_date`, `is_published` (Boolean).

### `exam_paper`
*   **Purpose**: Specific paper within an event (e.g., "Maths I").
*   **FKs**: 
    *   `exam_event_id` (**Cascade Delete**).
    *   `subject_id` (**Cascade Delete**).
*   **Fields**: `date`, `start_time`, `end_time`, `total_marks`.

### `student_result`
*   **Purpose**: Stores marks for a specific student in a specific paper.
*   **FKs**:
    *   `exam_paper_id` (**Cascade Delete**).
    *   `student_id` (**Cascade Delete**).
*   **Fields**: `marks_obtained`, `is_fail` (Boolean), `status` (Present/Absent).

---

## 4. University Life & Communication

### `university_event`
*   **Purpose**: Cultural or Tech events (e.g., "Tech Fest", "Sports Meet").
*   **Fields**: `title`, `description`, `date`, `category` (Sports/Tech/Cultural), `image_data`.

### `event_registration`
*   **Purpose**: Tracks which students are attending an event.
*   **FKs**:
    *   `event_id` (**Cascade Delete**).
    *   `student_id` (**Cascade Delete**).
*   **Constraint**: Unique constraint on `(event_id, student_id)` to prevent double registration.

### `notice`
*   **Purpose**: Broadcast messages.
*   **Fields**: `title`, `content`, `category`, `target_course`.
*   **FKs**: `target_student_id` (**Cascade Delete** - for private notices).

---

## 5. Administrative & Support

### `fee_record`
*   **Purpose**: Financial tracking.
*   **FKs**: `student_id` (**Cascade Delete**).
*   **Fields**: `amount_due`, `amount_paid`, `status` (Paid/Pending), `transaction_reference`.

### `student_query`
*   **Purpose**: Helpdesk tickets raised by students.
*   **FKs**: `student_id` (**Cascade Delete**), `faculty_id` (Target).
*   **Fields**: `title`, `status` (Pending/Resolved).

### `query_message`
*   **Purpose**: Chat history/replies within a query.
*   **FKs**: `query_id` (**Cascade Delete**).
*   **Fields**: `sender_type` (Student/Faculty), `content`.
