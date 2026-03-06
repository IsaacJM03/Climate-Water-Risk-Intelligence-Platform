import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  MapPin,
  Bell,
  Activity,
  LogOut,
  CloudRain,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/regions', label: 'Regions', icon: MapPin },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/readings', label: 'Readings', icon: Activity },
]

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-primary-900 text-white flex flex-col">
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-primary-700">
          <CloudRain className="w-6 h-6 text-primary-300" />
          <span className="font-bold text-sm leading-tight">
            Climate Risk<br />
            <span className="text-primary-300 font-normal text-xs">Intelligence Platform</span>
          </span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-700 text-white font-medium'
                    : 'text-primary-200 hover:bg-primary-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-primary-700 text-xs text-primary-300">
          <p className="truncate">{user?.userId ?? 'Unknown'}</p>
          <p className="mt-0.5 capitalize">{user?.role ?? ''}</p>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
          <h1 className="text-base font-semibold text-gray-800">
            Climate &amp; Water Risk Intelligence
          </h1>
          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-gray-600">
                Org&nbsp;
                <span className="font-medium text-primary-700">#{user.orgId}</span>
                &nbsp;·&nbsp;
                <span className="capitalize bg-primary-50 text-primary-700 text-xs px-2 py-0.5 rounded-full font-medium">
                  {user.role}
                </span>
              </span>
            )}
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
