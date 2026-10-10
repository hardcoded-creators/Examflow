import time
from collections import defaultdict
from datetime import datetime

from app.validator import validate_plan


def time_to_minutes(value: str) -> int:
    hour, minute = value.split(":")[:2]
    return int(hour) * 60 + int(minute)


def overlaps(start1, end1, start2, end2):
    return time_to_minutes(start1) < time_to_minutes(end2) and \
        time_to_minutes(start2) < time_to_minutes(end1)


def seat_allowed(row, col, placed, rules):
    """Checks same-subject adjacency against already-placed students."""
    for placed_row, placed_col in placed:
        row_diff = abs(row - placed_row)
        col_diff = abs(col - placed_col)

        if rules.horizontal_separation and row_diff == 0 and col_diff == 1:
            return False
        if rules.vertical_separation and col_diff == 0 and row_diff == 1:
            return False
        if rules.diagonal_separation and row_diff == 1 and col_diff == 1:
            return False

    return True


def room_is_available(room, exam_date, start_time, end_time, blocks):
    if room["status"] != "Available":
        return False

    for block in blocks:
        if block["room_id"] != room["id"]:
            continue
        if block["block_date"] != exam_date:
            continue
        if overlaps(
            start_time,
            end_time,
            block["start_time"],
            block["end_time"],
        ):
            return False

    return True


def invigilator_is_available(
    invigilator,
    exam_date,
    start_time,
    end_time,
    availability,
    unavailability,
    assigned_duties,
):
    if invigilator["status"] != "Active":
        return False

    available = any(
        item["invigilator_id"] == invigilator["id"]
        and item["available_date"] == exam_date
        and time_to_minutes(item["start_time"]) <= time_to_minutes(start_time)
        and time_to_minutes(item["end_time"]) >= time_to_minutes(end_time)
        for item in availability
    )

    if not available:
        return False

    blocked = any(
        item["invigilator_id"] == invigilator["id"]
        and item["unavailable_date"] == exam_date
        and overlaps(
            start_time,
            end_time,
            item["start_time"],
            item["end_time"],
        )
        for item in unavailability
    )

    if blocked:
        return False

    for duty in assigned_duties:
        if duty["invigilator_id"] != invigilator["id"]:
            continue
        if duty["exam_date"] != exam_date:
            continue
        if overlaps(
            start_time,
            end_time,
            duty["start_time"],
            duty["end_time"],
        ):
            return False

    return True


