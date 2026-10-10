import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, PageHeader } from '../components/ui';

export default function Reports() {
  const [plans, setPlans] = useState<any[]>([]);
  const [planVersion, setPlanVersion] = useState('');

  useEffect(() => {
    api.get<{ plans: any[] }>('/api/planner/versions').then((data) =>
      setPlans(data.plans)
    );
  }, []);

  return (
    <div>
      <PageHeader title="Reports & Exports" description="Download plans and operational reports" />

      <Card title="Select Plan">
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
      </Card>

      <div className="mt-5">
        <Card title="Available Reports">
          <div className="flex flex-wrap gap-3">
            <a href={`http://localhost:8000/api/reports/invigilator-roster?plan_version=${planVersion}`}>
              <Button variant="secondary">Invigilator Roster CSV</Button>
            </a>
            <a href={`http://localhost:8000/api/students/export`}>
              <Button variant="secondary">Students CSV</Button>
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
}