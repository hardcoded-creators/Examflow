from collections import defaultdict

from app.scheduler import overlaps, time_to_minutes


def validate_plan(db, plan_version, rules):
    assignments = db.execute(
        "SELECT * FROM seat_assignments WHERE plan_version = ?",
        (plan_version,),
    ).fetchall()

    staff_assignments = db.execute(
        "SELECT * FROM invigilator_assignments WHERE plan_version = ?",
        (plan_version,),
    ).fetchall()

    exams = {
        row["id"]: row
        for row in db.execute("SELECT * FROM exams")
    }
    rooms = {
        row["id"]: row
        for row in db.execute("SELECT * FROM rooms")
    }
    invigilators = {
        row["id"]: row
        for row in db.execute("SELECT * FROM invigilators")
    }
    blocks = db.execute("SELECT * FROM room_blocks").fetchall()
    availability = db.execute("SELECT * FROM staff_availability").fetchall()
    unavailability = db.execute(
        "SELECT * FROM staff_unavailability"
    ).fetchall()

    conflicts = []

    def add_conflict(severity, category, entity, exam_id, description, rule, suggestion):
        conflicts.append(
            {
                "severity": severity,
                "category": category,
                "entity": entity,
                "exam_id": exam_id,
                "description": description,
                "rule": rule,
                "suggestion": suggestion,
            }
        )

    room_load = defaultdict(int)
    exam_rooms = defaultdict(set)
    occupied = set()

    for assignment in assignments:
        exam = exams.get(assignment["exam_id"])
        room = rooms.get(assignment["room_id"])

        if not exam or not room:
            add_conflict(
                "Critical",
                "Invalid assignment",
                f"Assignment {assignment['id']}",
                assignment["exam_id"],
                "Assignment refers to an invalid examination or room.",
                "Valid references",
                "Regenerate the plan.",
            )
            continue

        room_load[room["id"]] += 1
        exam_rooms[exam["id"]].add(room["id"])
        occupied.add(
            (assignment["room_id"], assignment["seat_row"], assignment["seat_col"])
        )

        if room["status"] != "Available":
            add_conflict(
                "Critical",
                "Unavailable room assignment",
                room["name"],
                exam["id"],
                f"{room['name']} is marked unavailable but contains assigned students.",
                "Room availability",
                "Replan using another available room.",
            )

        for block in blocks:
            if block["room_id"] != room["id"]:
                continue
            if block["block_date"] != exam["exam_date"]:
                continue

            if overlaps(
                exam["start_time"],
                exam["end_time"],
                block["start_time"],
                block["end_time"],
            ):
                add_conflict(
                    "Critical",
                    "Room blocked during examination",
                    room["name"],
                    exam["id"],
                    f"{room['name']} is blocked during this examination.",
                    "Room availability",
                    "Replan using another available room.",
                )

    for room_id, load in room_load.items():
        room = rooms.get(room_id)
        if room and load > room["usable_capacity"]:
            add_conflict(
                "Critical",
                "Room overcapacity",
                room["name"],
                None,
                f"{room['name']} has {load} students but usable capacity is "
                f"{room['usable_capacity']}.",
                "Room capacity",
                "Move students to another room or increase usable capacity.",
            )

    by_exam_room = defaultdict(list)
    for assignment in assignments:
        by_exam_room[
            (assignment["exam_id"], assignment["room_id"])
        ].append(assignment)

    for (exam_id, room_id), rows in by_exam_room.items():
        room = rooms.get(room_id)
        if not room:
            continue

        for current in rows:
            for other in rows:
                if current["id"] >= other["id"]:
                    continue

                row_diff = abs(current["seat_row"] - other["seat_row"])
                col_diff = abs(current["seat_col"] - other["seat_col"])

                violation = False

                if rules["horizontal_separation"] and row_diff == 0 and col_diff == 1:
                    violation = True

                if rules["vertical_separation"] and col_diff == 0 and row_diff == 1:
                    violation = True

                if rules["diagonal_separation"] and row_diff == 1 and col_diff == 1:
                    violation = True

                if violation:
                    add_conflict(
                        "Critical",
                        "Same-subject seating adjacency",
                        f"{current['seat_label']} / {other['seat_label']}",
                        exam_id,
                        "Two students taking the same examination are seated in "
                        "a prohibited neighboring arrangement.",
                        "Seating adjacency",
                        "Move one student to a valid separated seat and revalidate.",
                    )

    staff_by_exam = defaultdict(list)
    for assignment in staff_assignments:
        staff_by_exam[assignment["exam_id"]].append(assignment)

    for exam_id, duties in staff_by_exam.items():
        exam = exams.get(exam_id)
        if not exam:
            continue

        required = max(1, rules.get("invigilators_per_room", 1))
        room_count = len(exam_rooms.get(exam_id, set()))
        required_total = required * room_count

        if len(duties) < required_total:
            add_conflict(
                "Critical",
                "Insufficient staff coverage",
                exam_id,
                exam_id,
                f"Examination requires {required_total} invigilator assignments "
                f"but has {len(duties)}.",
                "Staff coverage",
                "Assign additional available invigilators or reduce room usage.",
            )

    duty_list = []
    for assignment in staff_assignments:
        exam = exams.get(assignment["exam_id"])
        if not exam:
            continue

        duty_list.append(
            {
                "invigilator_id": assignment["invigilator_id"],
                "exam_date": exam["exam_date"],
                "start_time": exam["start_time"],
                "end_time": exam["end_time"],
            }
        )

    workload = defaultdict(int)
    for duty in duty_list:
        workload[duty["invigilator_id"]] += 1

    for invigilator_id, count in workload.items():
        invigilator = invigilators.get(invigilator_id)
        if invigilator and count > invigilator["max_workload"]:
            add_conflict(
                "Critical",
                "Invigilator workload exceeded",
                invigilator["name"],
                None,
                f"{invigilator['name']} has {count} duties but the maximum is "
                f"{invigilator['max_workload']}.",
                "Staff workload",
                "Reassign duties to eligible invigilators.",
            )

    for i, duty_a in enumerate(duty_list):
        for duty_b in duty_list[i + 1:]:
            if duty_a["invigilator_id"] != duty_b["invigilator_id"]:
                continue
            if duty_a["exam_date"] != duty_b["exam_date"]:
                continue

            if overlaps(
                duty_a["start_time"],
                duty_a["end_time"],
                duty_b["start_time"],
                duty_b["end_time"],
            ):
                add_conflict(
                    "Critical",
                    "Invigilator double-booking",
                    duty_a["invigilator_id"],
                    None,
                    "An invigilator has overlapping duties.",
                    "No overlapping duties",
                    "Assign a substitute invigilator.",
                )

    for duty in duty_list:
        invigilator_id = duty["invigilator_id"]
        invigilator = invigilators.get(invigilator_id)

        if not invigilator:
            continue

        available = any(
            item["invigilator_id"] == invigilator_id
            and item["available_date"] == duty["exam_date"]
            and time_to_minutes(item["start_time"])
            <= time_to_minutes(duty["start_time"])
            and time_to_minutes(item["end_time"])
            >= time_to_minutes(duty["end_time"])
            for item in availability
        )

        if not available:
            add_conflict(
                "Critical",
                "Invigilator unavailable",
                invigilator["name"],
                None,
                f"{invigilator['name']} is assigned outside their available period.",
                "Staff availability",
                "Assign an available substitute.",
            )

        blocked = any(
            item["invigilator_id"] == invigilator_id
            and item["unavailable_date"] == duty["exam_date"]
            and overlaps(
                duty["start_time"],
                duty["end_time"],
                item["start_time"],
                item["end_time"],
            )
            for item in unavailability
        )

        if blocked:
            add_conflict(
                "Critical",
                "Invigilator unavailable",
                invigilator["name"],
                None,
                f"{invigilator['name']} is assigned during a marked absence.",
                "Staff availability",
                "Assign an available substitute.",
            )

    hard_violations = len(
        [item for item in conflicts if item["severity"] == "Critical"]
    )

    return {
        "conflicts": conflicts,
        "hard_violations": hard_violations,
        "assigned_students": len(assignments),
        "status": (
            "Valid"
            if hard_violations == 0
            else "Invalid"
        ),
    }