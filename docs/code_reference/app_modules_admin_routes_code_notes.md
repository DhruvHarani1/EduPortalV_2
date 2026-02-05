# detailed_technical_reference: app/modules/admin/routes.py

## File Overview
This module handles the **Admin Dashboard** and **System-Wide Reports**. It focuses on aggregating high-level metrics for the visualization layer (Chart.js) and generating printable summaries.

---

## Route: `/dashboard` (GET)

### Purpose
The landing page for the Admin, serving as a real-time health monitor of the institution.

### Logic Breakdown (Metric Aggregation)

#### 1. Population Counts
*   **Method**: `Query.count()` (Efficient `SELECT COUNT(*)`).
*   **Metrics**: `Total Students`, `Total Faculty`.

#### 2. Course Distribution (Pie Chart Data)
*   **Goal**: Visualize student distribution across courses (e.g., "How many in B.Tech vs MBA?").
*   **SQL Query**:
    ```sql
    SELECT course_name, COUNT(id) 
    FROM student_profile 
    GROUP BY course_name
    ```
*   **Python Implementation**:
    *   Uses `func.count(StudentProfile.id)` and `group_by(StudentProfile.course_name)`.
    *   **Transformation**: Splits the result tuples `[(B.Tech, 50), (MBA, 20)]` into two parallel lists:
        *   `course_labels = ['B.Tech', 'MBA']`
        *   `course_counts = [50, 20]`
    *   *Usage*: These lists represent the `labels` and `data` arrays passed to the Chart.js configuration in the template.

#### 3. Stream Filtering
*   **Recent Notices**: Fetches the top 5 most recent notices using `order_by(desc).limit(5)` to populate the "Activity Feed" widget.

---

## Route: `/dashboard/system_report_print` (GET)

### Purpose
Generates a "Print-Friendly" (Ctrl+P optimized) snapshot of the system state.

### Logic Breakdown
*   **Data Gathering**: Re-runs the aggregation logic from the dashboard but includes slightly more detail (Limit 10 notices instead of 5).
*   **Timestamping**: Captures `datetime.now()` as `generated_at` so the printed report serves as a valid audit document.
