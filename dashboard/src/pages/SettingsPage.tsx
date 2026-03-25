import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Save,
  RefreshCw,
  AlertTriangle,
  Slack,
  MessageSquare,
  Mail,
  Send,
  Phone,
  Globe,
  Bell,
  Key,
  FileText,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Info
} from 'lucide-react'

type Tab = 'cluster' | 'llm' | 'alerting' | 'general'

const llmProviders = [
  { id: 'openai', name: 'OpenAI', logo: 'https://upload.wikimedia.org/wikipedia/commons/4/4d/OpenAI_Logo.svg' },
  { id: 'anthropic', name: 'Anthropic', logo: 'https://upload.wikimedia.org/wikipedia/commons/7/78/Anthropic_Logo.svg' },
  { id: 'gemini', name: 'Google Gemini', logo: 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Google_Gemini_logo.svg' },
  { id: 'azure', name: 'Azure OpenAI', logo: 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Microsoft_Azure.svg' },
  { id: 'ollama', name: 'Ollama', logo: '' },
  { id: 'local', name: 'Local Model', logo: '' },
]

const alertChannels = [
  { id: 'slack', name: 'Slack', icon: Slack, color: 'bg-[#4A154B]' },
  { id: 'teams', name: 'Microsoft Teams', icon: MessageSquare, color: 'bg-[#5059C9]' },
  { id: 'telegram', name: 'Telegram', icon: Send, color: 'bg-[#229ED9]' },
  { id: 'email', name: 'Email', icon: Mail, color: 'bg-red-500' },
  { id: 'sms', name: 'SMS (Twilio)', icon: Phone, color: 'bg-[#F22F46]' },
  { id: 'webhook', name: 'Custom Webhook', icon: Globe, color: 'bg-purple-500' },
  { id: 'grafana', name: 'Grafana', icon: Bell, color: 'bg-[#F46800]' },
  { id: 'prometheus', name: 'Prometheus', icon: Bell, color: 'bg-[#E6522C]' },
  { id: 'pagerduty', name: 'PagerDuty', icon: Bell, color: 'bg-[#06AC38]' },
  { id: 'opsgenie', name: 'OpsGenie', icon: Bell, color: 'bg-[#FFFFFF]' },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('cluster')
  const [kubeconfigPath, setKubeconfigPath] = useState('/etc/rancher/k3s/k3s.yaml')
  const [selectedProvider, setSelectedProvider] = useState('openai')
  const [apiKey, setApiKey] = useState('')
  const [enabledChannels, setEnabledChannels] = useState<string[]>(['slack'])
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle')

  const handleSave = async () => {
    setIsSaving(true)
    setSaveStatus('idle')

    // Simulate save
    await new Promise(resolve => setTimeout(resolve, 1500))

    setIsSaving(false)
    setSaveStatus('success')
    setTimeout(() => setSaveStatus('idle'), 3000)
  }

  const toggleChannel = (channelId: string) => {
    setEnabledChannels(prev =>
      prev.includes(channelId)
        ? prev.filter(c => c !== channelId)
        : [...prev, channelId]
    )
  }

  const tabs = [
    { id: 'cluster', label: 'Cluster', icon: FileText },
    { id: 'llm', label: 'LLM Provider', icon: Key },
    { id: 'alerting', label: 'Alerting', icon: Bell },
    { id: 'general', label: 'General', icon: Settings },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 text-sm mt-1">Configure K3s Sentinel settings</p>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-2 border-b border-slate-700/50 pb-4"
      >
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as Tab)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                : 'bg-slate-700/30 text-slate-400 hover:text-white border border-transparent hover:bg-slate-700/50'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </motion.div>

      {/* Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2 }}
        className="bg-slate-800/40 border border-slate-700/30 rounded-2xl p-6"
      >
        {/* Cluster Settings */}
        {activeTab === 'cluster' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white mb-1">Cluster Configuration</h3>
              <p className="text-slate-400 text-sm">Configure kubeconfig path and cluster connection</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Kubeconfig Path
                </label>
                <input
                  type="text"
                  value={kubeconfigPath}
                  onChange={(e) => setKubeconfigPath(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all"
                  placeholder="/etc/rancher/k3s/k3s.yaml"
                />
                <p className="text-xs text-slate-500 mt-2">
                  Path to the kubeconfig file for cluster authentication
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Context Name
                  </label>
                  <input
                    type="text"
                    defaultValue="default"
                    className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Namespace
                  </label>
                  <input
                    type="text"
                    defaultValue="default"
                    className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all"
                  />
                </div>
              </div>

              <div className="flex items-center gap-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                <Info className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <div>
                  <p className="text-blue-400 text-sm font-medium">K3s Default Path</p>
                  <p className="text-slate-400 text-xs mt-0.5">
                    For single-node K3s installations, the kubeconfig is typically at /etc/rancher/k3s/k3s.yaml
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* LLM Provider Settings */}
        {activeTab === 'llm' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white mb-1">LLM Provider</h3>
              <p className="text-slate-400 text-sm">Configure AI provider for root cause analysis</p>
            </div>

            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Select Provider
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {llmProviders.map(provider => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    className={`flex items-center gap-3 p-4 rounded-xl border transition-all ${
                      selectedProvider === provider.id
                        ? 'bg-indigo-500/20 border-indigo-500/50'
                        : 'bg-slate-700/30 border-slate-600/30 hover:border-slate-500/50'
                    }`}
                  >
                    {provider.logo ? (
                      <img src={provider.logo} alt={provider.name} className="w-6 h-6 rounded" />
                    ) : (
                      <div className="w-6 h-6 bg-slate-600 rounded flex items-center justify-center">
                        <Key className="w-3 h-3 text-white" />
                      </div>
                    )}
                    <span className="text-sm text-white font-medium">{provider.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* API Key */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all"
                placeholder="Enter your API key"
              />
              <p className="text-xs text-slate-500 mt-2">
                API key will be stored securely and encrypted
              </p>
            </div>

            {/* Model Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Model
                </label>
                <select className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white focus:outline-none focus:border-indigo-500/50 transition-all">
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Temperature
                </label>
                <input
                  type="number"
                  defaultValue={0.7}
                  min={0}
                  max={2}
                  step={0.1}
                  className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white focus:outline-none focus:border-indigo-500/50 transition-all"
                />
              </div>
            </div>
          </div>
        )}

        {/* Alerting Settings */}
        {activeTab === 'alerting' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white mb-1">Alerting Channels</h3>
              <p className="text-slate-400 text-sm">Configure notification channels for alerts</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {alertChannels.map(channel => {
                const Icon = channel.icon
                const isEnabled = enabledChannels.includes(channel.id)

                return (
                  <button
                    key={channel.id}
                    onClick={() => toggleChannel(channel.id)}
                    className={`flex items-center justify-between p-4 rounded-xl border transition-all ${
                      isEnabled
                        ? 'bg-indigo-500/20 border-indigo-500/50'
                        : 'bg-slate-700/30 border-slate-600/30 hover:border-slate-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${channel.color}`}>
                        <Icon className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-white font-medium">{channel.name}</span>
                    </div>
                    <div className={`w-10 h-6 rounded-full transition-colors ${
                      isEnabled ? 'bg-indigo-500' : 'bg-slate-600'
                    }`}>
                      <div className={`w-4 h-4 bg-white rounded-full mt-1 transition-transform ${
                        isEnabled ? 'translate-x-5' : 'translate-x-1'
                      }`} />
                    </div>
                  </button>
                )
              })}
            </div>

            {enabledChannels.length > 0 && (
              <div className="pt-4 border-t border-slate-700/50">
                <h4 className="text-sm font-medium text-slate-300 mb-3">Channel Configuration</h4>
                <div className="space-y-3">
                  {enabledChannels.includes('slack') && (
                    <div className="p-4 bg-slate-700/30 rounded-xl">
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Slack Webhook URL
                      </label>
                      <input
                        type="text"
                        className="w-full px-4 py-2.5 bg-slate-800/50 border border-slate-600/30 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all"
                        placeholder="https://hooks.slack.com/services/..."
                      />
                    </div>
                  )}
                  {enabledChannels.includes('email') && (
                    <div className="p-4 bg-slate-700/30 rounded-xl">
                      <label className="block text-sm font-medium text-slate-300 mb-2">
                        Email Recipients
                      </label>
                      <input
                        type="text"
                        className="w-full px-4 py-2.5 bg-slate-800/50 border border-slate-600/30 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 transition-all"
                        placeholder="admin@example.com, ops@example.com"
                      />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* General Settings */}
        {activeTab === 'general' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white mb-1">General Settings</h3>
              <p className="text-slate-400 text-sm">Configure general application settings</p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-xl">
                <div>
                  <p className="text-white font-medium">Auto-refresh Data</p>
                  <p className="text-slate-400 text-sm">Automatically refresh cluster data</p>
                </div>
                <div className="w-10 h-6 bg-indigo-500 rounded-full">
                  <div className="w-4 h-4 bg-white rounded-full mt-1 translate-x-5" />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-xl">
                <div>
                  <p className="text-white font-medium">Enable RCA</p>
                  <p className="text-slate-400 text-sm">Enable AI-powered root cause analysis</p>
                </div>
                <div className="w-10 h-6 bg-indigo-500 rounded-full">
                  <div className="w-4 h-4 bg-white rounded-full mt-1 translate-x-5" />
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-xl">
                <div>
                  <p className="text-white font-medium">Dark Mode</p>
                  <p className="text-slate-400 text-sm">Enable dark theme</p>
                </div>
                <div className="w-10 h-6 bg-indigo-500 rounded-full">
                  <div className="w-4 h-4 bg-white rounded-full mt-1 translate-x-5" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Refresh Interval (seconds)
                </label>
                <input
                  type="number"
                  defaultValue={30}
                  min={10}
                  max={300}
                  className="w-full px-4 py-3 bg-slate-700/30 border border-slate-600/30 rounded-xl text-white focus:outline-none focus:border-indigo-500/50 transition-all"
                />
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Save Button */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-end gap-4"
      >
        {saveStatus === 'success' && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2 text-emerald-400"
          >
            <CheckCircle2 className="w-5 h-5" />
            <span className="text-sm">Settings saved successfully</span>
          </motion.div>
        )}

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-500 hover:bg-indigo-600 disabled:bg-indigo-500/50 text-white rounded-xl font-medium transition-colors"
        >
          {isSaving ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {isSaving ? 'Saving...' : 'Save Settings'}
        </motion.button>
      </motion.div>
    </div>
  )
}
