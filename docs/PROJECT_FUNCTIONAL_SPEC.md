# EduPortal - Functional Specification & User Guide

## 1. Project Vision
**EduPortal** is a Next-Generation University Management System (UMS) designed to bridge the gap between simple record-keeping and intelligent decision-making. Unlike legacy ERPs, EduPortal leverages **AI-driven Analytics** to provide actionable insights into student performance and faculty effectiveness.

---

## 2. User Personas & Capabilities

### 👑 The Administrator (Superuser)
*   **Role**: Total System Control.
*   **Key Capabilities**:
    *   **User Management**: Onboard students and hire faculty.
    *   **Academic Configuration**: Create Courses (B.Tech, MBA), Subjects, and Semesters.
    *   **Exam Controller**: Schedule "Exam Events", publish results, and declare holidays.
    *   **Intelligence Viewer**: Access the "Future Sight" prediction engine.
    *   **Financial Overseer**: Track student fee payments and dues.

### 🎓 The Faculty (Teacher)
*   **Role**: Academic Delivery & Assessment.
*   **Key Capabilities**:
    *   **Attendance Marking**: Log daily class attendance.
    *   **Result Entry**: Input marks for their specific subjects.
    *   **Support & Mentorship**: Reply to breakdown queries from their mentees.
    *   **Timetable**: View generated weekly schedules.

### 🎒 The Student (End User)
*   **Role**: Consumer of information.
*   **Key Capabilities**:
    *   **Performance View**: See their own grades and GPA trends.
    *   **Event Hub**: Register for Cultural, Tech, or Sports events.
    *   **Financials**: Check fee status and history.
    *   **Helpdesk**: Raise queries directly to faculty or admin.

---

## 3. Module Breakdown (In-Depth)

### A. The Academic Engine
This module manages the core university structure.
*   **Dynamic Timetable**: Automatically detects conflicts.
*   **Attendance Registry**: Real-time aggregation. It calculates percentages instantly, coloring students as **Green (Safe)**, **Yellow (Warning)**, or **Red (Critical)**.

### B. The Examination System
A hierarchical system designed for flexibility.
1.  **Event Creation**: Admin creates "Winter Semester Finals 2025".
2.  **Paper Scheduling**: Admin schedules "Maths I" on Dec 10th.
3.  **Result Entry**: Faculty enters marks; Admin publishes results.

### C. Student Support & Helpdesk
A dedicated ticketing system for students.
*   **Workflow**: Student raises query -> Linked Faculty receives notification -> Chat-style thread for resolution.
*   **Categories**: Academic doubts, Leave requests, Administration issues.

### D. University Life (Events)
Beyond academics, managing campus culture.
*   **Event Types**: Technical Symposiums, Cultural Nights, Sports Meets.
*   **Registration**: Students can "One-Click Register" for events.
*   **Multimedia**: Events support rich image banners.

### E. Finance Module
*   **Fee Tracking**: Semester-wise fee records (Paid/Pending/Partial).
*   **History**: Students can view their entire payment ledger.

### F. The Intelligence Suite (USP)
1.  **Career Prediction**: Monte Carlo simulations predict "Future Salary".
2.  **Radar Analysis**: A 5-point spider chart evaluating "Consistency" and "Attendance".
3.  **Faculty Equity**: Measures how "Inclusive" a teacher is based on mark distribution standard deviation.

---

## 4. End-to-End User Journeys

### Journey 1: The "Exam Season" Flow
1.  **Admin** creates `ExamEvent`: "Mid-Terms".
2.  **Admin** adds `ExamPaper`s for all subjects.
3.  **Students** view the Date Sheet on their dashboard.
4.  **Faculty** inputs scores once exams are done.
5.  **Admin** publishes results, triggering AI prediction updates.

### Journey 2: The "Event Registration" Flow
1.  **Admin** posts "Hackathon 2026" under University Events.
2.  **Student** sees the banner on their dashboard.
3.  **Student** clicks "Register".
4.  **System** adds them to the participant list and updates the database.
