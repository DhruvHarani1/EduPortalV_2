# detailed_technical_reference: app/modules/admin/reports_mgmt.py

## File Overview
This module acts as the **Analytics Engine** of the application. It processes raw data (Marks, Attendance, Faculty Reviews) into actionable insights using statistical methods and rule-based AI heuristics.

---

## Route: `/api/reports/student-performance` (GET)

### Purpose
Generates data for the Student Performance Analytics Dashboard (Radar Chart, Scatter Plot, Velocity).

### Logic Breakdown

#### 1. Consistency & Growth Analysis (Scatter Plot)
*   **Method**: `consistency` list generation.
*   **Input**: All `StudentResult` records.
*   **Algorithm**:
    *   **Average (X-Axis)**: `statistics.mean(all_marks)` for a student.
    *   **Consistency (Y-Axis)**: `statistics.stdev(all_marks)`.
        *   *Interpretation*: Lower Standard Deviation = More Consistent performance.
    *   **Growth Velocity**:
        *   Compares `Sem 3 Average` vs `Sem 1 Average`.
        *   Formula: `((Sem3 - Sem1) / Sem1) * 100`.
        *   *Result*: Percentage growth (positive) or decline (negative).

#### 2. Risk Detection ("Danger Zone")
*   **Threshold**: Any student with an overall `Average < 40%`.
*   **Action**: Added to `danger_zone` list with status "Critical".

#### 3. Radar Chart Data (Academic DNA)
*   **Purpose**: Shows aggregate batch performance per subject.
*   **Algorithm**:
    *   Iterates through all `Active Subjects`.
    *   Calculates the `Global Average` of marks for each subject.
    *   *SQL*: `SELECT AVG(marks_obtained) FROM results JOIN papers ... WHERE subject_id = X`.

#### 4. AI Executive Summary
*   **Heuristic**:
    *   Counts `Improving Students` (Growth > 3%).
    *   Counts `Declining Students` (Growth < -3%).
*   **Review Text Generation**:
    *   If `Improving > Declining`: Status = **"Improving"**.
    *   If `Declining > Improving`: Status = **"Declining"**. Suggests "Review teaching pace".
    *   If `Danger Zone > 10% of Batch`: Status = **"Critical Warning"**. Suggests "Parent-Teacher Meeting".

---

## Route: `/api/reports/attendance` (GET)

### Purpose
Analyzes attendance patterns to predict truancy and identify schedule fatigue.

### Logic Breakdown

#### 1. Fatigue Index (Day-wise Analysis)
*   **Goal**: Identify which day of the week has the lowest attendance.
*   **Algorithm**:
    *   Iterates all `Attendance` records.
    *   Buckets them by `Weekday` (0=Mon, 4=Fri).
    *   Calculates `Presence Rate = (Present / Total) * 100` for each day.
*   **Insight**: If `Lowest Day Rate < 70%`, flags "Fatigue Detected" and suggests gamified sessions for that day.

#### 2. Truancy Prediction
*   **Goal**: Predict likelihood of a student dropping out.
*   **Algorithm**:
    *   Calculates `Overall Attendance %` for each student.
    *   **Drop-off Threshold**: 75%.
    *   **Probability Formula**:
        *   If `Attendance < 75%`: `Dropout Probability = 100 - Attendance %`.
            *   *Example*: 60% attendance = 40% chance of dropout.
        *   Else: 0% risk.
    *   Sorts list by Risk (Highest first).

---

## Route: `/api/reports/faculty` (GET)

### Purpose
Evaluates Faculty performance based on the grades of their students (Outcome-based Assessment).

### Logic Breakdown (The "Archetype" Engine)
Classifies teachers into 4 distinct personas based on two metrics: **Performance (Avg Grades)** and **Equity (Standard Deviation)**.

1.  **Metric 1: Performance Index**: `Average Marks` of their class.
2.  **Metric 2: Equity Index**:
    *   Measures how "fair" the learning distribution is.
    *   Formula: `100 - (Standard Deviation * 2.0)`.
    *   *Logic*: High variance (StdDev) means some students ace while others fail (Low Equity). Low variance means everyone is at a similar level (High Equity).

3.  **Classification Rules**:
    *   **The Master Teacher** (Green): `Perf >= 60` AND `Equity >= 60`. (High Grades, Everyone learns).
    *   **The Elite Coach** (Indigo): `Perf >= 65` AND `Equity < 60`. (Top students do well, weak ones fail).
    *   **The Empathetic Guide** (Blue): `Perf < 55` AND `Equity >= 65`. (Low grades, but everyone passes/fails together).
    *   **The Strict Evaluator** (Red): `Equity < 45`. (Chaotic distribution, high failure).

---

## Route: `/api/reports/future` (GET)

### Purpose
Predicts career outcomes and salary packages (The "Sorting Hat").

### Logic Breakdown

#### 1. Career Clustering
*   **Basis**: Combination of `Average Score` and `Variance (Consistency)`.
*   **Rules**:
    *   **Avg > 85, Low Variance**: "Research / PhD" (Consistent Genius).
    *   **Avg > 85, High Variance**: "Data Scientist" (Spiky Genius).
    *   **Avg > 70**: "Full Stack Developer".
    *   **Avg > 60**: "Product Manager".
    *   **Avg < 60**: "Analyst".

#### 2. Monte Carlo Salary Simulation
*   **Base Packages**: Assigned by Role (e.g., Scientist = 18 LPA, Analyst = 4.5 LPA).
*   **Simulation**:
    *   Adds `random.uniform(-1.0, 3.0)` noise to the base package for every student to create realistic distribution curves.
*   **Probability Tiers**:
    *   Tier 1 (> 12 LPA): calculated % chance.
    *   Tier 2 (8-12 LPA): calculated % chance.
    *   Tier 3 (< 8 LPA): calculated % chance.
