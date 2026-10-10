import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "examflow.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                roll TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                semester TEXT NOT NULL,
                email TEXT,
                special_needs TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Active'
            );

            CREATE TABLE IF NOT EXISTS subjects (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                semester TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                subject_code TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Scheduled',
                FOREIGN KEY (subject_code) REFERENCES subjects(code)
            );

            CREATE TABLE IF NOT EXISTS registrations (
                student_id TEXT NOT NULL,
                exam_id TEXT NOT NULL,
                PRIMARY KEY (student_id, exam_id),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                building TEXT DEFAULT '',
                floor TEXT DEFAULT '',
                physical_capacity INTEGER NOT NULL,
                usable_capacity INTEGER NOT NULL,
                seat_rows INTEGER NOT NULL,
                seats_per_row INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS room_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                block_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                reason TEXT DEFAULT '',
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS invigilators (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT DEFAULT '',
                email TEXT DEFAULT '',
                max_workload INTEGER NOT NULL DEFAULT 5,
                status TEXT NOT NULL DEFAULT 'Active'
            );

            CREATE TABLE IF NOT EXISTS staff_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invigilator_id TEXT NOT NULL,
                available_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                FOREIGN KEY (invigilator_id)
                    REFERENCES invigilators(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS staff_unavailability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invigilator_id TEXT NOT NULL,
                unavailable_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                reason TEXT DEFAULT '',
                FOREIGN KEY (invigilator_id)
                    REFERENCES invigilators(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS plan_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Draft',
                solver_status TEXT NOT NULL,
                runtime_ms INTEGER NOT NULL,
                rules TEXT NOT NULL,
                snapshot TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS seat_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_version INTEGER NOT NULL,
                exam_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                seat_row INTEGER NOT NULL,
                seat_col INTEGER NOT NULL,
                seat_label TEXT NOT NULL,
                UNIQUE(plan_version, student_id, exam_id),
                UNIQUE(plan_version, room_id, seat_row, seat_col),
                FOREIGN KEY (plan_version)
                    REFERENCES plan_versions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS invigilator_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_version INTEGER NOT NULL,
                exam_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                invigilator_id TEXT NOT NULL,
                UNIQUE(plan_version, exam_id, room_id),
                UNIQUE(plan_version, exam_id, invigilator_id),
                FOREIGN KEY (plan_version)
                    REFERENCES plan_versions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_version INTEGER NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                entity TEXT NOT NULL,
                exam_id TEXT,
                description TEXT NOT NULL,
                rule TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                FOREIGN KEY (plan_version)
                    REFERENCES plan_versions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                previous_value TEXT DEFAULT '',
                new_value TEXT DEFAULT '',
                reason TEXT DEFAULT '',
                plan_version INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_registrations_exam
                ON registrations(exam_id);
            CREATE INDEX IF NOT EXISTS idx_assignments_plan
                ON seat_assignments(plan_version);
            CREATE INDEX IF NOT EXISTS idx_inv_assignments_plan
                ON invigilator_assignments(plan_version);
            """
        )