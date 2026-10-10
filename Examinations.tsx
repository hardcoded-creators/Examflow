import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, Input, PageHeader } from '../components/ui';

export default function Examinations() {
  const [exams, setExams] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [form, setForm] = useState({
    subject_code: '', exam_date: '', start_time: '', end_time: '',
  });

  const load = async () => {
    const examData = await api.get<{ exams: any[] }>('/api/exams');
    const subjectData = await api.get<{ subjects: any[] }>('/api/subjects');
    setExams(examData.exams);
    setSubjects(subjectData.subjects);
  };

  useEffect(() => {
    load();
  }, []);

  const createExam = async () => {
    try {
      await api.post('/api/exams', form);
      setForm({ subject_code: '', exam_date: '', start_time: '', end_time: '' });
      load();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div>
      <PageHeader title="Examinations" description="Manage examination sessions" />

      <Card title="Create Examination">
        <div className="grid gap-3 md:grid-cols-5">
          <select
            className="rounded-md border border-[#E5E7EB] px-3 py-2 text-sm"
            value={form.subject_code}
            onChange={(e) => setForm({ ...form, subject_code: e.target.value })}
          >
            <option value="">Select subject</option>
            {subjects.map((subject) => (
              <option key={subject.code} value={subject.code}>
                {subject.code} — {subject.name}
              </option>
            ))}
          </select>

          <Input type="date" value={form.exam_date}
            onChange={(v) => setForm({ ...form, exam_date: v })} />
          <Input type="time" value={form.start_time}
            onChange={(v) => setForm({ ...form, start_time: v })} />
          <Input type="time" value={form.end_time}
            onChange={(v) => setForm({ ...form, end_time: v })} />
          <Button onClick={createExam}>Create</Button>
        </div>
      </Card>

      <div className="mt-5">
        <Card title="Examination Sessions">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Exam</th>
                  <th>Subject</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Students</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {exams.map((exam) => (
                  <tr key={exam.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">{exam.id}</td>
                    <td>{exam.subject_code}</td>
                    <td>{exam.exam_date}</td>
                    <td>{exam.start_time}–{exam.end_time}</td>
                    <td>{exam.registered_students}</td>
                    <td>{exam.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}