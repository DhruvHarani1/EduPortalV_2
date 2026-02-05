# detailed_technical_reference: app/models/profiles.py

## File Overview
This module defines the **User Personas**. It separates the Authentication identity (`User` table) from the Domain identity (`Profile` tables).

---

## Class: `StudentProfile`
*   **Relationship**: One-to-One with `User`.
    *   `user_id`: Unique Foreign Key.
*   **Fields**:
    *   `enrollment_number`: Unique Identifier (Business Key).
    *   `mentor_id`: Self-referential-ish link to `FacultyProfile`.
*   **Method**: `get_overall_attendance()`
    *   **Logic**: Performs a real-time query on the `Attendance` table to calculate the global percentage.
    *   *Note*: Used frequently in dashboards.

## Class: `FacultyProfile`
*   **Relationship**: One-to-One with `User`.
*   **Assets**:
    *   `photo_data`: Stores profile picture as `LargeBinary` (BLOB).
    *   `assigned_subject`: A generic text field (comma-separated) for display purposes, distinct from the actual `Subject` table relational links.
