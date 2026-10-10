import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, Input, PageHeader } from '../components/ui';

export default function Invigilators() {
  const [staff, setStaff] = useState<any[]>([]);
  const [form, setForm] = useState({
    name: '', department: '', email: '', max_workload: '3',
  });

  const load = async () => {
    const result = await api.get<{ invigilators: any[] }>('/api/invigilators');
    setStaff(result.invigilators);
  };

  useEffect(() => {
    load();
  }, []);

  const addStaff = async () => {
    await api.post('/api/invigilators', {
      ...form,
      max_workload: Number(form.max_workload),
    });
    setForm({ name: '', department: '', email: '', max_workload: '3' });
    load();
  };

  return (
    <div>
      <PageHeader title="Invigilators" description="Manage staff availability and duties" />

      <Card title="Add Invigilator">
        <div className="grid gap-3 md:grid-cols-4">
          <Input value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="Full name" />
          <Input value={form.department} onChange={(v) => setForm({ ...form, department: v })} placeholder="Department" />
          <Input value={form.email} onChange={(v) => setForm({ ...form, email: v })} placeholder="Email" />
          <Input type="number" value={form.max_workload} onChange={(v) => setForm({ ...form, max_workload: v })} placeholder="Max duties" />
          <Button onClick={addStaff}>Add</Button>
        </div>
      </Card>

      <div className="mt-5">
        <Card title="Invigilator List">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Name</th>
                  <th>Department</th>
                  <th>Max Workload</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {staff.map((person) => (
                  <tr key={person.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">{person.name}</td>
                    <td>{person.department}</td>
                    <td>{person.max_workload}</td>
                    <td>{person.status}</td>
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