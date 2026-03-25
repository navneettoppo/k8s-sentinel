import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Bell,
  Search,
  Filter,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  Info,
  Clock,
  Eye,
  Trash2,
  Settings,
  ChevronRight,
  Zap,
  Bug,
  Database,
  Cpu
} from 'lucide-react'

const mockAlerts = [
  {
    id: 1,
    title: 'High CPU Usage',
    description: 'Node k3s-master-01 CPU usage exceeded 90% threshold',
    severity: 'critical',
    source: 'Node',
    sourceName: 'k3s-master-01',
    timestamp: '2 min ago',
    acknowledged: false,
    rca: 'Multiple pods competing for CPU resources. Consider scaling horizontally or optimizing workloads.'
  },
  {
    id: 2,
    title: 'Pod CrashLoopBackOff',
    description: 'Pod backend-api-7d9f8b6c-x2z4k is in CrashLoopBackOff state',
    severity: 'warning',
    source: 'Pod',
    sourceName: 'backend-api-7d9f8b6c-x2z4k',
    timestamp: '15 min ago',
    acknowledged: false,
    rca: 'Application crash due to memory limit exceeded. Review application logs and increase memory allocation.'
  },
  {
    id: 3,
    title: 'Disk Pressure Warning',
    description: 'Node k3s-worker-02 disk usage at 85%',
    severity: 'warning',
    source: 'Node',
    sourceName: 'k3s-worker-02',
    timestamp: '1 hour ago',
    acknowledged: true,
    rca: 'Disk filling up due to log accumulation. Consider cleaning old logs or expanding disk capacity.'
  },
  {
    id: 4,
    title: 'Service Unavailable',
    description: 'Service frontend-web has no ready pods',
    severity: 'critical',
    source: 'Service',
    sourceName: 'frontend-web',
    timestamp: '30 min ago',
    acknowledged: false,
    rca: 'All backend pods are down. Check deployment status and recent pod events for root cause.'
  },
  {
    id: 5,
    title: 'Memory Limit Approaching',
    description: 'Pod postgres-0 memory usage at 92% of limit',
    severity: 'info',
    source: 'Pod',
    sourceName: 'postgres-0',
    timestamp: '2 hours ago',
    acknowledged: true,
    rca: 'Memory usage approaching limit. Monitor closely and plan for capacity increase.'
  },
  {
    id: 6,
    title: 'Deployment Scale Up',
    description: 'backend-api deployment scaled from 3 to 5 replicas',
    severity: 'info',
    source: 'Deployment',
    sourceName: 'backend-api',
    timestamp: '3 hours ago',
    acknowledged: true,
    rca: 'Manual scale operation by admin. Auto-scaling rules may need adjustment.'
  },
]

const severityConfig: Record<string, { bg: string; text: string; border: string; icon: any }> = {
  critical: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30', icon: XCircle },
  warning: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30', icon: AlertTriangle },
  info: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30', icon: Info },
}

const sourceIcon: Record<string, any> = {
  Node: Cpu,
  Pod: Database,
  Service: Zap,
  Deployment: Bug,
}

