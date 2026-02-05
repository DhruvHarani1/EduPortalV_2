<div align="center">

# 🎓 EDU-PORTAL
### The Future of University Management

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<p align="center">
  <img src="https://images.unsplash.com/photo-1541339907198-e08756dedf3f?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80" alt="University Banner" width="100%" style="border-radius: 10px;" />
</p>

[**🚀 Getting Started**](#-getting-started) •
[**✨ Key Features**](#-key-features) •
[**📚 Documentation**](#-documentation-hub) •
[**🏗️ Tech Stack**](#-tech-stack) •
[**🤝 Contributing**](#-contributing)

</div>

---

## 🌟 Overview

**EduPortal** is not just another management system; it is an **Intelligent Academic Operating System**. Built with a modern, high-performance stack (Flask + TailwindCSS), it bridges the gap between Administration, Faculty, and Students through a seamless, responsive, and data-driven interface.

It features **AI-powered analytics**, automated scheduling algorithms, and a robust permission system, all wrapped in a premium, glassmorphism-inspired UI.

---

## ✨ Key Features

### 🏛️ For Administrators
*   **AI-Driven Insights**: Dashboard with predictive analytics for Student Retention (Truancy Risk) and Faculty Performance archetypes.
*   **Automated Scheduling**: One-click **Timetable Generation** using a greedy constraint-satisfaction algorithm. Avoids conflicts automatically.
*   **Examination Lifecycle**: Manage Exam Events, Schedule Papers, and auto-generate **Result Matrices (CSV)** for thousands of students.
*   **Targeted Announcements**: Send notices to the entire university, specific courses, or individual faculty members.

### 👨‍🏫 For Faculty
*   **Batch Operations**: Mark attendance for 60+ students in seconds using our "Sticky Form" batch interface.
*   **Result Entry**: Rapid-fire marks entry system with auto-validation and "Fail" flagging (Marks < 33%).
*   **Mentorship Hub**: Dedicated dashboard to track and edit profiles for assigned mentees.
*   **Smart Attendance**: Visual indicators for low-attendance students directly in the marking view.

### 🎓 For Students
*   **Live Dashboard**: Real-time **SPI (Semester Performance Index)** calculation and Attendance percentages.
*   **Bunk Recovery Calculator**: "You need to attend next **5** classes to reach 75%."
*   **Digital Services**: Apply for Scholarships, Register for Events, and Pay Fees online (simulated gateway).
*   **Ticket System**: Direct query channel to faculty for academic doubts.

---

## 📚 Documentation Hub

We believe code should be self-documenting, but we documented it anyway— **in extreme detail**.

### 🛠️ Technical Deep Dives
*   [**Architecture & Design**](docs/PROJECT_FUNCTIONAL_SPEC.md): The masterplan, user personas, and system vision.
*   [**Database Schema**](docs/DATABASE_SCHEMA.md): Full ER Diagram and relationship details.
*   [**Deployment Guide**](docs/DEPLOYMENT.md): Production setup updates.

### 📝 Code Reference (The "Engine Room")
*   [**AI & Analytics Engine**](docs/code_reference/app_modules_admin_reports_mgmt_code_notes.md): How we predict careers and classify faculty.
*   [**Scheduler Algorithm**](docs/code_reference/app_modules_admin_timetable_mgmt_code_notes.md): The logic behind the timetable generator.
*   [**Grading Logic**](docs/code_reference/app_modules_student_code_notes.md): Breakdowns of SPI, CGPA, and Attendance Recovery formulas.
*   [**Exam System**](docs/code_reference/app_modules_admin_exams_mgmt_code_notes.md): How dynamic result CSVs are built.
*   [**Core Models**](docs/code_reference/app_models_academics_code_notes.md): Deep dive into the `Course`, `Subject`, and `Attendance` tables.

---

## 🚀 Getting Started

### 1. Prerequisites
*   **Python 3.8+**
*   **Node.js** (for TailwindCSS compilation)
*   **PostgreSQL**

### 2. Installation

**Backend Setup**
```bash
# Clone the repo
git clone https://github.com/your-org/edu-portal.git
cd EDU-PORTAL

# Create Virtual Env
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# Install Deps
pip install -r requirements.txt
```

**Frontend Setup**
```bash
npm install
```

### 3. Configuration
1.  Copy `.env.example` to `.env`.
2.  Update your Database credentials.
3.  Run the **Seeder** to populate the DB with realistic test data:
    ```bash
    python manage.py seed
    ```

### 4. Running the App
You need **two** terminals:

**Terminal 1 (CSS Compiler)**
```bash
npm run dev
```

**Terminal 2 (Flask Server)**
```bash
flask run
```

Visit: `http://127.0.0.1:5000`

---

## 🏗️ Tech Stack

### Backend
*   **Framework**: Flask (Blueprints architecture)
*   **ORM**: SQLAlchemy (Relational mapping)
*   **Auth**: Flask-Login (RBAC: Admin, Faculty, Student)
*   **Exports**: Python CSV, ReportLab (PDFs)

### Frontend
*   **Styling**: **TailwindCSS v3** (Utility-first)
*   **Components**: Jinja2 Templates (Server-Side Rendering)
*   **Charts**: Chart.js (Data Visualization)
*   **Icons**: FontAwesome & HeroIcons

---

## 🔑 Login Credentials (Seed Data)

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@edu.com` | `123` |
| **Faculty** | `faculty1@edu.com` | `123` |
| **Student** | `student1@edu.com` | `123` |

---

<div align="center">

Made with ❤️ by the EduPortal Team.

</div>