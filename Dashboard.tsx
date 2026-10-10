import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { Card, PageHeader, Badge, Button } from '../components/ui';

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setError('');
      setData(await api.get('/api/dashboard'));
    } catch (err: any) {
      setError(err.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return <p>Loading dashboard…</p>;

  const metrics = data.metrics;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Live examination-planning overview"
        actions={<Button onClick={load}>Refresh</Button>}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ['Registered Students', metrics.total_students],
          ['Scheduled Examinations', metrics.scheduled_examinations],
          ['Available Rooms', metrics.available_rooms],
          ['Available Invigilators', metrics.available_invigilators],
          ['Unassigned Students', metrics.unassigned_students],
          ['Active Conflicts', metrics.active_conflicts],
          ['Plan Completion', `${metrics.plan_completion_percent}%`],
          ['Latest Plan', metrics.latest_plan_status],
        ].map(([label, value]) => (
          <Card key={label as string}>
            <p className="text-sm text-[#667085]">{label}</p>
            <p className="mt-2 text-2xl font-semibold">{value}</p>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Card title="Upcoming Examinations">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Subject</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Students</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.upcoming_examinations.map((exam: any) => (
                  <tr key={exam.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">{exam.subject_code}</td>
                    <td>{exam.exam_date}</td>
                    <td>{exam.start_time}</td>
                    <td>{exam.registered_students}</td>
                    <td><Badge text={exam.status} tone="blue" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Room Utilization">
          {data.room_utilization.map((room: any) => (
            <div key={room.room} className="mb-3">
              <div className="flex justify-between text-sm">
                <span>{room.room}</span>
                <span>{room.utilization}%</span>
              </div>
              <div className="mt-1 h-2 rounded bg-gray-100">
                <div
                  className="h-2 rounded bg-[#2563EB]"
                  style={{ width: `${Math.min(room.utilization, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Quick Actions">
          <div className="flex flex-wrap gap-3">
            <Link to="/students"><Button variant="secondary">Add Students</Button></Link>
            <Link to="/examinations"><Button variant="secondary">Create Examination</Button></Link>
            <Link to="/rooms"><Button variant="secondary">Add Room</Button></Link>
            <Link to="/invigilators"><Button variant="secondary">Add Invigilator</Button></Link>
            <Link to="/planner"><Button>Generate Plan</Button></Link>
          </div>
        </Card>
      </div>
    </div>
  );
}