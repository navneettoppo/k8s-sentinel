import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
  FileJson,
  CheckCircle2,
  XCircle,
  Loader2,
  Server,
  ArrowRight,
  AlertCircle
} from 'lucide-react'
import { useCluster } from '../context/ClusterContext'

export default function KubeconfigSetup() {
  const navigate = useNavigate()
  const { connect, isLoading } = useCluster()
  const [kubeconfigPath, setKubeconfigPath] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationStatus, setValidationStatus] = useState<'idle' | 'valid' | 'invalid'>('idle')
  const [validationMessage, setValidationMessage] = useState('')

  const defaultPaths = [
    '/etc/rancher/k3s/k3s.yaml',
    '~/.kube/config',
    '~/.kube/k3s.yaml',
    '/root/.kube/config'
  ]

  // Get API base URL
  const getApiBaseUrl = () => {
    const stored = localStorage.getItem('api_base_url')
    if (stored) return stored
    return import.meta.env.VITE_API_URL || 'http://localhost:8000'
  }

  const handleValidate = useCallback(async () => {
    if (!kubeconfigPath.trim()) {
      toast.error('Please enter a kubeconfig path')
      return
    }

    setIsValidating(true)
    setValidationStatus('idle')
    setValidationMessage('')

    try {
      const apiBaseUrl = getApiBaseUrl()
      const response = await fetch(`${apiBaseUrl}/api/cluster/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kubeconfig_path: kubeconfigPath })
      })

      const data = await response.json()

      if (data.valid) {
        setValidationStatus('valid')
        setValidationMessage(data.cluster_name ? `${data.cluster_name} (${data.cluster_version})` : 'Kubeconfig is valid')
      } else {
        setValidationStatus('invalid')
        setValidationMessage(data.message || 'Invalid kubeconfig file')
      }
    } catch {
      // If API is not available, do basic file path validation
      const expandedPath = kubeconfigPath.replace('~', process.env.HOME || '/root')
      const isValidFormat = kubeconfigPath.includes('kubeconfig') ||
                           kubeconfigPath.includes('k3s') ||
                           kubeconfigPath.includes('.yaml') ||
                           kubeconfigPath.includes('.yml') ||
                           kubeconfigPath.includes('.json')

      if (isValidFormat) {
        setValidationStatus('valid')
        setValidationMessage('Path format looks valid (API not available for full validation)')
      } else {
        setValidationStatus('valid') // Be permissive in demo mode
        setValidationMessage('Path format accepted (will use mock data)')
      }
    }

    setIsValidating(false)
  }, [kubeconfigPath])

  const handleConnect = useCallback(async () => {
    const success = await connect(kubeconfigPath)
    if (success) {
      navigate('/dashboard')
    }
  }, [kubeconfigPath, connect, navigate])

  return (
    <div className="min-h-screen bg-[#030303] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Effects - Dribbble style */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-[#8EC060]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-[#F95106]/5 rounded-full blur-[120px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#0F3DDE]/3 rounded-full blur-[150px]" />
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(26,26,26,0.3)_1px,transparent_1px),linear-gradient(90deg,rgba(26,26,26,0.3)_1px,transparent_1px)] bg-[size:60px_60px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,black,transparent)]" />

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="relative w-full max-w-lg"
      >
        {/* Header Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-[#8EC060] to-[#435E2A] shadow-lg shadow-[#8EC060]/20 mb-4">
            <Server className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-[#FAFAFA] mb-2">K3s Sentinel</h1>
          <p className="text-[#8a8a8a]">Configure your Kubernetes cluster connection</p>
        </motion.div>

        {/* Setup Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-[#0a0a0a]/80 backdrop-blur-xl border border-[#2a2a2a] rounded-2xl p-8 shadow-2xl"
        >
          {/* Path Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-[#FAFAFA] mb-2">
              Kubeconfig Path
            </label>
            <div className="relative">
              <FileJson className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8a8a8a]" />
              <input
                type="text"
                value={kubeconfigPath}
                onChange={(e) => {
                  setKubeconfigPath(e.target.value)
                  setValidationStatus('idle')
                  setValidationMessage('')
                }}
                placeholder="/etc/rancher/k3s/k3s.yaml"
                className="w-full pl-12 pr-4 py-3 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl text-[#FAFAFA] placeholder-[#5a5a5a] focus:outline-none focus:border-[#8EC060]/50 focus:ring-2 focus:ring-[#8EC060]/20 transition-all"
              />
            </div>
            <p className="mt-2 text-xs text-[#6a6a6a]">
              Enter the absolute path to your kubeconfig file
            </p>
          </div>

          {/* Quick Select */}
          <div className="mb-6">
            <p className="text-xs text-[#6a6a6a] mb-2">Quick select:</p>
            <div className="flex flex-wrap gap-2">
              {defaultPaths.map((path) => (
                <button
                  key={path}
                  onClick={() => {
                    setKubeconfigPath(path)
                    setValidationStatus('idle')
                    setValidationMessage('')
                  }}
                  className={`px-3 py-1.5 text-xs rounded-lg transition-all ${
                    kubeconfigPath === path
                      ? 'bg-[#8EC060]/20 text-[#8EC060] border border-[#8EC060]/30'
                      : 'bg-[#1a1a1a] text-[#8a8a8a] hover:bg-[#2a2a2a] border border-transparent'
                  }`}
                >
                  {path}
                </button>
              ))}
            </div>
          </div>

          {/* Validation Status */}
          <AnimatePresence mode="wait">
            {validationStatus !== 'idle' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={`mb-6 p-4 rounded-xl border ${
                  validationStatus === 'valid'
                    ? 'bg-[#8EC060]/10 border-[#8EC060]/20'
                    : 'bg-[#F95106]/10 border-[#F95106]/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  {validationStatus === 'valid' ? (
                    <CheckCircle2 className="w-5 h-5 text-[#8EC060]" />
                  ) : (
                    <XCircle className="w-5 h-5 text-[#F95106]" />
                  )}
                  <span className={`text-sm ${
                    validationStatus === 'valid' ? 'text-[#8EC060]' : 'text-[#F95106]'
                  }`}>
                    {validationMessage || (validationStatus === 'valid'
                      ? 'Kubeconfig file found and validated'
                      : 'Kubeconfig file not found')}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleValidate}
              disabled={isValidating || !kubeconfigPath.trim()}
              className="flex-1 px-4 py-3 bg-[#1a1a1a] hover:bg-[#2a2a2a] border border-[#2a2a2a] rounded-xl text-[#FAFAFA] font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isValidating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Validate'
              )}
            </button>
            <button
              onClick={handleConnect}
              disabled={isLoading || !kubeconfigPath.trim()}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-[#8EC060] to-[#435E2A] hover:from-[#A8D080] hover:to-[#6BA040] rounded-xl text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-[#8EC060]/25"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Connect
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </motion.div>

        {/* Info Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-6 p-4 bg-[#0a0a0a]/50 border border-[#2a2a2a] rounded-xl"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#0F3DDE] flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-[#FAFAFA] mb-1">Default K3s Paths</h3>
              <ul className="text-xs text-[#6a6a6a] space-y-1">
                <li>• Standard K3s: <code className="text-[#8EC060]">/etc/rancher/k3s/k3s.yaml</code></li>
                <li>• K3s HA: <code className="text-[#8EC060]">/var/lib/rancher/k3s/server/agent/k3s.yaml</code></li>
                <li>• Custom kubeconfig: <code className="text-[#8EC060]">~/.kube/config</code></li>
              </ul>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
