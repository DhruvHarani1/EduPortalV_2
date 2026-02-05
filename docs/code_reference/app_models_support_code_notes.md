# detailed_technical_reference: app/models/support.py

## File Overview
This module implements the **Helpdesk / Ticketing System**. It mimics a conversation-thread model (like email or chat) between a Student and Faculty.

---

## Class: `StudentQuery` (db.Model)

### Purpose
The **Parent Ticket**. Represents the core issue/question.

### Schema
*   `student_id`: Values the "Requester".
*   `faculty_id`: Values the "Assignee".
*   `subject_id` (Optional): contexts the query to a specific subject (e.g., "Doubt in Chapter 4").
*   `status`: State Machine ('Pending' -> 'Answered' -> 'Resolved').
*   `updated_at`: Critical for sorting the Faculty Inbox (newest activity first).

### Relationships
*   `messages`: One-to-Many. Contains the full chat history.
*   **Cascade**: `cascade="all, delete-orphan"`.
    *   *Effect*: Deleting the Query Ticket deletes all specific messages within it.

---

## Class: `QueryMessage` (db.Model)

### Purpose
A specific **Reply** within a thread.

### Schema
*   `query_id`: Foreign Key to the Parent Ticket.
*   `sender_type`: Discriminator ('student' or 'faculty'). Determines the bubble color in UI.
*   `content`: The text body.
*   `image_data`: Optional screenshot/photo attachment (BLOB).
