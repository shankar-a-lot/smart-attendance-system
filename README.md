## 📌 Executive Summary & Problem Understanding

Institutional ERPs operating at scale (5,000+ students, 200+ faculty members across diverse academic departments) face three primary operational challenges in attendance management:
1. **Compliance Risks & Silent Modifications:** Uncontrolled editing of historical attendance creates disputes during end-of-semester examination clearance.
2. **Delayed Intervention:** Shortages below statutory thresholds (e.g., 75%) are often identified too late for students to recover.
3. **Operational Concurrency:** Morning marking rushes create slot collisions, double-booking, and database contention.

This solution provides an **audit-first, role-governed Smart Attendance Management Platform** engineered with a layered 3-tier architecture (FastAPI backend + React frontend + Relational SQLite/PostgreSQL store).

---

## 🖼️ User Interface & Working Prototype

### 1. Student Portal — Subject Performance & Recovery Target
Students track subject-wise eligibility, attendance progress meters, and an exact calculated recovery target showing how many consecutive future classes they must attend to restore examination eligibility.

![Student Portal View](docs/student_portal.png)

### 2. Faculty Dashboard — Marking Matrix & Automated Shortage Alerts
Faculty record attendance via a fast matrix grid. The system automatically scans session totals and triggers real-time shortage alerts to the Class Teacher and Section HOD when a student drops below 75%.

![Faculty Dashboard View](docs/faculty_dashboard.png)

---

## 🎯 Key Architectural & Product Features

### 1. Automated Real-Time Shortage Alerts
- Post-submission evaluation checks all student attendance ratios within the affected course and section.
- If a student falls strictly below **75%**, alerts are automatically dispatched and linked to:
  - The assigned **Course / Class Teacher**
  - The **Head of Department (HOD)**
- Alerts remain active on faculty dashboards until student compliance is re-established.

### 2. Strict Least-Privilege RBAC & Immutable Audit Ledger
- **Course Ownership:** Faculty can only record attendance for courses and sections explicitly assigned to them.
- **Locking Mechanism:** Historical attendance is locked after submission. Faculty cannot silently overwrite past records via HTTP `PUT`/`UPDATE`.
- **Dual-Control Governance:** Any attendance correction must be submitted as a formal request (`attendance_corrections`) containing a mandatory justification reason. Modifications only apply if reviewed and approved by the HOD or Admin.

### 3. Student Subject Analytics & Recovery Math
Unlike naive calculation formulas that underestimate required attendance, the platform calculates the exact **Deficit Recovery Metric**:

$$\text{Required Classes } (k) = \max\left(0, \left\lceil \frac{0.75 \cdot T - P}{0.25} \right\rceil\right)$$

*Where $T = \text{Total Sessions Concluded}$ and $P = \text{Sessions Attended}$.*  
*Proof:* To reach $\ge 75\%$, we solve:
$$\frac{P + k}{T + k} \ge 0.75 \implies P + k \ge 0.75T + 0.75k \implies 0.25k \ge 0.75T - P \implies k \ge \frac{0.75T - P}{0.25}$$

---

## 🏗️ System Architecture & Data Model

