import csv
import io
import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.db import get_db
from app.schemas import (
    AvailabilityIn,
    ExamIn,
    InvigilatorIn,
    RegistrationIn,
    RoomBlockIn,
    RoomIn,
    StudentIn,
    SubjectIn,
    UnavailabilityIn,
)

router = APIRouter()


def audit(db, action, entity, previous="", new="", reason="", plan_version=None):
    from datetime import datetime

    db.execute(
        """
        INSERT INTO audit_events
        (timestamp, username, action, entity, previous_value, new_value, reason, plan_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(),
            "coordinator@examflow.app",
            action,
            entity,
            previous,
            new,
            reason,
            plan_version,
        ),
    )


@router.get("/api/students")
def list_students(
    search: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    with get_db() as db:
        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if search:
            query += " AND (name LIKE ? OR roll LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        if department:
            query += " AND department = ?"
            params.append(department)

        if semester:
            query += " AND semester = ?"
            params.append(semester)

        total = db.execute(
            f"SELECT COUNT(*) FROM ({query})", params
        ).fetchone()[0]

        query += " ORDER BY roll LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])

        rows = db.execute(query, params).fetchall()

    return {
        "students": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/students")
def create_student(payload: StudentIn):
    student_id = f"S{uuid.uuid4().hex[:8].upper()}"

    with get_db() as db:
        try:
            db.execute(
                """
                INSERT INTO students
                (id, roll, name, department, semester, email, special_needs, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    payload.roll,
                    payload.name,
                    payload.department,
                    payload.semester,
                    payload.email,
                    payload.special_needs,
                    payload.status,
                ),
            )
            audit(db, "Created student", payload.roll, "", payload.name)
        except Exception as exc:
            raise HTTPException(
                status_code=409,
                detail="Student ID or roll number already exists.",
            ) from exc

    return {"id": student_id, "message": "Student created."}


@router.put("/api/students/{student_id}")
def update_student(student_id: str, payload: StudentIn):
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Student not found.")

        db.execute(
            """
            UPDATE students
            SET roll = ?, name = ?, department = ?, semester = ?, email = ?,
                special_needs = ?, status = ?
            WHERE id = ?
            """,
            (
                payload.roll,
                payload.name,
                payload.department,
                payload.semester,
                payload.email,
                payload.special_needs,
                payload.status,
                student_id,
            ),
        )
        audit(
            db,
            "Updated student",
            existing["roll"],
            existing["name"],
            payload.name,
        )

    return {"message": "Student updated."}


@router.delete("/api/students/{student_id}")
def delete_student(student_id: str):
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Student not found.")

        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        audit(db, "Deleted student", existing["roll"], existing["name"], "")

    return {"message": "Student deleted."}


