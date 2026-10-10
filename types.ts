export interface Student {
  id: string;
  roll: string;
  name: string;
  department: string;
  semester: string;
  email?: string;
  special_needs?: string;
  status: string;
}

export interface Exam {
  id: string;
  subject_code: string;
  subject_name: string;
  exam_date: string;
  start_time: string;
  end_time: string;
  status: string;
  registered_students: number;
}

export interface Room {
  id: string;
  name: string;
  building: string;
  floor: string;
  physical_capacity: number;
  usable_capacity: number;
  seat_rows: number;
  seats_per_row: number;
  status: string;
}

export interface Invigilator {
  id: string;
  name: string;
  department: string;
  max_workload: number;
  status: string;
}

export interface PlanVersion {
  id: number;
  created_at: string;
  status: string;
  solver_status: string;
  runtime_ms: number;
  assigned_students: number;
  invigilator_assignments: number;
}

export interface Conflict {
  id: number;
  severity: string;
  category: string;
  entity: string;
  exam_id?: string;
  description: string;
  rule: string;
  suggestion: string;
  status: string;
}