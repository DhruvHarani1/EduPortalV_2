# detailed_technical_reference: app/models/finance.py

## File Overview
This module defines the **financial ledger** for the student body. It tracks fee obligations, payments, and statuses.

---

## Class: `FeeRecord` (db.Model)

### Purpose
Represents a single financial obligation (e.g., "Semester 3 Fee").

### Core Schema
*   **Composite Business Key**: The combination of `student_id` + `semester` + `academic_year` defines a unique obligation context (though not enforced by SQL constraint, it is the logical grouping).
*   **Money Fields**:
    *   `amount_due`: The expected total.
    *   `amount_paid`: The running total of payments received.
    *   *Derived Logic*: A record is fully paid when `amount_paid >= amount_due`.
*   **Status Workflow**:
    *   `Pending`: Default state.
    *   `Paid`: `amount_paid >= amount_due`.
    *   `Partial`: `0 < amount_paid < amount_due`.
    *   `Overdue`: `date.today() > due_date` AND `status != Paid`.

### Relationships
*   **Student Link**:
    *   `student = db.relationship('StudentProfile')`.
    *   **Cascade**: `backref=..., cascade="all, delete-orphan"`.
    *   *Implication*: If a student profile is deleted, all their financial history (Fee Records) is automatically wiped. This ensures no "ghost debt" remains in the system without an owner.

### Payment Metadata
*   `payment_mode`: Stores the method ('Online', 'Cash').
*   `transaction_reference`: Stores the Gateway ID or Receipt Number.