@router.post("/api/students/import")
async def import_students(file: UploadFile):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file.")

    contents = await file.read()
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))
    required = {"roll", "name", "department", "semester"}

    if not reader.fieldnames or not required.issubset(
        {field.strip().lower() for field in reader.fieldnames}
    ):
        raise HTTPException(
            status_code=400,
            detail="CSV must include roll, name, department, and semester columns.",
        )

    valid_rows = []
    errors = []

    with get_db() as db:
        existing_rolls = {
            row["roll"] for row in db.execute("SELECT roll FROM students")
        }

        for row_number, row in enumerate(reader, start=2):
            row = {key.strip().lower(): value.strip() for key, value in row.items()}

            if not row.get("roll") or not row.get("name"):
                errors.append(
                    {"row": row_number, "error": "Roll and name are required."}
                )
                continue

            if row["roll"] in existing_rolls:
                errors.append(
                    {"row": row_number, "error": f"Duplicate roll: {row['roll']}"}
                )
                continue

            valid_rows.append(
                (
                    f"S{uuid.uuid4().hex[:8].upper()}",
                    row["roll"],
                    row["name"],
                    row.get("department", "General"),
                    row.get("semester", "Semester 1"),
                    row.get("email", ""),
                    row.get("special_needs", ""),
                    row.get("status", "Active"),
                )
            )
            existing_rolls.add(row["roll"])

        if valid_rows:
            db.executemany(
                """
                INSERT INTO students
                (id, roll, name, department, semester, email, special_needs, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                valid_rows,
            )
            audit(
                db,
                "Imported students",
                "Students",
                "",
                f"{len(valid_rows)} records",
                f"CSV import: {file.filename}",
            )

    return {
        "filename": file.filename,
        "valid_records": len(valid_rows),
        "invalid_records": len(errors),
        "errors": errors,
    }


@router.get("/api/students/export")
def export_students():
    with get_db() as db:
        rows = db.execute("SELECT * FROM students ORDER BY roll").fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "roll", "name", "department", "semester", "email",
         "special_needs", "status"]
    )
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="students.csv"'
        },
    )


@router.get("/api/subjects")
def list_subjects():
    with get_db() as db:
        rows = db.execute("SELECT * FROM subjects ORDER BY code").fetchall()
    return {"subjects": [dict(row) for row in rows]}


@router.post("/api/subjects")
def create_subject(payload: SubjectIn):
    with get_db() as db:
        try:
            db.execute(
                "INSERT INTO subjects VALUES (?, ?, ?, ?)",
                (
                    payload.code,
                    payload.name,
                    payload.department,
                    payload.semester,
                ),
            )
            audit(db, "Created subject", payload.code, "", payload.name)
        except Exception as exc:
            raise HTTPException(
                status_code=409, detail="Subject code already exists."
            ) from exc

    return {"message": "Subject created."}


@router.get("/api/exams")
def list_exams():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT e.id, e.subject_code, s.name AS subject_name,
                   e.exam_date, e.start_time, e.end_time, e.status,
                   COUNT(r.student_id) AS registered_students
            FROM exams e
            JOIN subjects s ON s.code = e.subject_code
            LEFT JOIN registrations r ON r.exam_id = e.id
            GROUP BY e.id
            ORDER BY e.exam_date, e.start_time
            """
        ).fetchall()

    return {"exams": [dict(row) for row in rows]}


@router.post("/api/exams")
def create_exam(payload: ExamIn):
    exam_id = f"EXM-{uuid.uuid4().hex[:8].upper()}"

    with get_db() as db:
        subject = db.execute(
            "SELECT * FROM subjects WHERE code = ?", (payload.subject_code,)
        ).fetchone()

        if not subject:
            raise HTTPException(status_code=400, detail="Subject does not exist.")

        if payload.start_time >= payload.end_time:
            raise HTTPException(
                status_code=400,
                detail="Start time must be before end time.",
            )

        db.execute(
            """
            INSERT INTO exams
            (id, subject_code, exam_date, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                exam_id,
                payload.subject_code,
                payload.exam_date,
                payload.start_time,
                payload.end_time,
                payload.status,
            ),
        )
        audit(db, "Created examination", exam_id, "", payload.subject_code)

    return {"id": exam_id, "message": "Examination created."}


@router.delete("/api/exams/{exam_id}")
def cancel_exam(exam_id: str):
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM exams WHERE id = ?", (exam_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Examination not found.")

        db.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
        audit(
            db,
            "Cancelled examination",
            exam_id,
            existing["status"],
            "Cancelled",
        )

    return {"message": "Examination cancelled."}


@router.post("/api/registrations")
def register_student(payload: RegistrationIn):
    with get_db() as db:
        student = db.execute(
            "SELECT * FROM students WHERE id = ?", (payload.student_id,)
        ).fetchone()
        exam = db.execute(
            "SELECT * FROM exams WHERE id = ?", (payload.exam_id,)
        ).fetchone()

        if not student or not exam:
            raise HTTPException(
                status_code=400,
                detail="Invalid student or examination.",
            )

        try:
            db.execute(
                "INSERT INTO registrations VALUES (?, ?)",
                (payload.student_id, payload.exam_id),
            )
            audit(
                db,
                "Registered student",
                student["roll"],
                "",
                exam["id"],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=409,
                detail="Student is already registered for this examination.",
            ) from exc

    return {"message": "Student registered."}


@router.get("/api/rooms")
def list_rooms():
    with get_db() as db:
        rows = db.execute("SELECT * FROM rooms ORDER BY name").fetchall()
    return {"rooms": [dict(row) for row in rows]}


@router.post("/api/rooms")
def create_room(payload: RoomIn):
    room_id = f"ROOM-{uuid.uuid4().hex[:6].upper()}"

    if payload.usable_capacity > payload.physical_capacity:
        raise HTTPException(
            status_code=400,
            detail="Usable capacity cannot exceed physical capacity.",
        )

    with get_db() as db:
        try:
            db.execute(
                """
                INSERT INTO rooms
                (id, name, building, floor, physical_capacity, usable_capacity,
                 seat_rows, seats_per_row, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    room_id,
                    payload.name,
                    payload.building,
                    payload.floor,
                    payload.physical_capacity,
                    payload.usable_capacity,
                    payload.seat_rows,
                    payload.seats_per_row,
                    payload.status,
                    payload.notes,
                ),
            )
            audit(db, "Created room", payload.name, "", str(payload.usable_capacity))
        except Exception as exc:
            raise HTTPException(
                status_code=409, detail="Room name already exists."
            ) from exc

    return {"id": room_id, "message": "Room created."}


