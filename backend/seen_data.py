import datetime
from app.database import engine, SessionLocal
from app.models import Base, User, Course, Department, Enrollment, AttendanceSession, AttendanceRecord

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Reset DB
db.query(AttendanceRecord).delete()
db.query(AttendanceSession).delete()
db.query(Enrollment).delete()
db.query(Course).delete()
db.query(Department).delete()
db.query(User).delete()

# 1. Departments & Users
dept = Department(name="Computer Science & Engineering")
db.add(dept)
db.flush()

hod = User(full_name="Dr. Ramesh Rao", email="hod.cse@college.edu", hashed_password="hash", role="HOD", department_id=dept.id)
teacher = User(full_name="Prof. Sunita Sharma", email="sunita.cse@college.edu", hashed_password="hash", role="FACULTY", department_id=dept.id)
student_1 = User(id=101, full_name="Arjun Verma", email="arjun@student.edu", hashed_password="hash", role="STUDENT", department_id=dept.id, section="A")
student_2 = User(id=102, full_name="Sneha Reddy", email="sneha@student.edu", hashed_password="hash", role="STUDENT", department_id=dept.id, section="A")
student_3 = User(id=103, full_name="Kiran Kumar", email="kiran@student.edu", hashed_password="hash", role="STUDENT", department_id=dept.id, section="A")

db.add_all([hod, teacher, student_1, student_2, student_3])
db.flush()

dept.hod_id = hod.id

# 2. Courses
c1 = Course(id=1, code="CS301", title="Data Structures & Algorithms", department_id=dept.id, faculty_id=teacher.id)
c2 = Course(id=2, code="CS302", title="Database Management Systems", department_id=dept.id, faculty_id=teacher.id)
db.add_all([c1, c2])
db.flush()

# 3. Enrollments
for s in [student_1, student_2, student_3]:
    db.add(Enrollment(student_id=s.id, course_id=c1.id, section="A"))
    db.add(Enrollment(student_id=s.id, course_id=c2.id, section="A"))

# 4. Past Sessions & Records (Make student 101 have low attendance <75% to trigger alert & recovery)
for i in range(1, 11):
    sess = AttendanceSession(course_id=c1.id, faculty_id=teacher.id, session_date=datetime.date(2026, 9, i), slot_number=1, section="A")
    db.add(sess)
    db.flush()
    # Student 101 attended only 5 out of 10 (50%) -> triggers shortage & alerts
    db.add(AttendanceRecord(session_id=sess.id, student_id=101, status="PRESENT" if i <= 5 else "ABSENT"))
    db.add(AttendanceRecord(session_id=sess.id, student_id=102, status="PRESENT"))
    db.add(AttendanceRecord(session_id=sess.id, student_id=103, status="PRESENT"))

db.commit()
db.close()
print("Database successfully seeded with realistic sample data!")