import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Box,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  MoreVertical,
  Terminal,
  Container
} from 'lucide-react'
import { useCluster } from '../context/ClusterContext'

type StatusFilter = 'all' | 'Running' | 'Pending' | 'Failed'

const statusConfig: Record<string, { bg: string; text: string; icon: any; label: string }> = {
  Running: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: CheckCircle2, label: 'Running' },
  Pending: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: Clock, label: 'Pending' },
  CrashLoopBackOff: { bg: 'bg-red-500/20', text: 'text-red-400', icon: XCircle, label: 'CrashLoopBackOff' },
  Evicted: { bg: 'bg-red-500/20', text: 'text-red-400', icon: AlertTriangle, label: 'Evicted' },
}

export default function PodsPage() {
  const { pods } = useCluster()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [namespaceFilter, setNamespaceFilter] = useState('all')

  const namespaces: string[] = Array.from(new Set(pods.map((p) => p.namespace as string)))

  const filteredPods = pods.filter(pod => {
    const matchesSearch = pod.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || pod.status === statusFilter
    const matchesNamespace = namespaceFilter === 'all' || pod.namespace === namespaceFilter
    return matchesSearch && matchesStatus && matchesNamespace
  })

  const statusCounts = {
    Running: pods.filter(p => p.status === 'Running').length,
    Pending: pods.filter(p => p.status === 'Pending').length,
    Failed: pods.filter(p => p.status === 'CrashLoopBackOff' || p.status === 'Evicted').length,
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
          <h1 className="text-2xl font-bold text-white">Pods</h1>
          <p className="text-slate-400 text-sm mt-1">Monitor all pods across namespaces</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search pods..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2.5 bg-slate-700/30 border border-slate-600/30 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all w-64"
            />
          </div>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800/40 border border-slate-700/30 rounded-2xl p-5 cursor-pointer hover:border-indigo-500/30 transition-all"
          onClick={() => setStatusFilter('all')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Pods</p>
              <p className="text-2xl font-bold text-white mt-1">{pods.length}</p>
            </div>
            <div className="p-3 rounded-xl bg-indigo-500">
              <Box className="w-5 h-5 text-white" />
            </div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className={`bg-slate-800/40 border rounded-2xl p-5 cursor-pointer transition-all ${
            statusFilter === 'Running' ? 'border-emerald-500/50' : 'border-slate-700/30'
          }`}
          onClick={() => setStatusFilter(statusFilter === 'Running' ? 'all' : 'Running')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Running</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{statusCounts.Running}</p>
            </div>
            <div className="p-3 rounded-xl bg-emerald-500/20">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className={`bg-slate-800/40 border rounded-2xl p-5 cursor-pointer transition-all ${
            statusFilter === 'Pending' ? 'border-amber-500/50' : 'border-slate-700/30'
          }`}
          onClick={() => setStatusFilter(statusFilter === 'Pending' ? 'all' : 'Pending')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Pending</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{statusCounts.Pending}</p>
            </div>
            <div className="p-3 rounded-xl bg-amber-500/20">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className={`bg-slate-800/40 border rounded-2xl p-5 cursor-pointer transition-all ${
            statusFilter === 'Failed' ? 'border-red-500/50' : 'border-slate-700/30'
          }`}
          onClick={() => setStatusFilter(statusFilter === 'Failed' ? 'all' : 'Failed')}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Failed</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{statusCounts.Failed}</p>
            </div>
            <div className="p-3 rounded-xl bg-red-500/20">
              <XCircle className="w-5 h-5 text-red-400" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Namespace Filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex items-center gap-2 flex-wrap"
      >
        <Filter className="w-4 h-4 text-slate-500" />
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

      {/* Pods Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        {filteredPods.map((pod, index) => {
          const config = statusConfig[pod.status] || statusConfig.Running
          const Icon = config.icon

          return (
            <motion.div
              key={pod.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              whileHover={{ y: -2 }}
              className="bg-slate-800/40 border border-slate-700/30 rounded-2xl p-5 hover:border-slate-600/50 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${config.bg}`}>
                    <Container className={`w-4 h-4 ${config.text}`} />
                  </div>
                  <div>
                    <h3 className="text-white font-medium text-sm truncate max-w-[180px]">{pod.name.split('-').slice(0, 2).join('-')}</h3>
                    <p className="text-slate-500 text-xs">{pod.namespace}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 ${config.bg} ${config.text} text-xs font-medium rounded-full`}>
                  <Icon className="w-3 h-3" />
                  {config.label}
                </span>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">IP</span>
                  <span className="text-slate-300 font-mono text-xs">{pod.ip || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Node</span>
                  <span className="text-slate-300 text-xs">{pod.node || 'Pending'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Restarts</span>
                  <span className={pod.restarts > 5 ? 'text-red-400' : 'text-slate-300'}>
                    {pod.restarts}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Age</span>
                  <span className="text-slate-300">{pod.age}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-700/30 flex items-center justify-between">
                <span className="text-xs text-slate-500">{pod.containers} container{pod.containers > 1 ? 's' : ''}</span>
                <button className="p-1.5 hover:bg-slate-700/50 rounded-lg transition-colors">
                  <Terminal className="w-3.5 h-3.5 text-slate-400" />
                </button>
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      {filteredPods.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-16"
        >
          <Box className="w-16 h-16 text-slate-600 mb-4" />
          <p className="text-slate-400">No pods found</p>
          <p className="text-slate-500 text-sm">Try adjusting your search or filters</p>
        </motion.div>
      )}
    </div>
  )
}
