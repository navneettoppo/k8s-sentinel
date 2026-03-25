import { Search, Bell, RefreshCw, User, Settings, LogOut, ChevronDown } from 'lucide-react'
import { useCluster } from '../../context/ClusterContext'
import { useTheme } from '../../context/ThemeContext'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface HeaderProps {
  sidebarCollapsed: boolean
  onToggleSidebar?: () => void
}

export default function Header({ sidebarCollapsed }: HeaderProps) {
  const { clusterInfo, isConnected, refreshData, disconnect, kubeconfigPath } = useCluster()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refreshData()
    setTimeout(() => setIsRefreshing(false), 500)
  }

  const handleDisconnect = () => {
    disconnect()
    localStorage.removeItem('kubeconfig_path')
    navigate('/setup')
    setShowUserMenu(false)
  }

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`fixed top-0 right-0 h-16 bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-[#2a2a2a] z-40 transition-all duration-300 ${
        sidebarCollapsed ? 'left-16' : 'left-64'
      }`}
    >
      <div className="h-full px-6 flex items-center justify-between">
        {/* Search */}
        <div className="flex-1 max-w-md">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6a6a6a] group-focus-within:text-[#8EC060] transition-colors" />
            <input
              type="text"
              placeholder="Search resources, pods, nodes..."
              className="w-full pl-10 pr-4 py-2.5 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl text-sm text-[#FAFAFA] placeholder-[#5a5a5a] focus:outline-none focus:border-[#8EC060]/50 focus:ring-2 focus:ring-[#8EC060]/20 transition-all"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          {/* Refresh Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleRefresh}
            disabled={isRefreshing || !isConnected}
            className={`p-2.5 rounded-xl transition-all ${
              isConnected
                ? 'bg-[#1a1a1a] hover:bg-[#2a2a2a] text-[#8a8a8a] hover:text-white'
                : 'bg-[#1a1a1a]/50 text-[#5a5a5a] cursor-not-allowed'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </motion.button>

          {/* Theme Toggle */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleTheme}
            className="p-2.5 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-xl text-[#8a8a8a] hover:text-white transition-all"
          >
            {theme === 'dark' ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </motion.button>

          {/* Notifications */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative p-2.5 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-xl text-[#8a8a8a] hover:text-white transition-all"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#F95106] rounded-full animate-pulse" />
          </motion.button>

          {/* User Menu */}
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 px-3 py-2 bg-[#1a1a1a] hover:bg-[#2a2a2a] rounded-xl transition-all"
            >
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#8EC060] to-[#435E2A] flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-[#FAFAFA] font-medium hidden sm:block">
                {clusterInfo?.name || 'Not Connected'}
              </span>
              <ChevronDown className="w-3 h-3 text-[#8a8a8a]" />
            </motion.button>

            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 mt-2 w-56 bg-[#0a0a0a]/90 backdrop-blur-xl border border-[#2a2a2a] rounded-xl shadow-xl shadow-black/20 overflow-hidden"
                >
                  <div className="p-3 border-b border-[#2a2a2a]">
                    <p className="text-sm text-[#FAFAFA] font-medium">Cluster Admin</p>
                    <p className="text-xs text-[#6a6a6a] mt-0.5">
                      {isConnected ? clusterInfo?.version || 'Connected' : 'Not connected'}
                    </p>
                    <p className="text-xs text-[#5a5a5a] mt-1 truncate" title={kubeconfigPath}>
                      Path: {kubeconfigPath || 'N/A'}
                    </p>
                  </div>
                  <div className="p-1">
                    <button
                      onClick={() => { navigate('/settings'); setShowUserMenu(false) }}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[#8a8a8a] hover:text-white hover:bg-[#1a1a1a] rounded-lg transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </button>
                    <button
                      onClick={handleDisconnect}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-[#F95106] hover:text-[#F95106]/80 hover:bg-[#F95106]/10 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Disconnect
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.header>
  )
}
