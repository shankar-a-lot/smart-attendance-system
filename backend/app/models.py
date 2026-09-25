import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, 
    DateTime, Date, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    hod_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'ADMIN', 'HOD', 'FACULTY', 'STUDENT'
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    section = Column(String, nullable=True) # e.g. 'A', 'B'

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    faculty_id = Column(Integer, ForeignKey("users.id")) # Respective Course/Class Teacher

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    section = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_date = Column(Date, nullable=False, default=datetime.date.today)
    slot_number = Column(Integer, nullable=False) # 1 to 8
    section = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_locked = Column(Boolean, default=False)
    __table_args__ = (
        UniqueConstraint("course_id", "session_date", "slot_number", "section", name="uq_session_slot"),
    )

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False) # 'PRESENT', 'ABSENT', 'EXCUSED'
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="uq_session_student"),)

class AttendanceCorrection(Base):
    __tablename__ = "attendance_corrections"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("attendance_records.id"), nullable=False)
    previous_status = Column(String, nullable=False)
    requested_status = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="PENDING") # 'PENDING', 'APPROVED', 'REJECTED'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AttendanceAlert(Base):
    __tablename__ = "attendance_alerts"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    current_percentage = Column(Float, nullable=False)
    notified_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Teacher or HOD
    role_alerted = Column(String, nullable=False) # 'CLASS_TEACHER', 'HOD'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_acknowledged = Column(Boolean, default=False)