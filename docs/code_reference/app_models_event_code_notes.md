# detailed_technical_reference: app/models/event.py

## File Overview
This module manages the **University Events System**, covering the event definition and the student registration/participation tracking.

---

## Class: `UniversityEvent` (db.Model)

### Purpose
Represents a public or private gathering (Hackathon, Cultural Fest, Seminar).

### Key Features
*   **Categorization**:
    *   Field: `category`.
    *   Values: 'Academic', 'Cultural', 'Sports', 'Tech'.
    *   *Usage*: Used in the Student Dashboard to filter cards.
*   **Media Storage**:
    *   `image_data` (LargeBinary): Stores the poster/banner directly in the DB as BLOB.
    *   `image_mimetype` (String): e.g., 'image/png'.
    *   *Rationale*: Simpler distribution than S3 for this scale.

### Relationships
*   `registrations`: One-to-Many link to `EventRegistration`. Allows getting `event.registrations` to count participants.

---

## Class: `EventRegistration` (db.Model)

### Purpose
Join Table representing a **Student's RSVP** or Participation.

### Schema
*   `event_id`: FK to `UniversityEvent`.
*   `student_id`: FK to `StudentProfile`.
*   `registered_at`: Timestamp of signup.

### Constrains & Logic
*   **Constraint Logic (Implicit)**: Application logic prevents duplicate registrations (One student cannot register twice for the same event IDs).
*   **Cascade**:
    *   Link is owned by `StudentProfile`.
    *   `cascade="all, delete-orphan"`.
    *   *Effect*: If the Student leaves (deleted), their registrations are removed. If the Event is cancelled (deleted), the backend logic usually handles cleaning up registrations (though SQL cascade might be set on the other side too).
