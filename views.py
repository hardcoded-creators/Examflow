import json
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io
import csv

from app.db import get_db
from app.scheduler import overlaps

router = APIRouter()


@router.get("/api/dashboard")
def dashboard():
    with get_db() as db:
        students = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        exams = db.execute("SELECT COUNT(*) FROM exams").fetchone()[0]
        rooms = db.execute(
            "SELECT COUNT(*) FROM rooms WHERE status = 'Available'"
        ).fetchone()[0]
        invigilators = db.execute(
            "SELECT COUNT(*) FROM invigilators WHERE status = 'Active'"
        ).fetchone()[0]

        latest_plan = db.execute(
            "SELECT * FROM plan_versions ORDER BY id DESC LIMIT 1"
        ).fetchone()

        assigned_students = 0
        active_conflicts = 0
        unassigned_students = 0
        completion = 0

        if latest_plan:
            assigned_students = db.execute(
                "SELECT COUNT(*) FROM seat_assignments WHERE plan_version = ?",
                (latest_plan["id"],),
            ).fetchone()[0]

            active_conflicts = db.execute(
                """
                SELECT COUNT(*) FROM conflicts
                WHERE plan_version = ? AND severity = 'Critical'
                """,
                (latest_plan["id"],),
            ).fetchone()[0]

            snapshot = json.loads(latest_plan["snapshot"])
            unassigned_students = len(snapshot.get("unassigned_students", []))

            total_required = db.execute(
                "SELECT COUNT(*) FROM registrations"
            ).fetchone()[0]

            if total_required:
                completion = round(
                    assigned_students / total_required * 100, 1
                )

        room_utilization = []
        for room in db.execute("SELECT * FROM rooms"):
            assigned = 0

            if latest_plan:
                assigned = db.execute(
                    """
                    SELECT COUNT(*) FROM seat_assignments
                    WHERE plan_version = ? AND room_id = ?
                    """,
                    (latest_plan["id"], room["id"]),
                ).fetchone()[0]

            room_utilization.append(
                {
                    "room": room["name"],
                    "utilization": round(
                        assigned / room["usable_capacity"] * 100, 1
                    ) if room["usable_capacity"] else 0,
                }
            )

        upcoming = db.execute(
            """
            SELECT e.id, e.subject_code, s.name AS subject_name,
                   e.exam_date, e.start_time, e.end_time, e.status,
                   COUNT(r.student_id) AS registered_students
            FROM exams e
            JOIN subjects s ON s.code = e.subject_code
            LEFT JOIN registrations r ON r.exam_id = e.id
            GROUP BY e.id
            ORDER BY e.exam_date, e.start_time
            LIMIT 10
            """
        ).fetchall()

        activity = db.execute(
            "SELECT * FROM audit_events ORDER BY id DESC LIMIT 8"
        ).fetchall()

    return {
        "metrics": {
            "total_students": students,
            "scheduled_examinations": exams,
            "available_rooms": rooms,
            "available_invigilators": invigilators,
            "unassigned_students": unassigned_students,
            "active_conflicts": active_conflicts,
            "plan_completion_percent": completion,
            "latest_plan_status": latest_plan["status"] if latest_plan else "No plan",
        },
        "upcoming_examinations": [dict(row) for row in upcoming],
        "room_utilization": room_utilization,
        "recent_activity": [dict(row) for row in activity],
    }


@router.get("/api/seating")
def seating(plan_version: int, exam_id: str):
    with get_db() as db:
        assignments = db.execute(
            """
            SELECT sa.*, st.roll, st.name AS student_name,
                   r.name AS room_name, r.seat_rows, r.seats_per_row
            FROM seat_assignments sa
            JOIN students st ON st.id = sa.student_id
            JOIN rooms r ON r.id = sa.room_id
            WHERE sa.plan_version = ? AND sa.exam_id = ?
            ORDER BY sa.room_id, sa.seat_row, sa.seat_col
            """,
            (plan_version, exam_id),
        ).fetchall()

        if not assignments:
            raise HTTPException(
                status_code=404,
                detail="No seating assignments found for this plan and examination.",
            )

    return {"seating": [dict(row) for row in assignments]}


@router.get("/api/seating/export")
def export_seating(plan_version: int, exam_id: str):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT st.roll, st.name, r.name AS room,
                   sa.seat_label, sa.seat_row, sa.seat_col
            FROM seat_assignments sa
            JOIN students st ON st.id = sa.student_id
            JOIN rooms r ON r.id = sa.room_id
            WHERE sa.plan_version = ? AND sa.exam_id = ?
            ORDER BY r.name, sa.seat_row, sa.seat_col
            """,
            (plan_version, exam_id),
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["roll", "student_name", "room", "seat_label", "row", "column"]
    )
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="seating-chart.csv"'
        },
    )


@router.get("/api/conflicts")
def list_conflicts(plan_version: int):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM conflicts WHERE plan_version = ? ORDER BY id",
            (plan_version,),
        ).fetchall()

    return {"conflicts": [dict(row) for row in rows]}


@router.get("/api/timetable")
def timetable():
    with get_db() as db:
        latest = db.execute(
            "SELECT id FROM plan_versions ORDER BY id DESC LIMIT 1"
        ).fetchone()

        plan_version = latest["id"] if latest else None

        rows = db.execute(
            """
            SELECT e.id, e.subject_code, s.name AS subject_name,
                   e.exam_date, e.start_time, e.end_time, e.status,
                   COUNT(DISTINCT r.student_id) AS registered_students,
                   COUNT(DISTINCT sa.room_id) AS assigned_rooms
            FROM exams e
            JOIN subjects s ON s.code = e.subject_code
            LEFT JOIN registrations r ON r.exam_id = e.id
            LEFT JOIN seat_assignments sa
                ON sa.exam_id = e.id AND sa.plan_version = ?
            GROUP BY e.id
            ORDER BY e.exam_date, e.start_time
            """,
            (plan_version,),
        ).fetchall()

    return {
        "plan_version": plan_version,
        "timetable": [dict(row) for row in rows],
    }


@router.get("/api/audit")
def audit_history():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM audit_events ORDER BY id DESC LIMIT 200"
        ).fetchall()

    return {"events": [dict(row) for row in rows]}


@router.get("/api/reports/invigilator-roster")
def invigilator_roster(plan_version: int):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT i.name, i.department, e.exam_date, e.start_time,
                   e.end_time, r.name AS room, sub.code AS subject_code
            FROM invigilator_assignments ia
            JOIN invigilators i ON i.id = ia.invigilator_id
            JOIN exams e ON e.id = ia.exam_id
            JOIN subjects sub ON sub.code = e.subject_code
            JOIN rooms r ON r.id = ia.room_id
            WHERE ia.plan_version = ?
            ORDER BY e.exam_date, e.start_time, i.name
            """,
            (plan_version,),
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["invigilator", "department", "date", "start", "end", "room", "subject"]
    )
    writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="invigilator-roster.csv"'
        },
    )