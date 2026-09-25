import React, { useState, useEffect } from "react";

interface CourseAnalytics {
  course_code: string;
  course_title: string;
  total_classes: number;
  attended_classes: number;
  percentage: number;
  is_shortage: boolean;
  classes_needed_for_75: number;
  status_indicator: string;
}

interface StudentAnalyticsResponse {
  student_id: number;
  courses: CourseAnalytics[];
}

interface AlertItem {
  alert_id: number;
  student_name: string;
  course_code: string;
  percentage: number;
  role_alerted: string;
}

export default function App() {
  const [role, setRole] = useState<"STUDENT" | "FACULTY">("STUDENT");
  const [studentData, setStudentData] = useState<StudentAnalyticsResponse | null>(null);
  const [facultyAlerts, setFacultyAlerts] = useState<AlertItem[]>([]);
  const [students, setStudents] = useState([
    { id: 101, name: "Arjun Verma", roll: "CS2101", status: "PRESENT" },
    { id: 102, name: "Sneha Reddy", roll: "CS2102", status: "PRESENT" },
    { id: 103, name: "Kiran Kumar", roll: "CS2103", status: "ABSENT" },
  ]);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/student/101/analytics")
      .then((res) => res.json())
      .then((data) => setStudentData(data))
      .catch((err) => console.error("Error loading student data:", err));
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/faculty/2/alerts")
      .then((res) => res.json())
      .then((data) => setFacultyAlerts(data))
      .catch((err) => console.error("Error loading alerts:", err));
  }, []);

  const toggleStatus = (id: number, newStatus: string) => {
    setStudents((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: newStatus } : s))
    );
  };

  const handleBulkSubmit = () => {
    const payload = {
      course_id: 1,
      faculty_id: 2,
      session_date: new Date().toISOString().split("T")[0],
      slot_number: 3,
      section: "A",
      records: students.map((s) => ({ student_id: s.id, status: s.status })),
    };

    fetch("http://localhost:8000/api/v1/attendance/mark", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((res) => {
        if (res.status === "SUCCESS") {
          setSubmitted(true);
          alert("Attendance recorded successfully!");
        } else {
          alert(res.detail || "Error saving records");
        }
      });
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <nav className="bg-white border-b px-6 py-4 flex flex-wrap justify-between items-center shadow-sm">
        <span className="font-bold text-slate-800 tracking-tight text-lg">
          Edumerge Smart Attendance
        </span>
        <div className="flex gap-2 mt-2 sm:mt-0">
          <button
            onClick={() => setRole("STUDENT")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              role === "STUDENT" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"
            }`}
          >
            Student Portal (Arjun)
          </button>
          <button
            onClick={() => setRole("FACULTY")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              role === "FACULTY" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"
            }`}
          >
            Faculty Dashboard (Prof. Sunita)
          </button>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto p-6">
        {role === "STUDENT" ? (
          <div>
            <header className="mb-6">
              <h1 className="text-2xl font-bold text-slate-800">My Subject Attendance & Performance</h1>
              <p className="text-sm text-slate-500">Track subject-wise eligibility and recovery requirements.</p>
            </header>

            {!studentData ? (
              <p className="text-sm text-slate-400">Loading student records from backend...</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {studentData.courses?.map((c) => (
                  <div key={c.course_code} className="bg-white border rounded-xl p-5 shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                          {c.course_code}
                        </span>
                        <h2 className="text-lg font-bold text-slate-800 mt-1">{c.course_title}</h2>
                      </div>
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                          c.percentage < 75 ? "bg-rose-100 text-rose-700" : "bg-emerald-100 text-emerald-700"
                        }`}
                      >
                        {c.percentage}%
                      </span>
                    </div>

                    <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden mb-4">
                      <div
                        className={`h-full ${c.percentage >= 75 ? "bg-emerald-500" : "bg-rose-500"}`}
                        style={{ width: `${Math.min(c.percentage, 100)}%` }}
                      />
                    </div>

                    <div className="flex justify-between text-xs text-slate-600 border-t pt-3">
                      <span>Attended: <strong>{c.attended_classes}</strong></span>
                      <span>Total Classes: <strong>{c.total_classes}</strong></span>
                    </div>

                    {c.is_shortage ? (
                      <div className="mt-4 p-3 bg-rose-50 rounded-lg border border-rose-200 text-xs text-rose-800">
                        ⚠️ <strong>Low Attendance Alert:</strong> Attend next <strong>{c.classes_needed_for_75}</strong> consecutive sessions to restore 75% standing.
                      </div>
                    ) : (
                      <div className="mt-4 p-3 bg-emerald-50 rounded-lg border border-emerald-200 text-xs text-emerald-800">
                        ✓ In good standing. Eligible for exams.
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div>
            {facultyAlerts.length > 0 && (
              <div className="mb-6 bg-rose-50 border border-rose-300 rounded-xl p-4">
                <h3 className="text-sm font-bold text-rose-900">
                  🔔 Automated Low Attendance Alerts ({facultyAlerts.length})
                </h3>
                <p className="text-xs text-rose-700 mt-1">
                  Alerts automatically sent to respective Class Teacher & Head of Section:
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {facultyAlerts.map((a) => (
                    <span key={a.alert_id} className="text-xs bg-white border border-rose-200 px-3 py-1 rounded-md text-rose-800 shadow-sm">
                      <strong>{a.student_name}</strong> ({a.course_code}) — {a.percentage}%
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white border rounded-xl shadow-sm p-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-bold text-slate-800">Mark Attendance: Data Structures (CS301)</h2>
                  <p className="text-xs text-slate-500">Section A • Today's Session</p>
                </div>
                <button
                  onClick={() => setStudents(students.map((s) => ({ ...s, status: "PRESENT" })))}
                  className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg border font-medium"
                >
                  Mark All Present
                </button>
              </div>

              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b text-xs text-slate-400 font-semibold uppercase">
                    <th className="py-2">Roll No</th>
                    <th className="py-2">Student Name</th>
                    <th className="py-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y text-sm">
                  {students.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50">
                      <td className="py-3 font-mono text-xs text-slate-500">{s.roll}</td>
                      <td className="py-3 font-medium text-slate-800">{s.name}</td>
                      <td className="py-3 text-right">
                        <div className="inline-flex rounded-lg border p-0.5 bg-slate-100">
                          {["PRESENT", "ABSENT", "EXCUSED"].map((st) => (
                            <button
                              key={st}
                              onClick={() => toggleStatus(s.id, st)}
                              className={`text-xs px-3 py-1 rounded-md transition font-medium ${
                                s.status === st
                                  ? st === "PRESENT"
                                    ? "bg-emerald-600 text-white shadow-sm"
                                    : st === "ABSENT"
                                    ? "bg-rose-600 text-white shadow-sm"
                                    : "bg-amber-600 text-white shadow-sm"
                                  : "text-slate-600 hover:text-slate-900"
                              }`}
                            >
                              {st}
                            </button>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="mt-6 flex justify-end">
                <button
                  disabled={submitted}
                  onClick={handleBulkSubmit}
                  className={`px-5 py-2 text-sm font-semibold rounded-lg text-white ${
                    submitted ? "bg-slate-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
                  }`}
                >
                  {submitted ? "Attendance Saved & Locked" : "Submit Attendance"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}