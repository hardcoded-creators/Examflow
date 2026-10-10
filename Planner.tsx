import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, PageHeader } from '../components/ui';

export default function Planner() {
  const [plans, setPlans] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState({
    horizontal_separation: true,
    vertical_separation: false,
    diagonal_separation: false,
    invigilators_per_room: 1,
    preserve_existing_assignments: true,
  });

  const load = async () => {
    const data = await api.get<{ plans: any[] }>('/api/planner/versions');
    setPlans(data.plans);
  };

  useEffect(() => {
    load();
  }, []);

  const generate = async () => {
    setLoading(true);
    try {
      const response = await api.post('/api/planner/generate', rules);
      setResult(response);
      load();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const replan = async (basePlanVersion: number) => {
    setLoading(true);
    try {
      const response = await api.post('/api/planner/replan', {
        base_plan_version: basePlanVersion,
        unavailable_room_id: 'ROOM-A',
        rules,
      });
      setResult(response);
      load();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Schedule Planner"
        description="Generate and replan examination seating and invigilator assignments"
      />

      <Card title="Scheduling Rules">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={rules.horizontal_separation}
              onChange={(e) =>
                setRules({ ...rules, horizontal_separation: e.target.checked })
              }
            />
            Prevent same-subject horizontal adjacency
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={rules.vertical_separation}
              onChange={(e) =>
                setRules({ ...rules, vertical_separation: e.target.checked })
              }
            />
            Prevent same-subject vertical adjacency
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={rules.diagonal_separation}
              onChange={(e) =>
                setRules({ ...rules, diagonal_separation: e.target.checked })
              }
            />
            Prevent same-subject diagonal adjacency
          </label>

          <label className="flex items-center gap-2 text-sm">
            Invigilators per room:
            <input
              type="number"
              min={1}
              value={rules.invigilators_per_room}
              onChange={(e) =>
                setRules({
                  ...rules,
                  invigilators_per_room: Number(e.target.value),
                })
              }
              className="w-20 rounded border border-[#E5E7EB] px-2 py-1"
            />
          </label>
        </div>

        <div className="mt-4">
          <Button onClick={generate}>
            {loading ? 'Generating…' : 'Generate Plan'}
          </Button>
        </div>
      </Card>

      {result && (
        <div className="mt-5">
          <Card title="Latest Scheduling Result">
            <p><strong>Status:</strong> {result.solver_status}</p>
            <p><strong>Runtime:</strong> {result.runtime_ms} ms</p>
            <p><strong>Assigned students:</strong> {result.assigned_students}</p>
            <p><strong>Plan version:</strong> {result.plan_version}</p>
            <p className="mt-2 text-sm text-[#667085]">{result.message}</p>
          </Card>
        </div>
      )}

      <div className="mt-5">
        <Card title="Plan Versions">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Version</th>
                  <th>Status</th>
                  <th>Solver</th>
                  <th>Runtime</th>
                  <th>Students</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((plan) => (
                  <tr key={plan.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">#{plan.id}</td>
                    <td>{plan.status}</td>
                    <td>{plan.solver_status}</td>
                    <td>{plan.runtime_ms} ms</td>
                    <td>{plan.assigned_students}</td>
                    <td>
                      <Button variant="secondary" onClick={() => replan(plan.id)}>
                        Simulate Room Failure
                      </Button>
                    </td>
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