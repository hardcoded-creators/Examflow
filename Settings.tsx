import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, PageHeader } from '../components/ui';

export default function Settings() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    api.get('/api/health').then(setStatus);
  }, []);

  const loadDemo = async () => {
    await api.post('/api/demo/load');
    alert('Demo data loaded.');
  };

  return (
    <div>
      <PageHeader title="Settings" description="Application and demonstration settings" />

      <Card title="System Status">
        {status && (
          <div className="space-y-2 text-sm">
            <p><strong>Backend:</strong> {status.status}</p>
            <p><strong>Database:</strong> SQLite</p>
            <p><strong>Scheduling engine:</strong> Deterministic constraint engine</p>
          </div>
        )}
      </Card>

      <div className="mt-5">
        <Card title="Demonstration Data">
          <p className="mb-3 text-sm text-[#667085]">
            Loads 120 students, 5 examinations, 4 rooms, and 6 invigilators.
          </p>
          <Button onClick={loadDemo}>Load Demo Data</Button>
        </Card>
      </div>
    </div>
  );
}