@router.put("/api/rooms/{room_id}/status")
def update_room_status(room_id: str, status: str):
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM rooms WHERE id = ?", (room_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Room not found.")

        db.execute(
            "UPDATE rooms SET status = ? WHERE id = ?", (status, room_id)
        )
        audit(
            db,
            "Changed room status",
            existing["name"],
            existing["status"],
            status,
        )

    return {"message": "Room status updated."}


@router.post("/api/rooms/block")
def block_room(payload: RoomBlockIn):
    with get_db() as db:
        room = db.execute(
            "SELECT * FROM rooms WHERE id = ?", (payload.room_id,)
        ).fetchone()

        if not room:
            raise HTTPException(status_code=404, detail="Room not found.")

        db.execute(
            """
            INSERT INTO room_blocks
            (room_id, block_date, start_time, end_time, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.room_id,
                payload.block_date,
                payload.start_time,
                payload.end_time,
                payload.reason,
            ),
        )
        audit(
            db,
            "Blocked room",
            room["name"],
            "Available",
            f"Blocked {payload.block_date} {payload.start_time}-{payload.end_time}",
            payload.reason,
        )

    return {"message": "Room blocked for the selected period."}


@router.get("/api/invigilators")
def list_invigilators():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT i.*,
                   COUNT(DISTINCT a.id) AS availability_count,
                   COUNT(DISTINCT u.id) AS unavailability_count
            FROM invigilators i
            LEFT JOIN staff_availability a ON a.invigilator_id = i.id
            LEFT JOIN staff_unavailability u ON u.invigilator_id = i.id
            GROUP BY i.id
            ORDER BY i.name
            """
        ).fetchall()

    return {"invigilators": [dict(row) for row in rows]}


@router.post("/api/invigilators")
def create_invigilator(payload: InvigilatorIn):
    invigilator_id = f"INV-{uuid.uuid4().hex[:6].upper()}"

    with get_db() as db:
        db.execute(
            """
            INSERT INTO invigilators
            (id, name, department, email, max_workload, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                invigilator_id,
                payload.name,
                payload.department,
                payload.email,
                payload.max_workload,
                payload.status,
            ),
        )
        audit(db, "Created invigilator", payload.name, "", payload.name)

    return {"id": invigilator_id, "message": "Invigilator created."}


@router.post("/api/invigilators/availability")
def add_availability(payload: AvailabilityIn):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO staff_availability
            (invigilator_id, available_date, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.invigilator_id,
                payload.available_date,
                payload.start_time,
                payload.end_time,
            ),
        )
        audit(db, "Added staff availability", payload.invigilator_id, "", "")

    return {"message": "Availability added."}


@router.post("/api/invigilators/unavailability")
def add_unavailability(payload: UnavailabilityIn):
    with get_db() as db:
        db.execute(
            """
            INSERT INTO staff_unavailability
            (invigilator_id, unavailable_date, start_time, end_time, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.invigilator_id,
                payload.unavailable_date,
                payload.start_time,
                payload.end_time,
                payload.reason,
            ),
        )
        audit(
            db,
            "Added staff absence",
            payload.invigilator_id,
            "Available",
            "Unavailable",
            payload.reason,
        )

    return {"message": "Absence added."}