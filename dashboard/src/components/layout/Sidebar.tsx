import { NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Server,
  Box,
  Network,
  Layers,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  X
} from 'lucide-react'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  isConnected: boolean
}

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { path: '/nodes', icon: Server, label: 'Nodes' },
  { path: '/pods', icon: Box, label: 'Pods' },
  { path: '/services', icon: Network, label: 'Services' },
  { path: '/deployments', icon: Layers, label: 'Deployments' },
  { path: '/alerts', icon: Bell, label: 'Alerts', badge: 3 },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar({ collapsed, onToggle, isConnected }: SidebarProps) {
  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 256 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 h-screen bg-[#0a0a0a]/80 backdrop-blur-xl border-r border-[#2a2a2a] z-50"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#2a2a2a]">
        <motion.div
          initial={false}
          animate={{ opacity: collapsed ? 0 : 1 }}
          className="flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#8EC060] to-[#435E2A] flex items-center justify-center shadow-lg shadow-[#8EC060]/20">
            <Zap className="w-6 h-6 text-white" />
          </div>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="font-bold text-lg text-[#FAFAFA]"
            >
              Sentinel
            </motion.span>
          )}
        </motion.div>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg bg-[#1a1a1a] hover:bg-[#2a2a2a] text-[#8a8a8a] hover:text-white transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Connection Status */}
      <div className={`px-4 py-3 ${collapsed ? 'hidden' : ''}`}>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1a1a1a]">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#8EC060] animate-pulse' : 'bg-[#F95106]'}`} />
          <span className="text-xs text-[#8a8a8a]">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative ${
                isActive
                  ? 'bg-gradient-to-r from-[#8EC060]/10 to-[#435E2A]/10 text-[#8EC060]'
                  : 'text-[#8a8a8a] hover:text-white hover:bg-[#1a1a1a]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute inset-0 bg-gradient-to-r from-[#8EC060]/10 to-[#435E2A]/10 rounded-xl border border-[#8EC060]/20"
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}
                <item.icon className={`w-5 h-5 relative z-10 ${isActive ? 'text-[#8EC060]' : ''}`} />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="font-medium text-sm relative z-10"
                  >
                    {item.label}
                  </motion.span>
                )}
                {!collapsed && item.badge && (
                  <span className="ml-auto px-2 py-0.5 text-xs font-medium bg-[#F95106]/20 text-[#F95106] rounded-full">
                    {item.badge}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Collapse indicator */}
      {collapsed && (
        <div className="absolute bottom-4 left-0 right-0 flex justify-center">
          <button
            onClick={onToggle}
            className="p-2 rounded-lg bg-[#1a1a1a] hover:bg-[#2a2a2a] text-[#8a8a8a] hover:text-white transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </motion.aside>
  )
}
