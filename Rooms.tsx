import { useEffect, useState } from 'react';
import { api } from '../api';
import { Button, Card, Input, PageHeader } from '../components/ui';

export default function Rooms() {
  const [rooms, setRooms] = useState<any[]>([]);
  const [form, setForm] = useState({
    name: '', building: '', floor: '', physical_capacity: '',
    usable_capacity: '', seat_rows: '', seats_per_row: '',
  });

  const load = async () => {
    const result = await api.get<{ rooms: any[] }>('/api/rooms');
    setRooms(result.rooms);
  };

  useEffect(() => {
    load();
  }, []);

  const addRoom = async () => {
    try {
      await api.post('/api/rooms', {
        ...form,
        physical_capacity: Number(form.physical_capacity),
        usable_capacity: Number(form.usable_capacity),
        seat_rows: Number(form.seat_rows),
        seats_per_row: Number(form.seats_per_row),
      });
      setForm({
        name: '', building: '', floor: '', physical_capacity: '',
        usable_capacity: '', seat_rows: '', seats_per_row: '',
      });
      load();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const toggleStatus = async (room: any) => {
    const status = room.status === 'Available' ? 'Unavailable' : 'Available';
    await api.put(`/api/rooms/${room.id}/status?status=${status}`, {});
    load();
  };

  return (
    <div>
      <PageHeader title="Rooms & Halls" description="Manage examination venues" />

      <Card title="Add Room">
        <div className="grid gap-3 md:grid-cols-4">
          <Input value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="Room name" />
          <Input value={form.building} onChange={(v) => setForm({ ...form, building: v })} placeholder="Building" />
          <Input type="number" value={form.physical_capacity} onChange={(v) => setForm({ ...form, physical_capacity: v })} placeholder="Physical capacity" />
          <Input type="number" value={form.usable_capacity} onChange={(v) => setForm({ ...form, usable_capacity: v })} placeholder="Usable capacity" />
          <Input type="number" value={form.seat_rows} onChange={(v) => setForm({ ...form, seat_rows: v })} placeholder="Rows" />
          <Input type="number" value={form.seats_per_row} onChange={(v) => setForm({ ...form, seats_per_row: v })} placeholder="Seats per row" />
          <Button onClick={addRoom}>Add Room</Button>
        </div>
      </Card>

      <div className="mt-5">
        <Card title="Room Inventory">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[#667085]">
                  <th className="py-2">Room</th>
                  <th>Building</th>
                  <th>Usable Seats</th>
                  <th>Grid</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {rooms.map((room) => (
                  <tr key={room.id} className="border-t border-[#E5E7EB]">
                    <td className="py-2">{room.name}</td>
                    <td>{room.building}</td>
                    <td>{room.usable_capacity}</td>
                    <td>{room.seat_rows} × {room.seats_per_row}</td>
                    <td>{room.status}</td>
                    <td>
                      <Button variant="secondary" onClick={() => toggleStatus(room)}>
                        Toggle
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