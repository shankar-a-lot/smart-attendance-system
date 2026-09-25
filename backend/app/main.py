import datetime
import math
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import (
    Base, User, Course, AttendanceSession, AttendanceRecord,
    AttendanceCorrection, AttendanceAlert, Enrollment
)
from app.services.alerts import evaluate_and_dispatch_alerts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Edumerge Smart Attendance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class RecordIn(BaseModel):
    student_id: int
    status: str

class MarkAttendanceRequest(BaseModel):
    course_id: int
    faculty_id: int
    session_date: datetime.date
    slot_number: int
    section: str
    records: List[RecordIn]

class CorrectionRequest(BaseModel):
    record_id: int
    requested_status: str
    reason: str
    requested_by: int

# --- REQUIREMENT 2: STRICT LEAST PRIVILEGE RECORDING ---

@app.post("/api/v1/attendance/mark")
def mark_attendance(payload: MarkAttendanceRequest, db: Session = Depends(get_db)):
    # Least-Privilege Check: Validate faculty ownership of the course
    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course or course.faculty_id != payload.faculty_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: You are not authorized to record attendance for this course."
        )

    # Check for slot collision / duplicate session
    existing_session = db.query(AttendanceSession).filter(
        AttendanceSession.course_id == payload.course_id,
        AttendanceSession.session_date == payload.session_date,
        AttendanceSession.slot_number == payload.slot_number,
        AttendanceSession.section == payload.section
    ).first()

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already exists for this slot. Use the correction workflow to make edits."
        )

    session_entry = AttendanceSession(
        course_id=payload.course_id,
        faculty_id=payload.faculty_id,
        session_date=payload.session_date,
        slot_number=payload.slot_number,
        section=payload.section
    )
    db.add(session_entry)
    db.flush()

    for item in payload.records:
        rec = AttendanceRecord(
            session_id=session_entry.id,
            student_id=item.student_id,
            status=item.status
        )
        db.add(rec)

    db.commit()

    # Trigger Requirement 1: Background alert check
    evaluate_and_dispatch_alerts(db, payload.course_id, payload.section)

    return {"status": "SUCCESS", "session_id": session_entry.id}

@app.post("/api/v1/attendance/request-correction")
def request_correction(payload: CorrectionRequest, db: Session = Depends(get_db)):
    """Faculty cannot silently overwrite past data; they can only raise a request."""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == payload.record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    correction = AttendanceCorrection(
        record_id=payload.record_id,
        previous_status=record.status,
        requested_status=payload.requested_status,
        reason=payload.reason,
        requested_by=payload.requested_by,
        status="PENDING"
    )
    db.add(correction)
    db.commit()
    return {"status": "PENDING_APPROVAL", "message": "Correction request logged for HOD review."}

@app.post("/api/v1/attendance/review-correction/{correction_id}")
def review_correction(correction_id: int, approve: bool, reviewer_id: int, db: Session = Depends(get_db)):
    """Only HOD or Admin can approve/reject changes."""
    reviewer = db.query(User).filter(User.id == reviewer_id).first()
    if not reviewer or reviewer.role not in ("ADMIN", "HOD"):
        raise HTTPException(status_code=403, detail="Only HOD or Admin can review corrections.")

    corr = db.query(AttendanceCorrection).filter(AttendanceCorrection.id == correction_id).first()
    if not corr or corr.status != "PENDING":
        raise HTTPException(status_code=400, detail="Invalid correction request.")

    if approve:
        corr.status = "APPROVED"
        rec = db.query(AttendanceRecord).filter(AttendanceRecord.id == corr.record_id).first()
        rec.status = corr.requested_status
    else:
        corr.status = "REJECTED"

    corr.reviewed_by = reviewer_id
    db.commit()
    return {"status": corr.status}

# --- REQUIREMENT 3: STUDENT PERFORMANCE & SUBJECT RECORDS ---

@app.get("/api/v1/student/{student_id}/analytics")
def get_student_records(student_id: int, db: Session = Depends(get_db)):
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()
    results = []

    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        
        # Calculate subject statistics
        records = (
            db.query(AttendanceRecord.status)
            .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
            .filter(
                AttendanceSession.course_id == enr.course_id,
                AttendanceRecord.student_id == student_id
            )
            .all()
        )
        
        total = len(records)
        attended = sum(1 for r in records if r.status in ("PRESENT", "EXCUSED"))
        pct = round((attended / total) * 100, 2) if total > 0 else 100.0

        # Math formula: consecutive classes needed for >= 75%
        # (attended + k) / (total + k) >= 0.75  =>  k >= (0.75*total - attended) / 0.25
        needed = 0
        if pct < 75.0:
            needed = max(0, math.ceil((0.75 * total - attended) / 0.25))

        results.append({
            "course_code": course.code,
            "course_title": course.title,
            "total_classes": total,
            "attended_classes": attended,
            "percentage": pct,
            "is_shortage": pct < 75.0,
            "classes_needed_for_75": needed,
            "status_indicator": "CRITICAL" if pct < 65 else ("WARNING" if pct < 75 else "HEALTHY")
        })

    return {"student_id": student_id, "courses": results}

@app.get("/api/v1/faculty/{user_id}/alerts")
def get_faculty_alerts(user_id: int, db: Session = Depends(get_db)):
    alerts = (
        db.query(AttendanceAlert, User.full_name, Course.code)
        .join(User, AttendanceAlert.student_id == User.id)
        .join(Course, AttendanceAlert.course_id == Course.id)
        .filter(AttendanceAlert.notified_to_user_id == user_id, AttendanceAlert.is_acknowledged == False)
        .all()
    )
    return [
        {
            "alert_id": a.AttendanceAlert.id,
            "student_name": a.full_name,
            "course_code": a.code,
            "percentage": a.AttendanceAlert.current_percentage,
            "role_alerted": a.AttendanceAlert.role_alerted,
            "created_at": a.AttendanceAlert.created_at
        }
        for a in alerts
    ]