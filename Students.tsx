import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, Input, PageHeader } from '../components/ui';

export default function Students() {
  const [students, setStudents] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [form, setForm] = useState({
    roll: '', name: '', department: '', semester: '', email: '',
  });
  const [message, setMessage] = useState('');

  const load = async () => {
    const result = await api.get<{ students: any[] }>(
      `/api/students?search=${encodeURIComponent(search)}`
    );
    setStudents(result.students);
  };

  useEffect(() => {
    load();
  }, [search]);

  const addStudent = async () => {
    try {
      await api.post('/api/students', form);
      setMessage('Student added.');
      setForm({ roll: '', name: '', department: '', semester: '', email: '' });
      load();
    } catch (err: any) {
      setMessage(err.message);
    }
  };

  return (
    <div>
      <PageHeader title="Students" description="Manage examination registrations" />

      {message && <p className="mb-4 text-sm text-blue-700">{message}</p>}

      <Card title="Add Student">
        <div className="grid gap-3 md:grid-cols-5">
          <Input value={form.roll} onChange={(v) => setForm({ ...form, roll: v })} placeholder="Roll number" />
          <Input value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="Full name" />
          <Input value={form.department} onChange={(v) => setForm({ ...form, department: v })} placeholder="Department" />
          <Input value={form.semester} onChange={(v) => setForm({ ...form, semester: v })} placeholder="Semester" />
          <Button onClick={addStudent}>Add</Button>
        </div>
      </Card>

      <div className="mt-5">
        <Card
          title="Student Records"
          actions={<Input value={search} onChange={setSearch} placeholder="Search name or roll" />}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Roll</th>
                  <th>Name</th>
                  <th>Department</th>
                  <th>Semester</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">{student.roll}</td>
                    <td>{student.name}</td>
                    <td>{student.department}</td>
                    <td>{student.semester}</td>
                    <td>{student.status}</td>
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