import math
from sqlalchemy.orm import Session
from app.models import (
    AttendanceRecord, AttendanceSession, Course, Department, User, AttendanceAlert
)

def evaluate_and_dispatch_alerts(db: Session, course_id: int, section: str):
    """
    Evaluates attendance for all students in a course/section.
    If attendance is strictly below 75%, automatically creates alerts 
    for the course teacher and the department HOD.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return
    dept = db.query(Department).filter(Department.id == course.department_id).first()

    # Get all distinct sessions for this course and section
    total_sessions = db.query(AttendanceSession).filter(
        AttendanceSession.course_id == course_id,
        AttendanceSession.section == section
    ).count()

    if total_sessions < 3: # Allow minimum baseline before triggering warnings
        return

    # Aggregate attendance for students in this course & section
    student_records = (
        db.query(AttendanceRecord.student_id, AttendanceRecord.status)
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
        .filter(AttendanceSession.course_id == course_id, AttendanceSession.section == section)
        .all()
    )

    stats = {}
    for sid, status in student_records:
        if sid not in stats:
            stats[sid] = {"attended": 0, "total": 0}
        stats[sid]["total"] += 1
        if status in ("PRESENT", "EXCUSED"):
            stats[sid]["attended"] += 1

    for sid, data in stats.items():
        pct = round((data["attended"] / data["total"]) * 100, 2)
        if pct < 75.0:
            # 1. Alert Course/Class Teacher
            existing_teacher_alert = db.query(AttendanceAlert).filter(
                AttendanceAlert.student_id == sid,
                AttendanceAlert.course_id == course_id,
                AttendanceAlert.notified_to_user_id == course.faculty_id,
                AttendanceAlert.is_acknowledged == False
            ).first()

            if not existing_teacher_alert and course.faculty_id:
                db.add(AttendanceAlert(
                    student_id=sid,
                    course_id=course_id,
                    current_percentage=pct,
                    notified_to_user_id=course.faculty_id,
                    role_alerted="CLASS_TEACHER"
                ))

            # 2. Alert Department HOD
            if dept and dept.hod_id:
                existing_hod_alert = db.query(AttendanceAlert).filter(
                    AttendanceAlert.student_id == sid,
                    AttendanceAlert.course_id == course_id,
                    AttendanceAlert.notified_to_user_id == dept.hod_id,
                    AttendanceAlert.is_acknowledged == False
                ).first()

                if not existing_hod_alert:
                    db.add(AttendanceAlert(
                        student_id=sid,
                        course_id=course_id,
                        current_percentage=pct,
                        notified_to_user_id=dept.hod_id,
                        role_alerted="HOD"
                    ))

    db.commit()