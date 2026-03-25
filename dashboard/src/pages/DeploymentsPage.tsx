import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Box,
  Search,
  Plus,
  RefreshCw,
  ArrowUpDown,
  MoreVertical,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle
} from 'lucide-react'

const mockDeployments = [
  { name: 'nginx-deployment', namespace: 'default', replicas: 3, available: 3, ready: 3, age: '15d', strategy: 'RollingUpdate' },
  { name: 'redis-deployment', namespace: 'default', replicas: 2, available: 2, ready: 2, age: '12d', strategy: 'Recreate' },
  { name: 'traefik', namespace: 'kube-system', replicas: 1, available: 1, ready: 1, age: '30d', strategy: 'RollingUpdate' },
  { name: 'backend-api', namespace: 'production', replicas: 5, available: 5, ready: 4, age: '7d', strategy: 'RollingUpdate' },
  { name: 'frontend-web', namespace: 'production', replicas: 3, available: 3, ready: 3, age: '7d', strategy: 'RollingUpdate' },
  { name: 'postgres', namespace: 'database', replicas: 1, available: 1, ready: 1, age: '14d', strategy: 'Recreate' },
  { name: 'prometheus', namespace: 'monitoring', replicas: 1, available: 1, ready: 1, age: '1d', strategy: 'RollingUpdate' },
  { name: 'grafana', namespace: 'monitoring', replicas: 1, available: 0, ready: 0, age: '1d', strategy: 'RollingUpdate' },
]

const statusConfig: Record<string, { bg: string; text: string; icon: any; label: string }> = {
  healthy: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: CheckCircle2, label: 'Healthy' },
  degraded: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: AlertTriangle, label: 'Degraded' },
  unhealthy: { bg: 'bg-red-500/20', text: 'text-red-400', icon: XCircle, label: 'Unhealthy' },
}

export default function DeploymentsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [namespaceFilter, setNamespaceFilter] = useState('all')

  const namespaces = [...new Set(mockDeployments.map(d => d.namespace))]

  const filteredDeployments = mockDeployments.filter(deployment => {
    const matchesSearch = deployment.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesNamespace = namespaceFilter === 'all' || deployment.namespace === namespaceFilter
    return matchesSearch && matchesNamespace
  })

  const getStatus = (deployment: typeof mockDeployments[0]) => {
    if (deployment.available === 0) return 'unhealthy'
    if (deployment.ready < deployment.replicas) return 'degraded'
    return 'healthy'
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
          <h1 className="text-2xl font-bold text-white">Deployments</h1>
          <p className="text-slate-400 text-sm mt-1">Manage application deployments</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search deployments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2.5 bg-slate-700/30 border border-slate-600/30 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all w-64"
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Deployment
          </motion.button>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Deployments', value: mockDeployments.length, icon: Box, color: 'bg-indigo-500' },
          { label: 'Healthy', value: mockDeployments.filter(d => getStatus(d) === 'healthy').length, icon: CheckCircle2, color: 'bg-emerald-500' },
          { label: 'Degraded', value: mockDeployments.filter(d => getStatus(d) === 'degraded').length, icon: AlertTriangle, color: 'bg-amber-500' },
          { label: 'Unavailable', value: mockDeployments.filter(d => getStatus(d) === 'unhealthy').length, icon: XCircle, color: 'bg-red-500' },
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

      {/* Namespace Filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex items-center gap-2"
      >
        <span className="text-sm text-slate-400">Namespace:</span>
        <button
          onClick={() => setNamespaceFilter('all')}
          className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
            namespaceFilter === 'all'
              ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
              : 'bg-slate-700/30 text-slate-400 hover:text-white border border-transparent'
          }`}
        >
          All
        </button>
        {namespaces.map(ns => (
          <button
            key={ns}
            onClick={() => setNamespaceFilter(ns)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              namespaceFilter === ns
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                : 'bg-slate-700/30 text-slate-400 hover:text-white border border-transparent'
            }`}
          >
            {ns}
          </button>
        ))}
      </motion.div>

      {/* Deployments Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-slate-800/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Deployment</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Replicas</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Ready</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Strategy</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Age</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody>
              {filteredDeployments.map((deployment, index) => {
                const status = getStatus(deployment)
                const config = statusConfig[status]
                const Icon = config.icon
                const readyPercent = (deployment.ready / deployment.replicas) * 100

                return (
                  <motion.tr
                    key={deployment.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-500/20 rounded-lg">
                          <Box className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div>
                          <span className="text-white font-medium">{deployment.name}</span>
                          <span className="text-slate-500 text-xs ml-2">({deployment.namespace})</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${config.bg} ${config.text} text-xs font-medium rounded-full`}>
                        <Icon className="w-3 h-3" />
                        {config.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-white">{deployment.available}</span>
                        <span className="text-slate-500">/</span>
                        <span className="text-slate-400">{deployment.replicas}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">{deployment.ready} ready</span>
                          <span className={readyPercent === 100 ? 'text-emerald-400' : 'text-amber-400'}>
                            {readyPercent}%
                          </span>
                        </div>
                        <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${readyPercent}%` }}
                            transition={{ duration: 0.8, delay: index * 0.1 }}
                            className={`h-full rounded-full ${
                              readyPercent === 100
                                ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                                : 'bg-gradient-to-r from-amber-500 to-amber-400'
                            }`}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-slate-400 text-sm">{deployment.strategy}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-slate-400 text-sm">{deployment.age}</span>
                    </td>
                    <td className="px-6 py-4">
                      <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
                        <MoreVertical className="w-4 h-4 text-slate-400" />
                      </button>
                    </td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}
