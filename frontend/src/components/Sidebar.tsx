import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/utils/cn'
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  Network,
  Search,
  Settings,
  Brain,
  FlaskConical,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Knowledge Graph', href: '/graph', icon: Network },
  { name: 'Search', href: '/search', icon: Search },
  { name: 'Analysis', href: '/analysis', icon: FlaskConical },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Brain className="h-8 w-8 text-primary" />
        <span className="text-xl font-bold">ScholarMind</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t p-4">
        <div className="flex items-center gap-3 rounded-lg bg-muted px-3 py-2">
          <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-sm font-medium text-primary">SM</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">ScholarMind</p>
            <p className="text-xs text-muted-foreground">v1.0.0</p>
          </div>
        </div>
      </div>
    </div>
  )
}