export default function AlertsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [selectedAlert, setSelectedAlert] = useState<typeof mockAlerts[0] | null>(null)

  const filteredAlerts = mockAlerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         alert.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter
    return matchesSearch && matchesSeverity
  })

  const alertCounts = {
    critical: mockAlerts.filter(a => a.severity === 'critical' && !a.acknowledged).length,
    warning: mockAlerts.filter(a => a.severity === 'warning' && !a.acknowledged).length,
    info: mockAlerts.filter(a => a.severity === 'info').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-slate-400 text-sm mt-1">K3s Sentinel alerts with root cause analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search alerts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2.5 bg-slate-700/30 border border-slate-600/30 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all w-64"
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-700/30 hover:bg-slate-700/50 border border-slate-600/30 text-slate-400 hover:text-white rounded-xl text-sm font-medium transition-colors"
          >
            <Settings className="w-4 h-4" />
            Configure
          </motion.button>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Critical', value: alertCounts.critical, icon: XCircle, color: 'bg-red-500' },
          { label: 'Warning', value: alertCounts.warning, icon: AlertTriangle, color: 'bg-amber-500' },
          { label: 'Info', value: alertCounts.info, icon: Info, color: 'bg-blue-500' },
          { label: 'Acknowledged', value: mockAlerts.filter(a => a.acknowledged).length, icon: CheckCircle2, color: 'bg-emerald-500' },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-slate-800/40 border border-slate-700/30 rounded-2xl p-5"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">{stat.label}</p>
                <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-xl ${stat.color}`}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Severity Filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex items-center gap-2"
      >
        <span className="text-sm text-slate-400">Severity:</span>
        {['all', 'critical', 'warning', 'info'].map(severity => (
          <button
            key={severity}
            onClick={() => setSeverityFilter(severity)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              severityFilter === severity
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                : 'bg-slate-700/30 text-slate-400 hover:text-white border border-transparent'
            }`}
          >
            {severity === 'all' ? 'All' : severity.charAt(0).toUpperCase() + severity.slice(1)}
          </button>
        ))}
      </motion.div>

      {/* Alerts List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="space-y-3"
        >
          {filteredAlerts.map((alert, index) => {
            const config = severityConfig[alert.severity]
            const Icon = config.icon
            const SourceIcon = sourceIcon[alert.source] || Bug

            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ scale: 1.01 }}
                onClick={() => setSelectedAlert(alert)}
                className={`bg-slate-800/40 border rounded-2xl p-5 cursor-pointer transition-all hover:border-slate-600/50 ${
                  selectedAlert?.id === alert.id
                    ? 'border-indigo-500/50 ring-2 ring-indigo-500/20'
                    : config.border
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${config.bg}`}>
                      <Icon className={`w-4 h-4 ${config.text}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-white font-medium">{alert.title}</h3>
                        {!alert.acknowledged && (
                          <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                        )}
                      </div>
                      <p className="text-slate-400 text-sm mt-1">{alert.description}</p>
                      <div className="flex items-center gap-4 mt-3">
                        <div className="flex items-center gap-1.5 text-xs text-slate-500">
                          <SourceIcon className="w-3 h-3" />
                          {alert.sourceName}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-slate-500">
                          <Clock className="w-3 h-3" />
                          {alert.timestamp}
                        </div>
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-500" />
                </div>
              </motion.div>
            )
          })}

          {filteredAlerts.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 bg-slate-800/40 border border-slate-700/30 rounded-2xl">
              <Bell className="w-16 h-16 text-slate-600 mb-4" />
              <p className="text-slate-400">No alerts found</p>
            </div>
          )}
        </motion.div>

        {/* RCA Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-slate-800/40 border border-slate-700/30 rounded-2xl p-6 h-fit sticky top-24"
        >
          {selectedAlert ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">Root Cause Analysis</h3>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="p-1.5 hover:bg-slate-700/50 rounded-lg transition-colors"
                >
                  <XCircle className="w-4 h-4 text-slate-400" />
                </button>
              </div>

              <div className="flex items-center gap-2">
                {(() => {
                  const config = severityConfig[selectedAlert.severity]
                  const Icon = config.icon
                  return (
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${config.bg} ${config.text} text-xs font-medium rounded-full`}>
                      <Icon className="w-3 h-3" />
                      {selectedAlert.severity.toUpperCase()}
                    </span>
                  )
                })()}
                <span className="text-slate-500 text-sm">{selectedAlert.timestamp}</span>
              </div>

              <div>
                <h4 className="text-white font-medium">{selectedAlert.title}</h4>
                <p className="text-slate-400 text-sm mt-1">{selectedAlert.description}</p>
              </div>

              <div className="p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-indigo-400" />
                  <span className="text-indigo-400 font-medium text-sm">AI Analysis</span>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {selectedAlert.rca}
                </p>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-sm font-medium transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  View Details
                </motion.button>
                {!selectedAlert.acknowledged && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-medium transition-colors"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Acknowledge
                  </motion.button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12">
              <Zap className="w-16 h-16 text-slate-600 mb-4" />
              <p className="text-slate-400">Select an alert to view</p>
              <p className="text-slate-500 text-sm">root cause analysis</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
