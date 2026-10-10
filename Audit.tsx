import { useEffect, useState } from 'react';
import { api } from '../api';
import { Card, PageHeader } from '../components/ui';

export default function Audit() {
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    api.get<{ events: any[] }>('/api/audit').then((data) =>
      setEvents(data.events)
    );
  }, []);

  return (
    <div>
      <PageHeader title="Audit History" description="Chronological scheduling activity" />

      <Card title="Recent Events">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[#667085]">
                <th className="py-2">Time</th>
                <th>User</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-t border-[#E5E7EB]">
                  <td className="py-2">{event.timestamp}</td>
                  <td>{event.username}</td>
                  <td>{event.action}</td>
                  <td>{event.entity}</td>
                  <td>{event.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}