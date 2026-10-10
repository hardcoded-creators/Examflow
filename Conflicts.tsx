import { useEffect, useState } from 'react';
import { api } from '../api';
import { Badge, Card, PageHeader } from '../components/ui';

export default function Conflicts() {
  const [plans, setPlans] = useState<any[]>([]);
  const [planVersion, setPlanVersion] = useState('');
  const [conflicts, setConflicts] = useState<any[]>([]);

  useEffect(() => {
    api.get<{ plans: any[] }>('/api/planner/versions').then((data) =>
      setPlans(data.plans)
    );
  }, []);

  const load = async () => {
    const result = await api.get<{ conflicts: any[] }>(
      `/api/conflicts?plan_version=${planVersion}`
    );
    setConflicts(result.conflicts);
  };

  return (
    <div>
      <PageHeader title="Conflicts & Alerts" description="Constraint violations and explanations" />

      <Card title="Select Plan">
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
          <button
            className="rounded-md bg-[#2563EB] px-4 py-2 text-sm text-white"
            onClick={load}
          >
            Load Conflicts
          </button>
        </div>
      </Card>

      <div className="mt-5">
        <Card title="Conflict Report">
          {!conflicts.length && (
            <p className="text-sm text-[#667085]">No conflicts loaded.</p>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Severity</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Rule</th>
                  <th>Suggested Fix</th>
                </tr>
              </thead>
              <tbody>
                {conflicts.map((conflict) => (
                  <tr key={conflict.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">
                      <Badge
                        text={conflict.severity}
                        tone={conflict.severity === 'Critical' ? 'red' : 'amber'}
                      />
                    </td>
                    <td>{conflict.category}</td>
                    <td>{conflict.description}</td>
                    <td>{conflict.rule}</td>
                    <td>{conflict.suggestion}</td>
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