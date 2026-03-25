import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { toast } from 'sonner'

// Types
interface ClusterInfo {
  name: string
  version: string
  nodes: number
  pods: number
  services: number
  namespaces: number
}

interface NodeMetrics {
  name: string
  status: string
  cpu: number
  memory: number
  disk: number
  networkRx: number
  networkTx: number
  age: string
}

interface PodInfo {
  name: string
  namespace: string
  status: string
  restarts: number
  age: string
  node: string
  ip: string
  containers: number
}

interface ServiceInfo {
  name: string
  namespace: string
  type: string
  cluster_ip: string
  ports: string[]
  selector: Record<string, string>
}

interface AlertInfo {
  id: string
  type: string
  severity: 'critical' | 'error' | 'warning' | 'info'
  message: string
  resource: string
  timestamp: string
  rootCause?: string
  suggestedFix?: string
  confidence?: number
}

interface ClusterContextType {
  // State
  isConnected: boolean
  isLoading: boolean
  clusterInfo: ClusterInfo | null
  nodes: NodeMetrics[]
  pods: PodInfo[]
  services: ServiceInfo[]
  alerts: AlertInfo[]
  kubeconfigPath: string
  apiBaseUrl: string

  // Actions
  connect: (path: string) => Promise<boolean>
  disconnect: () => void
  refreshData: () => Promise<void>
}

const ClusterContext = createContext<ClusterContextType | undefined>(undefined)

