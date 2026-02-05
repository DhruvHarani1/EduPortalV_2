# Features & Data Flow Deep Dive

This document provides a microscopic view of how data moves through the EduPortal system for each major feature. It explains the "Black Box" between a user clicking a button and the database updating.

---

## 🏗️ Feature 1: Student Enrollment & Profiling

### 1. Functional Goal
To create a digital identity for a student that links their **Login Credentials** (Auth) with their **Academic Data** (Profile).

### 2. Data Flow Diagram
`User Form` -> `Routes.py` -> `User Table` -> `Profile Table` -> `Dashboard`

### 3. Step-by-Step Logic
1.  **Input**: Admin fills "Add Student" form (Name, Email, Course, Semester).
2.  **Controller Logic** (`admin/routes.py` -> `add_student`):
    *   **Step A (Auth)**:
        ```python
        user = User(email=form.email, role='student')
        user.set_password('default123') # Code handles hashing via werkzeug
        db.session.add(user)
        db.session.flush() # CRITICAL: We need user.id before commit!
        ```
    *   *Why Flush?*: We need the auto-generated `user.id` to link the profile immediately.
    *   **Step B (Profile)**:
        ```python
        profile = StudentProfile(
            user_id=user.id, # The link
            enrollment=generate_enrollment_id(), # Custom logic e.g. STU2024...
            ...
        )
        ```
3.  **Database Commit**: a transactional commit ensures either *both* records exist or *neither* does (Atomicity).

---

## 📊 Feature 2: The Attendance Aggregator

### 1. Functional Goal
To convert thousands of daily attendance rows into a single "Percentage" for the registry view, **without** storing the percentage in the database (which would get out of sync).

### 2. The Logic (On-the-Fly Calculation)
We do not store "85%" in the user table. We calculate it every time the Admin opens the page.

**The SQL Alchemy Magic**:
```python
# app/admin/academics_mgmt.py

stats = db.session.query(
    Attendance.student_id,
    func.count(Attendance.id).label('total'), # Count ALL rows for student
    func.sum(case((Attendance.status == 'Present', 1), else_=0)) # Sum only PRESENTS
).group_by(Attendance.student_id).all()
```

### 3. Data Transformation
*   **Raw DB Data**:
    *   Row 1: John, Mon, Present
    *   Row 2: John, Tue, Absent
    *   Row 3: John, Wed, Present
*   **After Query**: `(John_ID, Total=3, Present=2)`
*   **Python Logic**: `percent = (2 / 3) * 100 = 66.6%`
*   **View Layer**: `attendance_list.html` receives `66.6` and renders a **Yellow Warning Bar**.

---

## 🔮 Feature 3: The AI Prediction Engine (Future Sight)

### 1. Functional Goal
To simulate future career outcomes based on current academic trajectory using Monte Carlo simulations.

### 2. Input Data Sources
*   **Grades**: Fetched from `StudentResult` table.
*   **Consistency**: Calculated via Standard Deviation of grades (Is the student erratic or stable?).
*   **Attendance**: Fetched from `Attendance` table.

### 3. The "Black Box" Algorithm (`reports_mgmt.py`)

#### Phase A: The "Stability Score"
We check if a student's performance is reliable.
```python
# If variance is low (<5), they are "Consistent"
# If variance is high (>15), they are "Volatile"
stability_score = 100 - (statistics.stdev(marks) * 2)
```

#### Phase B: The Salary Simulation (Monte Carlo)
We don't just pick a number. We define a probability curve.
1.  **Base Tier**: If Avg > 80, Base = 12 LPA. If Avg > 60, Base = 6 LPA.
2.  **Market Variance**: We add a randomness factor (`random.uniform(-2, +3)`) to simulate luck/interview skills.
3.  **Result**: Every time you run the report, the numbers shift strictly, simulating real-world uncertainty, but they stay within the student's "Talent Bracket".

---

## 📝 Feature 4: Exam Management Hierarchy

### 1. Functional Goal
To act as a flexible "Container System" for tests.

### 2. The Data Structure
It is not flat. It is a tree.
*   **Root**: `ExamEvent` ("Finals 2025")
    *   **Branch**: `ExamPaper` ("Math I", "Physics II")
        *   **Leaf**: `StudentResult` ("John scored 90")

### 3. Why this way?
This allows the Admin to:
1.  **Publish** an entire Event at once (`is_published=True` on Root).
2.  **Delay** results for a specific Paper.
3.  **Query** performance across all "Finals" across years easily.

---

## 🕵️ Feature 5: The "Radar" (Spider Chart)

### 1. Functional Goal
To visualize a student's strengths across 5 dimensions: **Coding, Theory, Attendance, Consistency, Project**.

### 2. Data Normalization
The chart needs values from 0-100. But different metrics measure differently.
*   **Attendance**: Already 0-100.
*   **GPA**: 0-10 scale. -> We multiply by 10.
*   **Backlogs**: 0 is Good, 5 is Bad. -> We invert it: `Score = 100 - (Backlogs * 20)`.

This "Normalization Layer" in `admin/routes.py` ensures the Radar Chart is always perfectly balanced relative to the visual center.