```text
┌────────────────────────────────────────────────────────┐
│        Client Tier: React 18 + Vite + Tailwind CSS     │
│  ├─ Student Portal: Subject health & recovery target   │
│  ├─ Faculty Dashboard: Matrix grid & alert feed        │
│  └─ HOD View: Correction audit & authorization inbox   │
└────────────────────────────┬───────────────────────────┘
                             │ HTTPS / JSON REST APIs
                             ▼
┌────────────────────────────────────────────────────────┐
│           Application Tier: FastAPI (Python 3.13)      │
│  ├─ Role-Based Access Control (RBAC) & Session Auth    │
│  ├─ Slot Collision & Idempotency Controller            │
│  ├─ Real-Time Alert Dispatcher Engine                  │
│  └─ Deficit Recovery & Eligibility Calculator          │
└────────────────────────────┬───────────────────────────┘
                             │ SQLAlchemy ORM
                             ▼
┌────────────────────────────────────────────────────────┐
│     Persistence Tier: Relational ACID Store (SQLite)   │
│  ├─ departments, users (ADMIN, HOD, FACULTY, STUDENT)  │
│  ├─ courses, enrollments                               │
│  ├─ attendance_sessions (Slot uniqueness constraint)   │
│  ├─ attendance_records (Individual attendance status)  │
│  ├─ attendance_alerts (Automated trigger notifications)│
│  └─ attendance_corrections (Immutable audit ledger)    │
└────────────────────────────────────────────────────────┘
Markdown
### Relational Schema Design

* **`departments`**: `(id, name, hod_id)`
* **`users`**: `(id, full_name, email, role, department_id, section)`
* **`courses`**: `(id, code, title, department_id, faculty_id)`
* **`enrollments`**: `(id, student_id, course_id, section)` — *Unique on `(student_id, course_id)`*
* **`attendance_sessions`**: `(id, course_id, faculty_id, session_date, slot_number, section, is_locked)` — *Composite Unique on `(course_id, session_date, slot_number, section)`*
* **`attendance_records`**: `(id, session_id, student_id, status)` — *Composite Unique on `(session_id, student_id)`*
* **`attendance_corrections`**: `(id, record_id, previous_status, requested_status, reason, requested_by, reviewed_by, status)`
* **`attendance_alerts`**: `(id, student_id, course_id, current_percentage, notified_to_user_id, role_alerted, is_acknowledged)`

---

## 🛡️ Edge Cases & System Validation

| Scenario / Edge Case | System Behavior & Mitigation |
| :--- | :--- |
| **Concurrent Double Submission** | Prevented via composite database index on `(course_id, session_date, slot_number, section)`. A duplicate save aborts with HTTP 400. |
| **Silent Historical Edits** | Direct record updates are blocked. Faculty must initiate an audit record that requires HOD sign-off. |
| **New Course (Zero Sessions)** | Guard condition catches $T = 0$, defaulting attendance to 100.0% and recovery needed to 0 to avoid division-by-zero errors. |
| **Mid-Semester Enrollments** | Denominator $T$ binds to sessions held post-enrollment date, preventing artificial shortage penalties. |
| **Excused vs. Absent** | Excused absences (medical certificates, institutional deputation) count neutrally or positively, separate from unexcused truancies. |

---

## ⚡ Quickstart & Local Setup

### 1. Prerequisites
* Python 3.10+
* Node.js 18+ and npm

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed sample data (departments, courses, faculty, students, initial sessions)
python seed_data.py

# Launch FastAPI backend
uvicorn app.main:app --reload --port 8000
Interactive Swagger API Documentation: http://localhost:8000/docs

3. Frontend Setup
Bash
# Navigate to frontend directory (in a separate terminal)
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
Web Application: http://localhost:5173

📋 Mandatory AI Usage Report
Plaintext
======================================================================
MANDATORY AI USAGE REPORT
======================================================================
AI TOOL USED: 
ChatGPT / Gemini / Cursor (Claude 3.7 Sonnet)

WHAT I ASKED AI TO DO:
1. Generate an initial normalized relational schema (SQLAlchemy DDL) linking 
   students, courses, timetable slots, and attendance records.
2. Formulate the mathematical recovery metric to compute the exact number of 
   future consecutive classes required for a student with < 75% attendance 
   to achieve compliance.
3. Scaffold a responsive React frontend interface supporting dual-view role 
   toggling (Student Analytics vs. Faculty Marking Matrix).

PROMPT THAT WAS MOST USEFUL:
"Derive an exact inequality formula to calculate how many consecutive classes a 
student must attend to cross 75% when their current attendance is P attended out 
of T total, avoiding zero-division and invalid integer subtraction."

CODE GENERATED BY AI: What part?
- FastAPI endpoint signatures and Pydantic request models.
- Initial Tailwind CSS styling skeleton for the matrix grid and progress bars.
- Foundational inequality formulation for attendance recovery.

CODE I MODIFIED: What part?
- Database Constraints: Added composite unique constraints on (course_id, 
  session_date, slot_number, section) to prevent duplicate sessions during 
  concurrent faculty submissions.
- Governance & RBAC: Re-engineered AI's naive direct PUT endpoint into an 
  event-driven approval ledger (attendance_corrections) to maintain audit trails.
- Zero-Division Guards: Added checks for courses with 0 completed sessions so 
  student analytics default safely to 100% without raising ZeroDivisionError.

AI OUTPUT THAT WAS WRONG:
1. Recovery Math: The AI initially computed recovery sessions using naive integer 
   subtraction: `(0.75 * total) - attended`. This fails because every future class 
   attended also increases the total session count (the denominator).
2. Data Integrity: The initial suggested schema allowed faculty to update past 
   records directly in-place, violating statutory academic audit requirements.

HOW I IDENTIFIED THE PROBLEM:
1. Tested with a scenario: Total = 10, Attended = 5 (50%). 
   The AI formula suggested 2.5 -> 3 classes needed. 
   Checking the result: (5 + 3) / (10 + 3) = 8 / 13 = 61.5%, which is still well 
   below the required 75%.
2. Institutional compliance analysis: In higher-education ERPs, attendance logs 
   serve as official records for examination clearance and cannot be silently 
   overwritten without reviewer attribution.

HOW I FIXED IT:
1. Derived the linear inequality:
   (P + k) / (T + k) >= 0.75  ==>  k >= (0.75 * T - P) / 0.25
   Implemented `math.ceil((0.75 * total - attended) / 0.25)`.
2. Created a dedicated `attendance_corrections` table with explicit state 
   transitions (PENDING -> APPROVED / REJECTED) requiring HOD/Admin review.
======================================================================
