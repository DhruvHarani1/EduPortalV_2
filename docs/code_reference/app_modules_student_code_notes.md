# detailed_technical_reference: app/modules/student/routes.py

## File Overview
This file contains the route handlers for the Student Portal. It is responsible for:
1.  **Dashboard Aggregation**: calculating live performance metrics (Attendance, SPI).
2.  **Academic History**: processing exam results and generating formatted marksheets.
3.  **Logistics**: displaying timetables, managing fee payments, and event registration.

---

## Route: `/dashboard` (GET)

### Purpose
Acts as the central command center for the student, aggregating critical real-time data from multiple underlying systems (Attendance, Finance, Academics).

### Logic Breakdown

#### 1. Attendance Calculation
*   **Method**: Calls `student.get_overall_attendance()`.
*   **Input**: `StudentProfile` object.
*   **Algorithm**:
    *   Queries `Attendance` table for all records matching `student.id`.
    *   Counts `Total Records` and `Present Records`.
    *   Returns `(Present / Total) * 100`.

#### 2. Latest SPI Calculation (Academic Performance)
The dashboard displays the **SPI (Semester Performance Index)** for the most recent completed exam event.

*   **Step 1: Fetch Results**
    *   Query `StudentResult` filtered by `student_id`.
*   **Step 2: Grouping**
    *   Iterates through all results and groups them by `ExamEvent`.
    *   Sorts events by date (`reverse=True`) to find the latest one.
*   **Step 3: Point Calculation (The "Grading Scale")**
    *   For each subject in the latest exam, converts `marks_obtained` (0-100) to `Grade Points` (0-10):
        *   **90 - 100**: 10 Points (Grade AA)
        *   **80 - 89**: 9 Points (Grade AB)
        *   **70 - 79**: 8 Points (Grade BB)
        *   **60 - 69**: 7 Points (Grade BC)
        *   **50 - 59**: 6 Points (Grade CC)
        *   **40 - 49**: 5 Points (Grade CD)
        *   **< 40**: 0 Points (Grade FF)
*   **Step 4: Credit Weighting**
    *   Retrieves `credits` from `Subject.weekly_lectures`.
    *   *Fallback*: If `weekly_lectures` is NULL, defaults to **3 credits**.
    *   Calculates `Weighted Points = Grade Points * Credits`.
*   **Step 5: Final Formula**
    *   `SPI = (Sum of Weighted Points) / (Sum of Total Credits)`
    *   Result is rounded to 2 decimal places.

---

## Route: `/attendance` (GET)

### Purpose
Provides a granular, subject-wise breakdown of attendance to help students identify which classes they are missing. It includes a "Recovery" calculator.

### Logic Breakdown

#### 1. Data Aggregation
*   **Subject List**: Fetches all subjects for the student's current Course/Semester.
*   **Timetable Integration**: Mapping specific days of the week to subjects to handle legacy attendance records that might only have a date (without a subject ID).

#### 2. Subject-Wise Stats
For each subject, the system calculates:
*   `Total Classes`: Count of attendance records linked to this subject.
*   `Present Count`: Count where `status == 'Present'`.
*   `Percentage`: `(Present / Total) * 100`.

#### 3. Recovery Logic (The "Bunk Recovery" Algorithm)
If a student's attendance in a subject is **below 75%**, the system calculates how many *consecutive* future classes they must attend to reach the safe threshold.

*   **Formula Derivation**:
    *   Let $P$ be current Present classes.
    *   Let $T$ be current Total classes.
    *   Let $X$ be the number of future classes needed.
    *   Target Threshold is 75% ($0.75$).
    *   Equation: $\frac{P + X}{T + X} = 0.75$
    *   $P + X = 0.75T + 0.75X$
    *   $0.25X = 0.75T - P$
    *   $X = \frac{0.75T - P}{0.25}$
*   **Result**: The code implements this formula: `x = (0.75 * total - present) / (1 - 0.75)`.
*   **Output**: Returns `ceil(x)` as the integer number of classes required.

---

## Route: `/academics/marksheet/<exam_id>` (GET)

### Purpose
Generates a printable, official-looking breakdown of results for a specific exam.

### Logic Breakdown
1.  **Validation**: Ensures the requested `exam_id` corresponds to papers taken by the logged-in student.
2.  **Aggregation**:
    *   Iterates through all `StudentResult` objects for this exam.
    *   Accumulates `Total Marks Obtained` vs `Total Max Marks` (e.g., 450/500).
3.  **Grade Assignment**:
    *   Re-applies the **Grading Scale Logic** (AA-FF) described in the Dashboard section to assign specific letter grades to each subject.
4.  **SPI Calculation**:
    *   Re-calculates the SPI for this specific exam event using the weighted credit formula.
5.  **Rendering**:
    *   Passes all calculated data to `marksheet_print.html`, which is likely styled with CSS `@media print` for PDF generation.

---

## Route: `/timetable` (GET)

### Purpose
Visualizes the weekly schedule.

### Logic Breakdown
1.  **Data Fetching**: Retrieves `Timetable` entries for the student's cohort.
2.  **Time Calculation**:
    *   Checks if `ScheduleSettings` exist (Admin-configured Start Time/Duration).
    *   **Dynamic Time Generation**:
        *   If Settings exist: Calls `settings.get_period_times(period_number)`.
        *   If No Settings: Uses a heuristic:
            *   Base Start: **09:00 AM**.
            *   Duration: **60 minutes**.
            *   `Start Time = 9:00 + (Period_Index * 60 min)`.
3.  **Structure**:
    *   Organizes data into a Dictionary: `{ 'Mon': [Slot1, Slot2], 'Tue': [...] }`.
    *   Sorts slots by `period_number` to ensure chronological order.

---

## Route: `/scholarship` (GET, POST)

### Purpose
A search engine for financial aid.

### Logic Breakdown
*   **Database**: Contains a hardcoded list of dictionaries (`SCHOLARSHIP_DB`) representing real-world schemes (NSP, AICTE).
*   **Search Filters**:
    1.  **Income Limit**: Checks if `Student Family Income` <= `Scholarship Max Income`.
    2.  **Category**: Checks if `Student Category` (e.g., OBC, SC) is in `Scholarship.allowed_categories`.
    3.  **Gender**: Checks if `Student Gender` is in `Scholarship.allowed_genders` (e.g., "Pragati Scholarship" is Female only).
*   **Output**: Returns a list of matching dictionaries.

---

## Route: `/fees/pay/<fee_id>` (POST)

### Purpose
Simulates a Payment Gateway transaction.

### Logic Breakdown
1.  **State Check**: Verifies fee is not already 'Paid'.
2.  **Transaction Generation**:
    *   Sets `status = 'Paid'`.
    *   Sets `payment_date = datetime.utcnow()`.
    *   Generates a mock **Transaction ID**: `TXN{timestamp}{fee_id}`.
3.  **Persistence**: Commits changes to `FeeRecord`.
4.  **Response**: Returns JSON `{ 'status': 'success' }` for frontend AJAX handling.
