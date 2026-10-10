import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, PageHeader } from '../components/ui';

export default function Seating() {
  const [exams, setExams] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [planVersion, setPlanVersion] = useState('');
  const [examId, setExamId] = useState('');
  const [seating, setSeating] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      api.get<{ exams: any[] }>('/api/exams'),
      api.get<{ plans: any[] }>('/api/planner/versions'),
    ]).then(([examData, planData]) => {
      setExams(examData.exams);
      setPlans(planData.plans);
    });
  }, []);

  const loadSeating = async () => {
    try {
      const result = await api.get<{ seating: any[] }>(
        `/api/seating?plan_version=${planVersion}&exam_id=${examId}`
      );
      setSeating(result.seating);
    } catch {
      setSeating([]);
    }
  };

  return (
    <div>
      <PageHeader title="Seating Arrangements" description="Interactive room-wise seating" />

      <Card title="Select Plan and Examination">
        <div className="flex flex-wrap gap-3">
          <select
            className="rounded-md border border-[#E5E7EB] px-3 py-2 text-sm"
            value={planVersion}
            onChange={(e) => setPlanVersion(e.target.value)}
          >
            <option value="">Select plan</option>
            {plans.map((plan) => (
              <option key={plan.id} value={plan.id}>
                Plan #{plan.id}
              </option>
            ))}
          </select>

          <select
            className="rounded-md border border-[#E5E7EB] px-3 py-2 text-sm"
            value={examId}
            onChange={(e) => setExamId(e.target.value)}
          >
            <option value="">Select examination</option>
            {exams.map((exam) => (
              <option key={exam.id} value={exam.id}>
                {exam.subject_code}
              </option>
            ))}
          </select>

          <Button onClick={loadSeating}>Load Seating</Button>

          <a
            href={`http://localhost:8000/api/seating/export?plan_version=${planVersion}&exam_id=${examId}`}
          >
            <Button variant="secondary">Export CSV</Button>
          </a>
        </div>
      </Card>

      <div className="mt-5">
        <Card title="Seating Grid">
          {!seating.length && <p className="text-sm text-[#667085]">No seating loaded.</p>}

          <div className="overflow-x-auto">
            <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(10, minmax(70px, 1fr))' }}>
              {seating.map((seat) => (
                <div
                  key={`${seat.room_id}-${seat.seat_row}-${seat.seat_col}`}
                  className="rounded-md border border-[#E5E7EB] bg-green-50 p-2 text-center text-xs"
                  title={`${seat.student_name} — ${seat.roll}`}
                >
                  <p className="font-medium">{seat.roll}</p>
                  <p className="text-[#667085]">{seat.seat_label}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}