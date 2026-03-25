import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Server,
  Cpu,
  HardDrive,
  Network,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  MoreVertical,
  Search,
  Filter
} from 'lucide-react'
import { useCluster } from '../context/ClusterContext'

type SortKey = 'name' | 'cpu' | 'memory' | 'disk'

export default function NodesPage() {
  const { nodes } = useCluster()
  const [searchTerm, setSearchTerm] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('name')
  const [sortAsc, setSortAsc] = useState(true)

  const filteredNodes = nodes
    .filter(node => node.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
      }
      return sortAsc ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number)
    })

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(true)
    }
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
          <h1 className="text-2xl font-bold text-white">Nodes</h1>
          <p className="text-slate-400 text-sm mt-1">Manage and monitor cluster nodes</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2.5 bg-slate-700/30 border border-slate-600/30 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all w-64"
            />
          </div>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Nodes', value: nodes.length, icon: Server, color: 'bg-indigo-500' },
          { label: 'Ready', value: nodes.length, icon: CheckCircle2, color: 'bg-emerald-500' },
          { label: 'CPU Cores', value: nodes.length * 4, icon: Cpu, color: 'bg-purple-500' },
          { label: 'Avg Memory', value: `${Math.round(nodes.reduce((acc, n) => acc + n.memory, 0) / (nodes.length || 1))}%`, icon: HardDrive, color: 'bg-pink-500' },
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

      {/* Nodes Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-slate-800/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left px-6 py-4">
                  <button
                    onClick={() => handleSort('name')}
                    className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider hover:text-white transition-colors"
                  >
                    Node Name
                    <SortIcon active={sortKey === 'name'} ascending={sortAsc} />
                  </button>
                </th>
                <th className="text-left px-6 py-4">
                  <button
                    onClick={() => handleSort('cpu')}
                    className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider hover:text-white transition-colors"
                  >
                    CPU
                    <SortIcon active={sortKey === 'cpu'} ascending={sortAsc} />
                  </button>
                </th>
                <th className="text-left px-6 py-4">
                  <button
                    onClick={() => handleSort('memory')}
                    className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider hover:text-white transition-colors"
                  >
                    Memory
                    <SortIcon active={sortKey === 'memory'} ascending={sortAsc} />
                  </button>
                </th>
                <th className="text-left px-6 py-4">
                  <button
                    onClick={() => handleSort('disk')}
                    className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider hover:text-white transition-colors"
                  >
                    Disk
                    <SortIcon active={sortKey === 'disk'} ascending={sortAsc} />
                  </button>
                </th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Network
                </th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody>
              {filteredNodes.map((node, index) => (
                <motion.tr
                  key={node.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-indigo-500/20 rounded-lg">
                        <Server className="w-4 h-4 text-indigo-400" />
                      </div>
                      <span className="text-white font-medium">{node.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{node.cpu}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${node.cpu}%` }}
                          transition={{ duration: 0.8, delay: index * 0.1 }}
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{node.memory}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${node.memory}%` }}
                          transition={{ duration: 0.8, delay: index * 0.1 + 0.1 }}
                          className="h-full bg-gradient-to-r from-pink-500 to-rose-500 rounded-full"
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{node.disk}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${node.disk}%` }}
                          transition={{ duration: 0.8, delay: index * 0.1 + 0.2 }}
                          className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1.5">
                        <Network className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-slate-400">↓ {(node.networkRx / 1024).toFixed(1)} KB/s</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Network className="w-3.5 h-3.5 text-blue-400" />
                        <span className="text-slate-400">↑ {(node.networkTx / 1024).toFixed(1)} KB/s</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full">
                      <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                      Ready
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
                      <MoreVertical className="w-4 h-4 text-slate-400" />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}

function SortIcon({ active, ascending }: { active: boolean; ascending: boolean }) {
  return (
    <svg
      className={`w-3 h-3 transition-colors ${active ? 'text-indigo-400' : 'text-slate-600'}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      {ascending ? (
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      ) : (
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      )}
    </svg>
  )
}
