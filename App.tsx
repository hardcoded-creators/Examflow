import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Students from './pages/Students';
import Examinations from './pages/Examinations';
import Rooms from './pages/Rooms';
import Invigilators from './pages/Invigilators';
import Planner from './pages/Planner';
import Seating from './pages/Seating';
import Conflicts from './pages/Conflicts';
import Timetable from './pages/Timetable';
import Reports from './pages/Reports';
import Audit from './pages/Audit';
import Settings from './pages/Settings';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/students" element={<Students />} />
        <Route path="/examinations" element={<Examinations />} />
        <Route path="/rooms" element={<Rooms />} />
        <Route path="/invigilators" element={<Invigilators />} />
        <Route path="/planner" element={<Planner />} />
        <Route path="/seating" element={<Seating />} />
        <Route path="/conflicts" element={<Conflicts />} />
        <Route path="/timetable" element={<Timetable />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}