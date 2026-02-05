# detailed_technical_reference: app/modules/admin/timetable_mgmt.py

## File Overview
This module handles the **Automated Timetable Generation**. It solves a Constraint Satisfaction Problem (CSP) to assign Subjects to Time Slots while respecting constraints like "Weekly Lecture Counts" and "Daily Limits".

---

## Route: `/timetable/generate` (POST)

### Purpose
The core algorithm that clears existing schedules and rebuilds them from scratch based on configuration.

### Algorithm Breakdown

#### Phase 1: Configuration & Prep
1.  **Inputs**:
    *   `Course` / `Semester`.
    *   `Days Per Week` (e.g., 5).
    *   `Slots Per Day` (e.g., 8).
    *   `Start Time` / `End Time`.
2.  **State Clearing**:
    *   `DELETE FROM timetable WHERE course=X AND semester=Y` to prevent overlaps.

#### Phase 2: Building the "Lecture Pool"
Creates a flat list of all lecture blocks that *must* be scheduled.
*   **Source**: `Subject` table.
*   **Logic**:
    *   For each subject `S`:
    *   Add `S` to `Pool` list **N** times, where N = `S.weekly_lectures`.
    *   *Example*: Java (3), Maths (4) -> `[Java, Java, Java, Maths, Maths, Maths, Maths]`.
*   **Shuffling**: `random.shuffle(pool)` is called to prevent deterministic clustering (e.g., all Math classes on Monday).

#### Phase 3: The Greedy Fill Strategy
Iterates through the grid (Day -> Period) and attempts to place a subject from the pool.

*   **Constraint 1: Daily Capacity**
    *   Logic: A single subject cannot appear too many times in one day.
    *   `Daily Limit` = `ceil(Total Lectures for Subject / Days in Week)`.
    *   *Check*: If `Math` is already scheduled `Limit` times on `Monday`, skip it.

*   **Constraint 2: Slot Availability**
    *   Iterates `Days` -> `Periods`.
    *   If `Grid[Day][Period]` is Empty:
        *   Try to pop a subject from `Pool`.
        *   If Subject passes **Daily Capacity** check:
            *   **Place It**: Assign to Grid.
            *   Break inner loop (move to next item in pool).
        *   Else: Put back in pool / Try next.

#### Phase 4: Persistence
*   Iterates the filled `Grid`.
*   Creates `Timetable` database objects:
    *   `day_of_week` (e.g., "Monday").
    *   `period_number` (1-8).
    *   `subject_id` (Mapped from grid).
    *   `faculty_id` (Inherited from Subject).

---

## Route: `/timetable/view` (GET)

### Purpose
Renders the grid view of the generated schedule.

### Logic Breakdown
1.  **Dynamic Headers**:
    *   Calls `settings.get_period_times(p)` to convert abstract Period Numbers (1, 2, 3) into concrete times (09:00, 10:00, 11:00) based on the configured *Start Time* and *Slot Duration*.
2.  **Grid Reconstruction**:
    *   DB returns a flat list of slots.
    *   Python converts this to a nested dictionary for HTML table iteration: `grid[Day][Period] = Slot`.

---

## Route: `/timetable/update_slot` (POST)

### Purpose
AJAX endpoint for **Drag-and-Drop** or manual overrides.

### Logic Breakdown
1.  **Input**: `slot_id` (optional), `day`, `period`, `subject_id` (if new).
2.  **Delete Operation**:
    *   If `subject_id` is empty/null, the slot is treated as "Free/Recess".
    *   The existing `Timetable` row is Deleted.
3.  **Update/Create Operation**:
    *   If slot exists: Update `subject_id`.
    *   If slot is empty: Create new `Timetable` row.
    *   **Auto-Link Faculty**: When a subject is assigned, the system automatically fetches and assigns the corresponding `faculty_id` from the `Subject` table.
