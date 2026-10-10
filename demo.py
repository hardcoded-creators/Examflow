import json
import random
from datetime import datetime, timedelta

from app.db import get_db


def load_demo_data():
    random.seed(42)

    with get_db() as db:
        db.executescript(
            """
            DELETE FROM audit_events;
            DELETE FROM conflicts;
            DELETE FROM invigilator_assignments;
            DELETE FROM seat_assignments;
            DELETE FROM plan_versions;
            DELETE FROM staff_unavailability;
            DELETE FROM staff_availability;
            DELETE FROM invigilators;
            DELETE FROM room_blocks;
            DELETE FROM rooms;
            DELETE FROM registrations;
            DELETE FROM exams;
            DELETE FROM subjects;
            DELETE FROM students;
            """
        )

        departments = ["CSE", "ECE", "MECH", "CIVIL"]
        subjects = [
            ("CS101", "Data Structures", "CSE", "Semester 3"),
            ("CS102", "Operating Systems", "CSE", "Semester 3"),
            ("EC201", "Digital Electronics", "ECE", "Semester 3"),
            ("ME101", "Thermodynamics", "MECH", "Semester 3"),
            ("CE101", "Structural Analysis", "CIVIL", "Semester 3"),
        ]

        for code, name, department, semester in subjects:
            db.execute(
                "INSERT INTO subjects VALUES (?, ?, ?, ?)",
                (code, name, department, semester),
            )

        student_ids = []
        for index in range(1, 121):
            student_id = f"S{index:04d}"
            student_ids.append(student_id)
            db.execute(
                """
                INSERT INTO students
                (id, roll, name, department, semester, email, special_needs, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    f"22CS{index:03d}",
                    f"Student {index}",
                    random.choice(departments),
                    "Semester 3",
                    f"student{index}@college.edu",
                    "Front-row seating" if index % 40 == 0 else "",
                    "Active",
                ),
            )

        exam_date = "2026-10-20"
        exam_ids = []

        for index, (code, name, department, semester) in enumerate(subjects):
            exam_id = f"EXM-{index + 1:03d}"
            exam_ids.append(exam_id)

            start_hour = 9 + index
            db.execute(
                """
                INSERT INTO exams
                (id, subject_code, exam_date, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    exam_id,
                    code,
                    exam_date,
                    f"{start_hour:02d}:00",
                    f"{start_hour + 2:02d}:00",
                    "Scheduled",
                ),
            )

            registered = random.sample(student_ids, random.randint(18, 32))
            for student_id in registered:
                db.execute(
                    "INSERT INTO registrations VALUES (?, ?)",
                    (student_id, exam_id),
                )

        rooms = [
            ("ROOM-A", "Hall A", "Main Block", "1", 60, 60, 6, 10),
            ("ROOM-B", "Hall B", "Main Block", "2", 50, 50, 5, 10),
            ("ROOM-C", "Hall C", "Science Block", "1", 40, 40, 4, 10),
            ("ROOM-D", "Hall D", "Science Block", "2", 30, 30, 3, 10),
        ]

        for room in rooms:
            db.execute(
                """
                INSERT INTO rooms
                (id, name, building, floor, physical_capacity, usable_capacity,
                 seat_rows, seats_per_row, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*room, "Available", ""),
            )

        invigilators = [
            ("INV-001", "Dr. Anita Rao", "CSE", 3),
            ("INV-002", "Prof. Ravi Kumar", "ECE", 3),
            ("INV-003", "Dr. Meena Iyer", "MECH", 2),
            ("INV-004", "Prof. Arjun Nair", "CIVIL", 3),
            ("INV-005", "Dr. Kavya Menon", "CSE", 2),
            ("INV-006", "Prof. Suresh Babu", "ECE", 3),
        ]

        for invigilator in invigilators:
            db.execute(
                "INSERT INTO invigilators VALUES (?, ?, ?, ?, ?, ?)",
                (*invigilator, "Active"),
            )

            db.execute(
                """
                INSERT INTO staff_availability
                (invigilator_id, available_date, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """,
                (invigilator[0], exam_date, "08:00", "18:00"),
            )

        db.execute(
            """
            INSERT INTO staff_unavailability
            (invigilator_id, unavailable_date, start_time, end_time, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("INV-003", exam_date, "09:00", "11:00", "Approved leave"),
        )

        db.execute(
            """
            INSERT INTO audit_events
            (timestamp, username, action, entity, previous_value, new_value, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                "coordinator@examflow.app",
                "Loaded demonstration dataset",
                "System",
                "",
                "120 students, 5 examinations, 4 rooms, 6 invigilators",
                "Initial demonstration setup",
            ),
        )

    return {"message": "Demo data loaded successfully."}