import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Network,
  Search,
  ExternalLink,
  Copy,
  MoreVertical,
  Globe,
  Server,
  Container
} from 'lucide-react'

const mockServices = [
  { name: 'kubernetes', type: 'ClusterIP', clusterIP: '10.43.0.1', ports: '443/TCP', selector: null, namespace: 'default', age: '30d' },
  { name: 'nginx-service', type: 'LoadBalancer', clusterIP: '10.43.0.100', ports: '80/TCP, 443/TCP', selector: 'app=nginx', namespace: 'default', age: '15d' },
  { name: 'redis-master', type: 'ClusterIP', clusterIP: '10.43.0.101', ports: '6379/TCP', selector: 'app=redis', namespace: 'default', age: '12d' },
  { name: 'traefik', type: 'LoadBalancer', clusterIP: '10.43.0.10', ports: '80/TCP, 443/TCP', selector: 'app=traefik', namespace: 'kube-system', age: '30d' },
  { name: 'app-backend', type: 'ClusterIP', clusterIP: '10.43.0.200', ports: '8080/TCP', selector: 'app=backend', namespace: 'production', age: '7d' },
  { name: 'app-frontend', type: 'LoadBalancer', clusterIP: '10.43.0.201', ports: '3000/TCP', selector: 'app=frontend', namespace: 'production', age: '7d' },
  { name: 'postgres-service', type: 'ClusterIP', clusterIP: '10.43.0.50', ports: '5432/TCP', selector: 'app=postgres', namespace: 'database', age: '14d' },
  { name: 'monitoring-stack', type: 'LoadBalancer', clusterIP: '10.43.0.75', ports: '9090/TCP, 3000/TCP', selector: 'app=monitoring', namespace: 'monitoring', age: '1d' },
]

const typeConfig: Record<string, { bg: string; text: string; icon: any }> = {
  ClusterIP: { bg: 'bg-blue-500/20', text: 'text-blue-400', icon: Server },
  LoadBalancer: { bg: 'bg-purple-500/20', text: 'text-purple-400', icon: Globe },
  NodePort: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: Container },
}

export default function ServicesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')

  const filteredServices = mockServices.filter(service => {
    const matchesSearch = service.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = typeFilter === 'all' || service.type === typeFilter
    return matchesSearch && matchesType
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-white">Services</h1>
          <p className="text-slate-400 text-sm mt-1">Manage cluster service networking</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search services..."
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
          { label: 'Total Services', value: mockServices.length, icon: Network, color: 'bg-indigo-500' },
          { label: 'ClusterIP', value: mockServices.filter(s => s.type === 'ClusterIP').length, icon: Server, color: 'bg-blue-500' },
          { label: 'LoadBalancer', value: mockServices.filter(s => s.type === 'LoadBalancer').length, icon: Globe, color: 'bg-purple-500' },
          { label: 'Namespaces', value: [...new Set(mockServices.map(s => s.namespace))].length, icon: Network, color: 'bg-pink-500' },
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

      {/* Type Filter */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex items-center gap-2"
      >
        <span className="text-sm text-slate-400">Type:</span>
        {['all', 'ClusterIP', 'LoadBalancer', 'NodePort'].map(type => (
          <button
            key={type}
            onClick={() => setTypeFilter(type)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              typeFilter === type
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                : 'bg-slate-700/30 text-slate-400 hover:text-white border border-transparent'
            }`}
          >
            {type === 'all' ? 'All Types' : type}
          </button>
        ))}
      </motion.div>

      {/* Services Table */}
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
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Service</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Type</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Cluster IP</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Ports</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Selector</th>
                <th className="text-left px-6 py-4 text-xs font-medium text-slate-400 uppercase tracking-wider">Age</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody>
              {filteredServices.map((service, index) => {
                const config = typeConfig[service.type] || typeConfig.ClusterIP
                const Icon = config.icon

                return (
                  <motion.tr
                    key={service.name}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${config.bg}`}>
                          <Network className={`w-4 h-4 ${config.text}`} />
                        </div>
                        <div>
                          <span className="text-white font-medium">{service.name}</span>
                          <span className="text-slate-500 text-xs ml-2">({service.namespace})</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${config.bg} ${config.text} text-xs font-medium rounded-full`}>
                        <Icon className="w-3 h-3" />
                        {service.type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <code className="text-slate-300 font-mono text-sm">{service.clusterIP}</code>
                        <button className="p-1 hover:bg-slate-700/50 rounded transition-colors">
                          <Copy className="w-3 h-3 text-slate-500" />
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-slate-300 font-mono text-sm">{service.ports}</code>
                    </td>
                    <td className="px-6 py-4">
                      {service.selector ? (
                        <code className="text-indigo-400 text-sm">{service.selector}</code>
                      ) : (
                        <span className="text-slate-500 text-sm">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-slate-400 text-sm">{service.age}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
                          <ExternalLink className="w-4 h-4 text-slate-400" />
                        </button>
                        <button className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors">
                          <MoreVertical className="w-4 h-4 text-slate-400" />
                        </button>
                      </div>
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
