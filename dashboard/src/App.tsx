import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AnimatePresence, motion } from 'framer-motion'

// Layout
import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'

// Pages
import DashboardOverview from './pages/DashboardOverview'
import NodesPage from './pages/NodesPage'
import PodsPage from './pages/PodsPage'
import ServicesPage from './pages/ServicesPage'
import DeploymentsPage from './pages/DeploymentsPage'
import AlertsPage from './pages/AlertsPage'
import SettingsPage from './pages/SettingsPage'
import KubeconfigSetup from './pages/KubeconfigSetup'

// Context
import { ClusterProvider } from './context/ClusterContext'
import { ThemeProvider } from './context/ThemeContext'

// Types
interface AppLayoutProps {
  children: React.ReactNode
  sidebarCollapsed: boolean
  onToggleSidebar: () => void
  isConnected: boolean
}

function AppLayout({ children, sidebarCollapsed, onToggleSidebar, isConnected }: AppLayoutProps) {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-[#030303]">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={onToggleSidebar}
          isConnected={isConnected}
        />
        <div
          className={`transition-all duration-300 ease-out ${
            sidebarCollapsed ? 'ml-20' : 'ml-64'
          }`}
        >
          <Header sidebarCollapsed={sidebarCollapsed} onToggleSidebar={onToggleSidebar} />
          <main className="p-6 mt-16">
            <AnimatePresence mode="wait">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
        <Toaster
          position="top-right"
          richColors
          duration={4000}
          className="font-sans"
          theme="dark"
        />
      </div>
    </ThemeProvider>
  )
}

// Wrapper component that uses the cluster context
function DashboardRoutes() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const { isConnected } = useCluster()

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev)
  }, [])

  return (
    <AppLayout
      sidebarCollapsed={sidebarCollapsed}
      onToggleSidebar={toggleSidebar}
      isConnected={isConnected}
    >
      <Routes>
        <Route path="/dashboard" element={<DashboardOverview />} />
        <Route path="/nodes" element={<NodesPage />} />
        <Route path="/pods" element={<PodsPage />} />
        <Route path="/services" element={<ServicesPage />} />
        <Route path="/deployments" element={<DeploymentsPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  )
}

// Import useCluster here since it's used in DashboardRoutes
import { useCluster } from './context/ClusterContext'

function App() {
  // Check if kubeconfig is configured
  const [isConfigured, setIsConfigured] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkConfig = async () => {
      try {
        const storedPath = localStorage.getItem('kubeconfig_path')
        if (storedPath) {
          // Try to validate with backend API
          const apiBaseUrl = localStorage.getItem('api_base_url') ||
            import.meta.env.VITE_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiBaseUrl}/api/cluster/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kubeconfig_path: storedPath })
          }).catch(() => null)

          // If API is available and returns valid, set configured
          if (response?.ok) {
            const data = await response.json()
            setIsConfigured(data.valid)
          } else {
            // If API is not available, use stored path as configured
            setIsConfigured(true)
          }
        }
      } catch {
        setIsConfigured(false)
      } finally {
        setIsLoading(false)
      }
    }
    checkConfig()
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#030303] flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <div className="w-16 h-16 border-2 border-[#8EC060] border-t-transparent rounded-full animate-spin" />
          <p className="text-[#8a8a8a] font-medium">Loading K3s Sentinel...</p>
        </motion.div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <ClusterProvider>
        <Routes>
          <Route
            path="/setup"
            element={
              isConfigured ? <Navigate to="/dashboard" replace /> : <KubeconfigSetup />
            }
          />
          <Route
            path="/*"
            element={
              isConfigured ? <DashboardRoutes /> : <Navigate to="/setup" replace />
            }
          />
        </Routes>
      </ClusterProvider>
    </BrowserRouter>
  )
}

export default App
