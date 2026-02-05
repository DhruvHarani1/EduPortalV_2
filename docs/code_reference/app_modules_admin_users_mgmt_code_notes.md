# detailed_technical_reference: app/modules/admin/users_mgmt.py

## File Overview
This module handles the lifecycle of Users (Students and Faculty). It includes complex logic for **Bulk CSV Import**, **Profile Image Management**, and **Many-to-Many Relationship Management** (Faculty <-> Subjects).

---

## Route: `/students/import` (POST)

### Purpose
Bulk onboarding of students via CSV upload.

### Logic Breakdown

#### 1. File Parsing
*   **Stream Handling**: Reads the uploaded binary file into an in-memory `io.StringIO` buffer to process it without saving to disk.
*   **Format**: Expects standard CSV headers: `name`, `email`, `password`, `enrollment_number`, `course_name`, `semester`.

#### 2. Row Processing Loop
*   Iterates through each row in the CSV.
*   **Validation Rule 1 (Completeness)**: Checks if `email`, `password`, and `enrollment` are present. Skips row if missing.
*   **Validation Rule 2 (Uniqueness)**: Checks `User.query.filter_by(email)`. Returns error if duplicate.

#### 3. Transactional Creation
For each valid row:
1.  **User Creation**:
    *   Creates `User(role='student')`.
    *   Generates Hash: `user.set_password(row['password'])`.
    *   `db.session.add(user)` -> `flush()` (To generate `user.id`).
2.  **Profile Creation**:
    *   Creates `StudentProfile` linked to the new `user.id`.
    *   Maps CSV fields to Profile fields.

#### 4. Error Handling
*   Maintains a list of `errors` (e.g., "Skipped row 5: Duplicate Email").
*   **Flash**: Displays the first 5 errors to the Admin after processing to avoid UI flooding.

---

## Route: `/faculty/add` & `/faculty/edit` (POST)

### Purpose
Managing Faculty profiles and their teaching assignments.

### Logic Breakdown

#### 1. Subject Linking (The "Assigned Subjects" logic)
*   **Input**: `request.form.getlist('assigned_subjects')` returns a list of Subject Names (e.g., `['Maths', 'Physics']`).
*   **Profile Update**: Stores a comma-separated string `Maths, Physics` in `faculty.assigned_subject` for quick display.

#### 2. Relationship Management (Logic in `edit_faculty`)
When a Faculty's subjects are changed, the system must update the `Subject` table's foreign keys.
*   **Step A: Unlinking (Orphan Removal)**
    *   Fetches all subjects currently owned by this faculty (`faculty_id == self.id`).
    *   Checks if `subject.name` is **NOT** in the new `selected_subject_names`.
    *   Action: Sets `subject.faculty_id = None`.
*   **Step B: Linking (Adoption)**
    *   Fetches subjects matching the new list.
    *   Action: Sets `subject.faculty_id = self.id`.

#### 3. Photo Handling
*   **Storage**: Binary data (`BLOB`) stored directly in SQL (`faculty.photo_data`).
*   **Serving**: The route `/faculty/photo/<id>` acts as a dedicated image server, setting the correct `Content-Type` header (e.g., `image/jpeg`).

---

## Route: `/students/add` (POST)

### Purpose
Single Student creation.

### Logic Breakdown
*   **Date Parsing**: Manually parses `request.form.get('date_of_birth')` from `YYYY-MM-DD` string to Python `date` object. Handles empty strings gracefully.
*   **Defaulting**: Sets `id_card_status` to `'Active'` by default if not specified.