// API Base URL - configurable for different deployments
const getApiBaseUrl = () => {
  // Check for custom API URL in localStorage or use environment
  const stored = localStorage.getItem('api_base_url')
  if (stored) return stored

  // Default to backend server
  return import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

export function ClusterProvider({ children }: { children: ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [clusterInfo, setClusterInfo] = useState<ClusterInfo | null>(null)
  const [nodes, setNodes] = useState<NodeMetrics[]>([])
  const [pods, setPods] = useState<PodInfo[]>([])
  const [services, setServices] = useState<ServiceInfo[]>([])
  const [alerts, setAlerts] = useState<AlertInfo[]>([])
  const [kubeconfigPath, setKubeconfigPath] = useState('')
  const [apiBaseUrl, setApiBaseUrl] = useState(getApiBaseUrl())

  // Connect to cluster via API
  const connect = useCallback(async (path: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      const response = await fetch(`${apiBaseUrl}/api/cluster/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kubeconfig_path: path })
      })

      const data = await response.json()

      if (!data.valid) {
        toast.error('Failed to validate kubeconfig', {
          description: data.message
        })
        return false
      }

      // Now connect to cluster
      const connectResponse = await fetch(`${apiBaseUrl}/api/cluster/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kubeconfig_path: path })
      })

      if (!connectResponse.ok) {
        throw new Error('Failed to connect to cluster')
      }

      // Fetch initial data
      await fetchClusterData(path)

      toast.success('Connected to cluster successfully', {
        description: `${data.cluster_name} (${data.cluster_version})`
      })

      return true
    } catch (error) {
      // If API is not available, fall back to mock data for demo
      console.warn('Backend API not available, using mock data:', error)
      return connectWithMockData(path)
    } finally {
      setIsLoading(false)
    }
  }, [apiBaseUrl])

  // Connect with mock data (fallback when backend is not available)
  const connectWithMockData = useCallback(async (path: string): Promise<boolean> => {
    await new Promise(resolve => setTimeout(resolve, 1500))

    const mockNodes: NodeMetrics[] = [
      { name: 'k3s-master', status: 'Ready', cpu: 45, memory: 62, disk: 38, networkRx: 1250, networkTx: 890, age: '30d' },
      { name: 'k3s-node-1', status: 'Ready', cpu: 72, memory: 78, disk: 52, networkRx: 2340, networkTx: 1560, age: '15d' },
      { name: 'k3s-node-2', status: 'Ready', cpu: 28, memory: 45, disk: 29, networkRx: 890, networkTx: 670, age: '10d' },
    ]

    const mockPods: PodInfo[] = [
      { name: 'nginx-deployment-7fb96c846b-abc12', namespace: 'default', status: 'Running', restarts: 0, age: '5d', node: 'k3s-node-1', ip: '10.42.1.15', containers: 1 },
      { name: 'redis-master-0', namespace: 'default', status: 'Running', restarts: 0, age: '12d', node: 'k3s-master', ip: '10.42.0.8', containers: 1 },
      { name: 'traefik-6d78d9cc9-xyz89', namespace: 'kube-system', status: 'Running', restarts: 2, age: '30d', node: 'k3s-master', ip: '10.42.0.1', containers: 1 },
      { name: 'coredns-5599c8d5f-abc123', namespace: 'kube-system', status: 'Running', restarts: 0, age: '30d', node: 'k3s-master', ip: '10.42.0.2', containers: 1 },
      { name: 'local-path-provisioner-xyz456', namespace: 'kube-system', status: 'Running', restarts: 0, age: '30d', node: 'k3s-master', ip: '10.42.0.3', containers: 1 },
      { name: 'app-backend-7c9d5f8b4-def56', namespace: 'production', status: 'CrashLoopBackOff', restarts: 15, age: '2d', node: 'k3s-node-2', ip: '10.42.2.10', containers: 2 },
      { name: 'app-frontend-5f8d7c9b4-ghi78', namespace: 'production', status: 'Running', restarts: 0, age: '7d', node: 'k3s-node-1', ip: '10.42.1.20', containers: 1 },
      { name: 'postgres-0', namespace: 'database', status: 'Running', restarts: 0, age: '14d', node: 'k3s-node-2', ip: '10.42.2.5', containers: 1 },
      { name: 'monitoring-stack-xyz123', namespace: 'monitoring', status: 'Pending', restarts: 0, age: '1d', node: '', ip: '', containers: 3 },
      { name: 'job-processor-7c8d9f0a1-jkl34', namespace: 'workers', status: 'Evicted', restarts: 3, age: '3d', node: 'k3s-node-1', ip: '', containers: 1 },
    ]

    const mockAlerts: AlertInfo[] = [
      {
        id: 'alert-1',
        type: 'pod_crash',
        severity: 'critical',
        message: 'Container app-backend is in CrashLoopBackOff state',
        resource: 'production/app-backend-7c9d5f8b4-def56',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        rootCause: 'Out of Memory (OOM) - Container exceeded memory limit of 512Mi',
        suggestedFix: 'Increase memory limits in deployment spec or optimize application memory usage',
        confidence: 0.95
      },
      {
        id: 'alert-2',
        type: 'pod_evicted',
        severity: 'error',
        message: 'Pod job-processor-7c8d9f0a1-jkl34 was evicted due to disk pressure',
        resource: 'workers/job-processor-7c8d9f0a1-jkl34',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        rootCause: 'Node k3s-node-1 has disk pressure (>90% disk usage)',
        suggestedFix: 'Clean up disk space: remove unused images, clear logs, check /var/lib/rancher/k3s',
        confidence: 0.92
      },
      {
        id: 'alert-3',
        type: 'pod_pending',
        severity: 'warning',
        message: 'Pod monitoring-stack-xyz123 has been pending for 1 day',
        resource: 'monitoring/monitoring-stack-xyz123',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        rootCause: 'Insufficient CPU resources on nodes - no node has enough CPU to schedule the pod',
        suggestedFix: 'Add more nodes or reduce CPU requests for this deployment',
        confidence: 0.78
      },
      {
        id: 'alert-4',
        type: 'node_resource',
        severity: 'warning',
        message: 'Node k3s-node-1 memory usage above 75%',
        resource: 'k3s-node-1',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        rootCause: 'High memory utilization due to multiple running applications',
        suggestedFix: 'Review memory-intensive pods and consider scaling or optimization',
        confidence: 0.88
      },
    ]

    const mockServices: ServiceInfo[] = [
      { name: 'kubernetes', namespace: 'default', type: 'ClusterIP', cluster_ip: '10.96.0.1', ports: ['443/TCP'], selector: {} },
      { name: 'nginx-service', namespace: 'default', type: 'LoadBalancer', cluster_ip: '10.96.0.10', ports: ['80/TCP', '443/TCP'], selector: { app: 'nginx' } },
      { name: 'redis-master', namespace: 'default', type: 'ClusterIP', cluster_ip: '10.96.0.11', ports: ['6379/TCP'], selector: { app: 'redis' } },
      { name: 'traefik', namespace: 'kube-system', type: 'LoadBalancer', cluster_ip: '10.96.0.1', ports: ['80/TCP', '443/TCP'], selector: { app: 'traefik' } },
    ]

    setNodes(mockNodes)
    setPods(mockPods)
    setAlerts(mockAlerts)
    setServices(mockServices)
    setClusterInfo({
      name: 'k3s-cluster (Demo)',
      version: 'v1.28.5+k3s1',
      nodes: mockNodes.length,
      pods: mockPods.length,
      services: mockServices.length,
      namespaces: 5
    })
    setKubeconfigPath(path)
    setIsConnected(true)
    localStorage.setItem('kubeconfig_path', path)

    toast.success('Connected to cluster (Demo Mode)', {
      description: 'Using mock data - configure backend API for real data'
    })

    return true
  }, [])

  // Fetch cluster data from API
  const fetchClusterData = useCallback(async (path?: string) => {
    try {
      // Fetch all data in parallel
      const [infoRes, nodesRes, podsRes, servicesRes, alertsRes] = await Promise.all([
        fetch(`${apiBaseUrl}/api/cluster/info`).catch(() => null),
        fetch(`${apiBaseUrl}/api/cluster/nodes`).catch(() => null),
        fetch(`${apiBaseUrl}/api/cluster/pods`).catch(() => null),
        fetch(`${apiBaseUrl}/api/cluster/services`).catch(() => null),
        fetch(`${apiBaseUrl}/api/alerts`).catch(() => null),
      ])

      // Process cluster info
      if (infoRes?.ok) {
        const info = await infoRes.json()
        setClusterInfo(info)
      }

      // Process nodes
      if (nodesRes?.ok) {
        const nodesData = await nodesRes.json()
        setNodes(nodesData.map((n: any) => ({
          name: n.name,
          status: n.status,
          cpu: n.cpu,
          memory: n.memory,
          disk: n.disk,
          networkRx: n.network_rx,
          networkTx: n.network_tx,
          age: n.age
        })))
      }

      // Process pods
      if (podsRes?.ok) {
        const podsData = await podsRes.json()
        setPods(podsData.map((p: any) => ({
          name: p.name,
          namespace: p.namespace,
          status: p.status,
          restarts: p.restarts,
          age: p.age,
          node: p.node,
          ip: p.ip,
          containers: p.containers
        })))
      }

      // Process services
      if (servicesRes?.ok) {
        const servicesData = await servicesRes.json()
        setServices(servicesData.map((s: any) => ({
          name: s.name,
          namespace: s.namespace,
          type: s.type,
          cluster_ip: s.cluster_ip,
          ports: s.ports,
          selector: s.selector
        })))
      }

      // Process alerts
      if (alertsRes?.ok) {
        const alertsData = await alertsRes.json()
        setAlerts(alertsData.map((a: any) => ({
          id: a.id,
          type: a.type,
          severity: a.severity,
          message: a.message,
          resource: a.resource,
          timestamp: a.timestamp,
          rootCause: a.root_cause,
          suggestedFix: a.suggested_fix,
          confidence: a.confidence
        })))
      }

      if (path) {
        setKubeconfigPath(path)
        setIsConnected(true)
        localStorage.setItem('kubeconfig_path', path)
      }
    } catch (error) {
      console.error('Failed to fetch cluster data:', error)
      throw error
    }
  }, [apiBaseUrl])

  // Disconnect from cluster
  const disconnect = useCallback(async () => {
    try {
      await fetch(`${apiBaseUrl}/api/cluster/disconnect`, {
        method: 'POST'
      }).catch(() => null)
    } catch {}

    setIsConnected(false)
    setClusterInfo(null)
    setNodes([])
    setPods([])
    setServices([])
    setAlerts([])
    setKubeconfigPath('')
    localStorage.removeItem('kubeconfig_path')
    toast.info('Disconnected from cluster')
  }, [apiBaseUrl])

  // Refresh data
  const refreshData = useCallback(async () => {
    if (!isConnected) return

    try {
      await fetchClusterData()
    } catch {
      toast.error('Failed to refresh cluster data')
    }
  }, [isConnected, fetchClusterData])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(refreshData, 30000)
    return () => clearInterval(interval)
  }, [isConnected, refreshData])

  // Check for existing connection on mount
  useEffect(() => {
    const storedPath = localStorage.getItem('kubeconfig_path')
    if (storedPath) {
      connect(storedPath).catch(console.error)
    }
  }, [])

  return (
    <ClusterContext.Provider
      value={{
        isConnected,
        isLoading,
        clusterInfo,
        nodes,
        pods,
        services,
        alerts,
        kubeconfigPath,
        apiBaseUrl,
        connect,
        disconnect,
        refreshData
      }}
    >
      {children}
    </ClusterContext.Provider>
  )
}

export function useCluster() {
  const context = useContext(ClusterContext)
  if (context === undefined) {
    throw new Error('useCluster must be used within a ClusterProvider')
  }
  return context
}
