import { ReactNode, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  BarChart3, Calendar, ClipboardList, DoorOpen, FileText, LayoutDashboard,
  Users, UserCheck, Grid3X3, AlertTriangle, Settings, History, Menu, X,
} from 'lucide-react';

const navigation = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/students', label: 'Students', icon: Users },
  { to: '/examinations', label: 'Examinations', icon: ClipboardList },
  { to: '/rooms', label: 'Rooms & Halls', icon: DoorOpen },
  { to: '/invigilators', label: 'Invigilators', icon: UserCheck },
  { to: '/planner', label: 'Schedule Planner', icon: Calendar },
  { to: '/seating', label: 'Seating Arrangements', icon: Grid3X3 },
  { to: '/conflicts', label: 'Conflicts & Alerts', icon: AlertTriangle },
  { to: '/timetable', label: 'Timetable', icon: Calendar },
  { to: '/reports', label: 'Reports & Exports', icon: FileText },
  { to: '/audit', label: 'Audit History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-60 transform bg-[#172B4D] text-white transition-transform md:static md:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-5">
          <div>
            <p className="text-lg font-bold">ExamFlow</p>
            <p className="text-xs text-gray-300">Intelligent Exam Planner</p>
          </div>
          <button className="md:hidden" onClick={() => setOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="space-y-1 px-3">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
                  isActive
                    ? 'bg-[#2563EB] text-white'
                    : 'text-gray-300 hover:bg-white/10'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-4 left-4 right-4 text-xs text-gray-400">
          2392608303-Avengers
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-[#E5E7EB] bg-white px-5 py-3">
          <button className="md:hidden" onClick={() => setOpen(true)}>
            <Menu size={22} />
          </button>
          <div className="hidden md:block">
            <p className="text-sm font-medium">Examination Operations</p>
            <p className="text-xs text-[#667085]">ExamFlow Workspace</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-[#172B4D] px-3 py-1 text-xs text-white">
              Coordinator
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-x-hidden p-5">{children}</main>
      </div>
    </div>
  );
}