from pydantic import BaseModel
from typing import Optional, Literal


class StudentIn(BaseModel):
    roll: str
    name: str
    department: str
    semester: str
    email: Optional[str] = ""
    special_needs: str = ""
    status: str = "Active"


class SubjectIn(BaseModel):
    code: str
    name: str
    department: str
    semester: str


class ExamIn(BaseModel):
    subject_code: str
    exam_date: str
    start_time: str
    end_time: str
    status: str = "Scheduled"


class RegistrationIn(BaseModel):
    student_id: str
    exam_id: str


class RoomIn(BaseModel):
    name: str
    building: str = ""
    floor: str = ""
    physical_capacity: int
    usable_capacity: int
    seat_rows: int
    seats_per_row: int
    status: str = "Available"
    notes: str = ""


class RoomBlockIn(BaseModel):
    room_id: str
    block_date: str
    start_time: str
    end_time: str
    reason: str = ""


class InvigilatorIn(BaseModel):
    name: str
    department: str = ""
    email: str = ""
    max_workload: int = 5
    status: str = "Active"


class AvailabilityIn(BaseModel):
    invigilator_id: str
    available_date: str
    start_time: str
    end_time: str


class UnavailabilityIn(BaseModel):
    invigilator_id: str
    unavailable_date: str
    start_time: str
    end_time: str
    reason: str = ""


class ScheduleRules(BaseModel):
    horizontal_separation: bool = True
    vertical_separation: bool = False
    diagonal_separation: bool = False
    invigilators_per_room: int = 1
    preserve_existing_assignments: bool = True


class ReplanRequest(BaseModel):
    base_plan_version: int
    unavailable_room_id: Optional[str] = None
    unavailable_invigilator_id: Optional[str] = None
    rules: ScheduleRules