# Project Setup Guide

## Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd EDU-PORTAL
    ```

2.  **Backend Setup**:
    ```bash
    # Create virtual environment
    python -m venv venv
    
    # Activate virtual environment
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**:
    ```bash
    npm install
    ```

4.  **Database Setup**:
    - Create a PostgreSQL database (e.g., `edu_portal`).
    - Copy `.env.example` to `.env` and update credentials.
    - Initialize database:
      ```bash
      flask db init
      flask db migrate
      flask db upgrade
      ```

5.  **Run Development Server**:
    ```bash
    npm run dev
    ```

## Project Structure
- `app/`: Flask application code.
- `app/blueprints/`: Modular routes (Auth, Admin, Faculty, Student).
- `app/models/`: Database models.
- `database/`: SQL scripts and seeds.
- `docs/`: Developer documentation.
