import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Server,
  Box,
  Network,
  Layers,
  AlertTriangle,
  Activity,
  Cpu,
  HardDrive,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ArrowRight,
  ChevronRight
} from 'lucide-react'
// @ts-expect-error - recharts types issue
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { useCluster } from '../context/ClusterContext'

// Animated counter component
function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [displayValue, setDisplayValue] = useState(0)

  useState(() => {
    const duration = 1000
    const steps = 30
    const increment = value / steps
    let current = 0

    const timer = setInterval(() => {
      current += increment
      if (current >= value) {
        setDisplayValue(value)
        clearInterval(timer)
      } else {
        setDisplayValue(Math.floor(current))
      }
    }, duration / steps)

    return () => clearInterval(timer)
  })

  return <span>{displayValue}{suffix}</span>
}

// Metric Card Component
function MetricCard({
  title,
  value,
  suffix,
  icon: Icon,
  trend,
  color,
  delay = 0
}: {
  title: string
  value: number
  suffix?: string
  icon: React.ElementType
  trend?: number
  color: string
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="relative overflow-hidden bg-[#0a0a0a]/80 backdrop-blur-xl border border-[#2a2a2a] rounded-2xl p-6 group hover:border-[#8EC060]/30 transition-all"
    >
      {/* Background Glow */}
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${color}`} />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-xl ${color}`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          {trend !== undefined && (
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${
              trend >= 0 ? 'bg-[#8EC060]/20 text-[#8EC060]' : 'bg-[#F95106]/20 text-[#F95106]'
            }`}>
              {trend >= 0 ? '+' : ''}{trend}%
            </span>
          )}
        </div>

        <h3 className="text-[#8a8a8a] text-sm font-medium mb-1">{title}</h3>
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-bold text-[#FAFAFA]">
            <AnimatedCounter value={value} />
          </span>
          {suffix && <span className="text-[#6a6a6a] text-sm">{suffix}</span>}
        </div>
      </div>

      {/* Decorative gradient */}
      <div className={`absolute -right-8 -bottom-8 w-24 h-24 ${color} opacity-20 rounded-full blur-2xl`} />
    </motion.div>
  )
}

// Node Status Card
function NodeStatusCard({ name, cpu, memory, status }: { name: string; cpu: number; memory: number; status: string }) {
  const statusColor = status === 'Ready' ? '#8EC060' : '#F95106'

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ scale: 1.02 }}
      className="bg-[#0a0a0a]/80 border border-[#2a2a2a] rounded-xl p-4 hover:border-[#8EC060]/30 transition-all"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-[#8a8a8a]" />
          <span className="text-[#FAFAFA] font-medium text-sm">{name}</span>
        </div>
        <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: statusColor }} />
      </div>

      <div className="space-y-2">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[#6a6a6a]">CPU</span>
            <span className="text-[#8a8a8a]">{cpu}%</span>
          </div>
          <div className="h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${cpu}%` }}
              transition={{ duration: 1, delay: 0.3 }}
              className="h-full bg-gradient-to-r from-[#8EC060] to-[#435E2A] rounded-full"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[#6a6a6a]">Memory</span>
            <span className="text-[#8a8a8a]">{memory}%</span>
          </div>
          <div className="h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${memory}%` }}
              transition={{ duration: 1, delay: 0.5 }}
              className="h-full bg-gradient-to-r from-[#F95106] to-[#D94500] rounded-full"
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// Alert Item Component
function AlertItem({
  severity,
  message,
  resource,
  timestamp,
  confidence,
  onClick
}: {
  severity: 'critical' | 'error' | 'warning' | 'info'
  message: string
  resource: string
  timestamp: string
  confidence?: number
  onClick?: () => void
}) {
  const severityConfig = {
    critical: { bg: 'bg-[#F95106]/10', border: 'border-[#F95106]/30', text: 'text-[#F95106]', icon: XCircle },
    error: { bg: 'bg-[#F95106]/10', border: 'border-[#F95106]/30', text: 'text-[#F95106]', icon: AlertCircle },
    warning: { bg: 'bg-[#F59E0B]/10', border: 'border-[#F59E0B]/30', text: 'text-[#F59E0B]', icon: AlertTriangle },
    info: { bg: 'bg-[#0F3DDE]/10', border: 'border-[#0F3DDE]/30', text: 'text-[#0F3DDE]', icon: AlertCircle }
  }

  const config = severityConfig[severity]
  const Icon = config.icon

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ x: 4 }}
      onClick={onClick}
      className={`p-4 ${config.bg} border ${config.border} rounded-xl cursor-pointer hover:scale-[1.01] transition-all`}
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 ${config.text} flex-shrink-0 mt-0.5`} />
        <div className="flex-1 min-w-0">
          <p className="text-[#FAFAFA] text-sm font-medium mb-1 line-clamp-2">{message}</p>
          <div className="flex items-center gap-3 text-xs text-[#6a6a6a]">
            <span className="truncate">{resource}</span>
            <span>•</span>
            <span>{timestamp}</span>
            {confidence !== undefined && (
              <>
                <span>•</span>
                <span className={config.text}>{Math.round(confidence * 100)}% confidence</span>
              </>
            )}
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-[#5a5a5a] flex-shrink-0" />
      </div>
    </motion.div>
  )
}

export default function DashboardOverview() {
  const { clusterInfo, nodes, pods, alerts, isConnected } = useCluster()

  // Calculate stats
  const totalCpu = nodes.reduce((acc, n) => acc + n.cpu, 0) / (nodes.length || 1)
  const totalMemory = nodes.reduce((acc, n) => acc + n.memory, 0) / (nodes.length || 1)
  const runningPods = pods.filter(p => p.status === 'Running').length
  const criticalAlerts = alerts.filter(a => a.severity === 'critical' || a.severity === 'error').length

  // Mock chart data
  const cpuChartData = [
    { time: '10:00', value: 45 },
    { time: '10:05', value: 52 },
    { time: '10:10', value: 48 },
    { time: '10:15', value: 61 },
    { time: '10:20', value: 55 },
    { time: '10:25', value: 67 },
    { time: '10:30', value: 58 },
  ]

  const podStatusData = [
    { status: 'Running', count: runningPods, color: '#8EC060' },
    { status: 'Pending', count: pods.filter(p => p.status === 'Pending').length, color: '#F59E0B' },
    { status: 'Failed', count: pods.filter(p => p.status === 'CrashLoopBackOff' || p.status === 'Evicted').length, color: '#F95106' },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-[#FAFAFA]">Cluster Overview</h1>
          <p className="text-[#8a8a8a] text-sm mt-1">Real-time monitoring and diagnostics</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-[#0a0a0a]/80 border border-[#2a2a2a] rounded-xl">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#8EC060] animate-pulse' : 'bg-[#F95106]'}`} />
          <span className="text-sm text-[#8a8a8a]">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Nodes"
          value={clusterInfo?.nodes || 0}
          icon={Server}
          color="bg-[#8EC060]"
          delay={0}
        />
        <MetricCard
          title="Total Pods"
          value={clusterInfo?.pods || 0}
          icon={Box}
          color="bg-[#0F3DDE]"
          delay={0.1}
        />
        <MetricCard
          title="Services"
          value={clusterInfo?.services || 0}
          icon={Network}
          color="bg-[#F59E0B]"
          delay={0.2}
        />
        <MetricCard
          title="Active Alerts"
          value={criticalAlerts}
          icon={AlertTriangle}
          color="bg-[#F95106]"
          trend={criticalAlerts > 0 ? 10 : -5}
          delay={0.3}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CPU Usage Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 bg-[#0a0a0a]/80 backdrop-blur-xl border border-[#2a2a2a] rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#8EC060]/20 rounded-lg">
                <Cpu className="w-5 h-5 text-[#8EC060]" />
              </div>
              <div>
                <h3 className="text-[#FAFAFA] font-medium">Cluster CPU Usage</h3>
                <p className="text-[#6a6a6a] text-xs">Real-time CPU utilization</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-[#FAFAFA]">{Math.round(totalCpu)}%</p>
              <p className="text-[#6a6a6a] text-xs">Average</p>
            </div>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cpuChartData}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8EC060" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8EC060" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6a6a6a', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6a6a6a', fontSize: 12 }}
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0a0a0a',
                    border: '1px solid #2a2a2a',
                    borderRadius: '8px',
                    color: '#FAFAFA'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#8EC060"
                  strokeWidth={2}
                  fill="url(#cpuGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Pod Status Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-[#0a0a0a]/80 backdrop-blur-xl border border-[#2a2a2a] rounded-2xl p-6"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-[#0F3DDE]/20 rounded-lg">
              <Layers className="w-5 h-5 text-[#0F3DDE]" />
            </div>
            <div>
              <h3 className="text-[#FAFAFA] font-medium">Pod Status</h3>
              <p className="text-[#6a6a6a] text-xs">Distribution by state</p>
            </div>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={podStatusData} layout="vertical">
                <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#6a6a6a', fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="status"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6a6a6a', fontSize: 12 }}
                  width={70}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0a0a0a',
                    border: '1px solid #2a2a2a',
                    borderRadius: '8px',
                    color: '#FAFAFA'
                  }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {podStatusData.map((entry, index) => (
                    <rect key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-center gap-4 mt-4">
            {podStatusData.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-xs text-[#8a8a8a]">{item.status}: {item.count}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Node Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-[#0a0a0a]/80 backdrop-blur-xl border border-[#2a2a2a] rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#8EC060]/20 rounded-lg">
                <Activity className="w-5 h-5 text-[#8EC060]" />
              </div>
              <div>
                <h3 className="text-[#FAFAFA] font-medium">Node Health</h3>
                <p className="text-[#6a6a6a] text-xs">Resource utilization per node</p>
              </div>
            </div>
            <button className="text-xs text-[#8EC060] hover:text-[#A8D080] flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {nodes.map((node) => (
              <NodeStatusCard
                key={node.name}
                name={node.name}
                cpu={node.cpu}
                memory={node.memory}
                status={node.status}
              />
            ))}
          </div>
        </motion.div>

        {/* Recent Alerts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-[#0a0a0a]/80 backdrop-blur-xl border border-[#2a2a2a] rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#F95106]/20 rounded-lg">
                <Zap className="w-5 h-5 text-[#F95106]" />
              </div>
              <div>
                <h3 className="text-[#FAFAFA] font-medium">Sentinel Alerts</h3>
                <p className="text-[#6a6a6a] text-xs">AI-detected issues with RCA</p>
              </div>
            </div>
            <button className="text-xs text-[#8EC060] hover:text-[#A8D080] flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {alerts.slice(0, 3).map((alert) => (
              <AlertItem
                key={alert.id}
                severity={alert.severity}
                message={alert.message}
                resource={alert.resource}
                timestamp={new Date(alert.timestamp).toLocaleTimeString()}
                confidence={alert.confidence}
              />
            ))}

            {alerts.length === 0 && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <CheckCircle2 className="w-12 h-12 text-[#8EC060]/50 mb-3" />
                <p className="text-[#8a8a8a]">All systems healthy</p>
                <p className="text-[#6a6a6a] text-xs">No alerts detected</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
