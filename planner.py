import json
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.db import get_db
from app.scheduler import generate_plan
from app.schemas import ReplanRequest, ScheduleRules
from app.validator import validate_plan

router = APIRouter()


def save_plan(db, result, rules):
    now = datetime.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO plan_versions
        (created_at, status, solver_status, runtime_ms, rules, snapshot)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            now,
            "Draft",
            result["solver_status"],
            result["runtime_ms"],
            json.dumps(rules),
            json.dumps(result),
        ),
    )
    plan_version = cursor.lastrowid

    for assignment in result["seat_assignments"]:
        db.execute(
            """
            INSERT INTO seat_assignments
            (plan_version, exam_id, student_id, room_id, seat_row, seat_col, seat_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_version,
                assignment["exam_id"],
                assignment["student_id"],
                assignment["room_id"],
                assignment["seat_row"],
                assignment["seat_col"],
                assignment["seat_label"],
            ),
        )

    for assignment in result["invigilator_assignments"]:
        db.execute(
            """
            INSERT INTO invigilator_assignments
            (plan_version, exam_id, room_id, invigilator_id)
            VALUES (?, ?, ?, ?)
            """,
            (
                plan_version,
                assignment["exam_id"],
                assignment["room_id"],
                assignment["invigilator_id"],
            ),
        )

    validation = validate_plan(db, plan_version, rules)

    for conflict in validation["conflicts"]:
        db.execute(
            """
            INSERT INTO conflicts
            (plan_version, severity, category, entity, exam_id,
             description, rule, suggestion, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan_version,
                conflict["severity"],
                conflict["category"],
                conflict["entity"],
                conflict["exam_id"],
                conflict["description"],
                conflict["rule"],
                conflict["suggestion"],
                "Open",
            ),
        )

    db.execute(
        """
        INSERT INTO audit_events
        (timestamp, username, action, entity, previous_value, new_value, reason, plan_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now,
            "coordinator@examflow.app",
            "Generated plan",
            "Plan",
            "",
            result["solver_status"],
            "Schedule generated",
            plan_version,
        ),
    )

    return plan_version, validation


@router.post("/api/planner/generate")
def generate_schedule(rules: ScheduleRules):
    with get_db() as db:
        result = generate_plan(db, rules.model_dump())
        plan_version, validation = save_plan(
            db, result, rules.model_dump()
        )

    return {
        "plan_version": plan_version,
        "solver_status": result["solver_status"],
        "runtime_ms": result["runtime_ms"],
        "assigned_students": len(result["seat_assignments"]),
        "unassigned_students": result["unassigned_students"],
        "unfilled_positions": result["unfilled_positions"],
        "validation": validation,
        "message": (
            "Plan generated successfully."
            if result["solver_status"] == "FEASIBLE"
            else "Plan generated, but constraints could not be fully satisfied."
        ),
    }


@router.post("/api/planner/replan")
def replan_schedule(payload: ReplanRequest):
    with get_db() as db:
        base_plan = db.execute(
            "SELECT * FROM plan_versions WHERE id = ?",
            (payload.base_plan_version,),
        ).fetchone()

        if not base_plan:
            raise HTTPException(status_code=404, detail="Base plan not found.")

        result = generate_plan(
            db,
            payload.rules.model_dump(),
            unavailable_room_id=payload.unavailable_room_id,
            unavailable_invigilator_id=payload.unavailable_invigilator_id,
            base_plan_version=payload.base_plan_version,
        )

        plan_version, validation = save_plan(
            db, result, payload.rules.model_dump()
        )

        previous_assignments = db.execute(
            "SELECT * FROM seat_assignments WHERE plan_version = ?",
            (payload.base_plan_version,),
        ).fetchall()

        new_assignments = db.execute(
            "SELECT * FROM seat_assignments WHERE plan_version = ?",
            (plan_version,),
        ).fetchall()

        previous_map = {
            (row["student_id"], row["exam_id"]): row
            for row in previous_assignments
        }
        new_map = {
            (row["student_id"], row["exam_id"]): row
            for row in new_assignments
        }

        changes = []

        for key, new_assignment in new_map.items():
            old_assignment = previous_map.get(key)

            if not old_assignment:
                reason = "New assignment required by replanning."
                changed = True
            elif (
                old_assignment["room_id"] != new_assignment["room_id"]
                or old_assignment["seat_label"] != new_assignment["seat_label"]
            ):
                reason = "Reassigned because the previous room or seat was unavailable."
                changed = True
            else:
                reason = "Existing assignment preserved."
                changed = False

            if changed:
                changes.append(
                    {
                        "student_id": key[0],
                        "exam_id": key[1],
                        "previous_room_id": old_assignment["room_id"] if old_assignment else None,
                        "new_room_id": new_assignment["room_id"],
                        "previous_seat": old_assignment["seat_label"] if old_assignment else None,
                        "new_seat": new_assignment["seat_label"],
                        "reason": reason,
                        "change_type": "Mandatory",
                    }
                )

        return {
            "plan_version": plan_version,
            "base_plan_version": payload.base_plan_version,
            "solver_status": result["solver_status"],
            "runtime_ms": result["runtime_ms"],
            "students_affected": len(changes),
            "changes": changes,
            "validation": validation,
            "message": (
                "Replanning completed."
                if result["solver_status"] == "FEASIBLE"
                else "Replanning could not satisfy all constraints."
            ),
        }


@router.get("/api/planner/versions")
def list_plan_versions():
    with get_db() as db:
        rows = db.execute(
            """
            SELECT pv.id, pv.created_at, pv.status, pv.solver_status,
                   pv.runtime_ms,
                   COUNT(sa.id) AS assigned_students,
                   COUNT(ia.id) AS invigilator_assignments
            FROM plan_versions pv
            LEFT JOIN seat_assignments sa ON sa.plan_version = pv.id
            LEFT JOIN invigilator_assignments ia ON ia.plan_version = pv.id
            GROUP BY pv.id
            ORDER BY pv.id DESC
            """
        ).fetchall()

    return {"plans": [dict(row) for row in rows]}


@router.post("/api/planner/{plan_version}/approve")
def approve_plan(plan_version: int):
    with get_db() as db:
        plan = db.execute(
            "SELECT * FROM plan_versions WHERE id = ?", (plan_version,)
        ).fetchone()

        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found.")

        conflicts = db.execute(
            """
            SELECT COUNT(*) FROM conflicts
            WHERE plan_version = ? AND severity = 'Critical'
            """,
            (plan_version,),
        ).fetchone()[0]

        if conflicts > 0:
            raise HTTPException(
                status_code=400,
                detail="Plan cannot be approved because critical conflicts exist.",
            )

        db.execute(
            "UPDATE plan_versions SET status = 'Approved' WHERE id = ?",
            (plan_version,),
        )
        db.execute(
            """
            INSERT INTO audit_events
            (timestamp, username, action, entity, previous_value, new_value, reason, plan_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                "coordinator@examflow.app",
                "Approved plan",
                "Plan",
                plan["status"],
                "Approved",
                "Coordinator approval",
                plan_version,
            ),
        )

    return {"message": "Plan approved."}


@router.post("/api/planner/{plan_version}/publish")
def publish_plan(plan_version: int):
    with get_db() as db:
        plan = db.execute(
            "SELECT * FROM plan_versions WHERE id = ?", (plan_version,)
        ).fetchone()

        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found.")

        if plan["status"] != "Approved":
            raise HTTPException(
                status_code=400,
                detail="Only approved plans can be published.",
            )

        db.execute(
            "UPDATE plan_versions SET status = 'Published' WHERE id = ?",
            (plan_version,),
        )
        db.execute(
            """
            INSERT INTO audit_events
            (timestamp, username, action, entity, previous_value, new_value, reason, plan_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                "coordinator@examflow.app",
                "Published plan",
                "Plan",
                "Approved",
                "Published",
                "Final publication",
                plan_version,
            ),
        )

    return {"message": "Plan published."}