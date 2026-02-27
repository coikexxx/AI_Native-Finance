import { Outlet, Link, useLocation } from 'react-router-dom'
import clsx from 'clsx'

const navItems = [
  { path: '/', label: '研究 Research', icon: '🔍' },
  { path: '/alerts', label: '提醒 Alerts', icon: '🔔' },
  { path: '/watchlist', label: '自选股 Watchlist', icon: '⭐' },
  { path: '/monitor', label: '监控 Monitor', icon: '📡' },
]

export function AppShell() {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="bg-slate-900 border-b border-slate-800 px-4 h-12 flex items-center gap-6">
        <Link to="/" className="text-sky-400 font-bold text-base tracking-tight flex-shrink-0">
          ⚡ AI Research Copilot
        </Link>
        <nav className="flex items-center gap-1">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'px-3 py-1.5 rounded-md text-sm transition-colors flex items-center gap-1.5',
                pathname === item.path || (item.path !== '/' && pathname.startsWith(item.path))
                  ? 'bg-sky-900/40 text-sky-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800',
              )}
            >
              <span className="text-xs">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto text-xs text-slate-600">
          AI-Native Finance · claude-sonnet-4-6
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 px-4 py-6 max-w-6xl mx-auto w-full">
        <Outlet />
      </main>
    </div>
  )
}
