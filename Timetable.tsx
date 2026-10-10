import { useEffect, useState } from 'react';
import { api } from '../api';
import { Card, PageHeader } from '../components/ui';

export default function Timetable() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get('/api/timetable').then(setData);
  }, []);

  if (!data) return <p>Loading timetable…</p>;

  return (
    <div>
      <PageHeader title="Timetable" description="Examination schedule overview" />

      <Card title="Examination Timetable">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[#667085]">
                <th className="py-2">Subject</th>
                <th>Date</th>
                <th>Time</th>
                <th>Students</th>
                <th>Rooms</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.timetable.map((exam: any) => (
                <tr key={exam.id} className="border-t border-[#E5E7EB]">
                  <td className="py-2">{exam.subject_code} — {exam.subject_name}</td>
                  <td>{exam.exam_date}</td>
                  <td>{exam.start_time}–{exam.end_time}</td>
                  <td>{exam.registered_students}</td>
                  <td>{exam.assigned_rooms}</td>
                  <td>{exam.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}