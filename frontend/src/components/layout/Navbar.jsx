import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, BookOpen, Link2 } from 'lucide-react'
import AccountSelector from './AccountSelector'
import { cn } from '@/lib/utils'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/strategies', label: 'Strategies', icon: TrendingUp },
  { path: '/journal', label: 'Journal', icon: BookOpen },
]

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="border-b border-dashboard-border bg-dashboard-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">AlphaDash</span>
          </Link>

          {/* Account Selector */}
          <AccountSelector />

          {/* Navigation */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "text-muted-foreground hover:text-white hover:bg-white/5"
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}

            {/* Connect MT5 Button */}
            <Link
              to="/connect"
              className={cn(
                "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ml-4 border border-emerald-500/30",
                location.pathname === '/connect'
                  ? "bg-emerald-500 text-white"
                  : "text-emerald-400 hover:bg-emerald-500/10"
              )}
            >
              <Link2 className="w-4 h-4" />
              <span>Connect MT5</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}