def generate_plan(db, rules: dict, unavailable_room_id=None,
                  unavailable_invigilator_id=None, base_plan_version=None):
    started = time.perf_counter()

    exams = db.execute(
        """
        SELECT e.id, e.subject_code, e.exam_date, e.start_time, e.end_time,
               s.name AS subject_name,
               COUNT(r.student_id) AS student_count
        FROM exams e
        JOIN subjects s ON s.code = e.subject_code
        LEFT JOIN registrations r ON r.exam_id = e.id
        GROUP BY e.id
        ORDER BY e.exam_date, e.start_time, student_count DESC
        """
    ).fetchall()

    rooms = db.execute("SELECT * FROM rooms ORDER BY usable_capacity").fetchall()
    blocks = db.execute("SELECT * FROM room_blocks").fetchall()
    invigilators = db.execute(
        "SELECT * FROM invigilators ORDER BY id"
    ).fetchall()
    availability = db.execute("SELECT * FROM staff_availability").fetchall()
    unavailability = db.execute(
        "SELECT * FROM staff_unavailability"
    ).fetchall()

    registrations = defaultdict(list)
    for row in db.execute("SELECT * FROM registrations"):
        registrations[row["exam_id"]].append(row["student_id"])

    students = {
        row["id"]: row
        for row in db.execute("SELECT * FROM students")
    }

    preserved = []
    if base_plan_version and rules.get("preserve_existing_assignments"):
        preserved = db.execute(
            """
            SELECT * FROM seat_assignments WHERE plan_version = ?
            """,
            (base_plan_version,),
        ).fetchall()

    seat_assignments = []
    invigilator_assignments = []
    unassigned_students = []
    unfilled_positions = []
    used_rooms = set()
    staff_duties = []
    staff_workload = defaultdict(int)

    # Preserve unaffected assignments during replanning.
    preserved_exam_ids = set()
    for assignment in preserved:
        exam = next((e for e in exams if e["id"] == assignment["exam_id"]), None)
        room = next((r for r in rooms if r["id"] == assignment["room_id"]), None)

        if not exam or not room:
            continue

        if unavailable_room_id and room["id"] == unavailable_room_id:
            continue

        if unavailable_invigilator_id:
            staff_assignment = next(
                (
                    item for item in invigilator_assignments
                    if item["exam_id"] == exam["id"]
                    and item["room_id"] == room["id"]
                ),
                None,
            )
            if staff_assignment and staff_assignment["invigilator_id"] == unavailable_invigilator_id:
                continue

        seat_assignments.append(
            {
                "exam_id": exam["id"],
                "student_id": assignment["student_id"],
                "room_id": room["id"],
                "seat_row": assignment["seat_row"],
                "seat_col": assignment["seat_col"],
                "seat_label": assignment["seat_label"],
            }
        )
        preserved_exam_ids.add(exam["id"])
        used_rooms.add(room["id"])

    for exam in exams:
        exam_id = exam["id"]
        student_ids = registrations.get(exam_id, [])

        if exam_id in preserved_exam_ids:
            continue

        if not student_ids:
            continue

        placed = False

        for room in rooms:
            if unavailable_room_id and room["id"] == unavailable_room_id:
                continue

            if not room_is_available(
                room, exam["exam_date"], exam["start_time"],
                exam["end_time"], blocks,
            ):
                continue

            if room["id"] in used_rooms:
                continue

            if room["usable_capacity"] < len(student_ids):
                continue

            seat_placements = []
            placed_coordinates = []
            remaining = list(student_ids)

            for row in range(1, room["seat_rows"] + 1):
                for col in range(1, room["seats_per_row"] + 1):
                    if not remaining:
                        break

                    if not seat_allowed(row, col, placed_coordinates, rules):
                        continue

                    student_id = remaining.pop(0)
                    placed_coordinates.append((row, col))
                    seat_placements.append(
                        {
                            "exam_id": exam_id,
                            "student_id": student_id,
                            "room_id": room["id"],
                            "seat_row": row,
                            "seat_col": col,
                            "seat_label": f"R{row}-C{col}",
                        }
                    )

                if not remaining:
                    break

            if remaining:
                continue

            eligible_invigilators = []
            for invigilator in invigilators:
                if unavailable_invigilator_id and \
                        invigilator["id"] == unavailable_invigilator_id:
                    continue

                if staff_workload[invigilator["id"]] >= invigilator["max_workload"]:
                    continue

                if invigilator_is_available(
                    invigilator,
                    exam["exam_date"],
                    exam["start_time"],
                    exam["end_time"],
                    availability,
                    unavailability,
                    staff_duties,
                ):
                    eligible_invigilators.append(invigilator)

            required_staff = max(1, rules.get("invigilators_per_room", 1))
            if len(eligible_invigilators) < required_staff:
                continue

            selected_staff = eligible_invigilators[:required_staff]

            seat_assignments.extend(seat_placements)
            used_rooms.add(room["id"])

            for invigilator in selected_staff:
                invigilator_assignments.append(
                    {
                        "exam_id": exam_id,
                        "room_id": room["id"],
                        "invigilator_id": invigilator["id"],
                    }
                )
                staff_workload[invigilator["id"]] += 1
                staff_duties.append(
                    {
                        "invigilator_id": invigilator["id"],
                        "exam_date": exam["exam_date"],
                        "start_time": exam["start_time"],
                        "end_time": exam["end_time"],
                    }
                )

            placed = True
            break

        if not placed:
            unassigned_students.extend(student_ids)
            unfilled_positions.append(
                {
                    "exam_id": exam_id,
                    "subject_code": exam["subject_code"],
                    "required_students": len(student_ids),
                    "reason": "No available room with enough usable seats and staff coverage.",
                }
            )

    runtime_ms = int((time.perf_counter() - started) * 1000)

    if unassigned_students or unfilled_positions:
        solver_status = "INFEASIBLE"
    else:
        solver_status = "FEASIBLE"

    return {
        "seat_assignments": seat_assignments,
        "invigilator_assignments": invigilator_assignments,
        "unassigned_students": unassigned_students,
        "unfilled_positions": unfilled_positions,
        "solver_status": solver_status,
        "runtime_ms": runtime_ms,
    }