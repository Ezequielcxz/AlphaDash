import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { syncApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import {
  Link2,
  Unlink2,
  RefreshCw,
  Download,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'

const CREDS_KEY = 'mt5_last_credentials'

export default function MT5Connect() {
  const navigate = useNavigate()

  // Restore login+server from localStorage (never password)
  const savedCreds = (() => {
    try { return JSON.parse(localStorage.getItem(CREDS_KEY) || '{}') } catch { return {} }
  })()

  const [credentials, setCredentials] = useState({
    login: savedCreds.login || '',
    password: '',
    server: savedCreds.server || '',
  })
  const [daysBack, setDaysBack] = useState(30)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState(null)
  const [syncResult, setSyncResult] = useState(null)
  const [error, setError] = useState(null)

  // MT5 terminal detection
  const [terminals, setTerminals] = useState([])
  const [selectedTerminalPath, setSelectedTerminalPath] = useState(savedCreds.path || '')

  // On mount: check connection status + detect running MT5 terminals
  useEffect(() => {
    const init = async () => {
      // 1. Check if backend is still connected
      try {
        const response = await syncApi.status()
        if (response.data?.connected) {
          setConnectionStatus(response.data)
          setCredentials(prev => ({
            ...prev,
            login: String(response.data.login || prev.login),
            server: response.data.server || prev.server,
          }))
        }
      } catch { /* backend unreachable */ }

      // 2. Detect running MT5 terminals
      try {
        const res = await syncApi.terminals()
        setTerminals(res.data || [])
        // Auto-select first terminal if nothing saved
        if (res.data?.length > 0 && !selectedTerminalPath) {
          setSelectedTerminalPath(res.data[0].path)
        }
      } catch { /* psutil not available */ }

      setLoading(false)
    }
    init()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleConnect = async () => {
    setLoading(true)
    setError(null)
    setConnectionStatus(null)

    try {
      const response = await syncApi.connect({
        login: parseInt(credentials.login),
        password: credentials.password,
        server: credentials.server,
        path: selectedTerminalPath || null,
      })

      setConnectionStatus(response.data)

      if (response.data?.connected) {
        localStorage.setItem(CREDS_KEY, JSON.stringify({
          login: credentials.login,
          server: credentials.server,
          path: selectedTerminalPath || null,
        }))
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Connection failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    setError(null)
    setSyncResult(null)

    try {
      const response = await syncApi.history({
        login: parseInt(credentials.login),
        password: credentials.password,
        server: credentials.server,
        days_back: daysBack,
        path: selectedTerminalPath || null,
      })

      const result = response.data
      setSyncResult(result)

      if (result.success && result.new_trades > 0 && result.account_id) {
        const saved = localStorage.getItem('selectedAccount')
        if (!saved) {
          localStorage.setItem('selectedAccount', JSON.stringify({
            id: result.account_id,
            account_number: parseInt(credentials.login),
            server: credentials.server
          }))
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  const handleDisconnect = async () => {
    try {
      await syncApi.disconnect()
      setConnectionStatus(null)
      setSyncResult(null)
      localStorage.removeItem(CREDS_KEY)
    } catch (err) {
      console.error('Disconnect error:', err)
    }
  }


  const isConnected = connectionStatus?.connected

  // Show spinner while we check initial connection status from backend
  if (loading && !connectionStatus) {
    return (
      <div className="flex items-center justify-center h-[40vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Connect MT5 Account</h1>
        <p className="text-muted-foreground mt-1">
          Enter your MT5 credentials to sync trade history
        </p>
      </div>

      {/* Connection Status Card */}
      {connectionStatus && (
        <Card className={cn(
          "border-2",
          isConnected ? "border-emerald-500/30" : "border-coral-500/30"
        )}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {isConnected ? (
                  <CheckCircle className="w-6 h-6 text-emerald-400" />
                ) : (
                  <XCircle className="w-6 h-6 text-coral-400" />
                )}
                <div>
                  <p className="font-medium">
                    {isConnected ? 'Connected' : 'Connection Failed'}
                  </p>
                  {isConnected && (
                    <p className="text-sm text-muted-foreground">
                      Account: {connectionStatus.login} @ {connectionStatus.server}
                    </p>
                  )}
                </div>
              </div>
              {isConnected && (
                <Button variant="outline" size="sm" onClick={handleDisconnect}>
                  <Unlink2 className="w-4 h-4 mr-2" />
                  Disconnect
                </Button>
              )}
            </div>

            {isConnected && (
              <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-dashboard-border">
                <div>
                  <p className="text-xs text-muted-foreground">Balance</p>
                  <p className="text-lg font-bold text-emerald-400">
                    ${connectionStatus.balance?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Equity</p>
                  <p className="text-lg font-bold">
                    ${connectionStatus.equity?.toLocaleString()}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Terminal Selector - only shown when multiple MT5 installs exist */}
      {terminals.length > 0 && (
        <Card className={cn(
          "border-2",
          terminals.length > 1 ? "border-yellow-500/40" : "border-dashboard-border"
        )}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center text-base">
              {terminals.length > 1 ? (
                <AlertCircle className="w-4 h-4 mr-2 text-yellow-400" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2 text-emerald-400" />
              )}
              {terminals.length > 1
                ? `${terminals.length} MT5 Terminals Detected — Choose One`
                : 'MT5 Terminal Detected'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 pt-0">
            {terminals.length > 1 && (
              <p className="text-xs text-yellow-400/80 mb-3">
                Multiple MT5 terminals are running. Select the one with your Vantage account logged in.
              </p>
            )}
            {terminals.map((t) => (
              <label
                key={t.path}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                  selectedTerminalPath === t.path
                    ? "border-emerald-500/50 bg-emerald-500/10"
                    : "border-dashboard-border hover:border-emerald-500/30"
                )}
              >
                <input
                  type="radio"
                  name="terminal"
                  value={t.path}
                  checked={selectedTerminalPath === t.path}
                  onChange={() => setSelectedTerminalPath(t.path)}
                  className="mt-0.5"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{t.name}</p>
                  <p className="text-xs text-muted-foreground truncate" title={t.path}>{t.path}</p>
                </div>
              </label>
            ))}
          </CardContent>
        </Card>
      )}

      {terminals.length === 0 && !isConnected && (
        <Card className="border-yellow-500/30">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-300">No MT5 terminal detected</p>
              <p className="text-xs text-muted-foreground mt-1">
                Open MetaTrader 5 and log in to your account before connecting.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Credentials Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Link2 className="w-5 h-5 mr-2" />
            MT5 Credentials
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Account Number (Login)
              </label>
              <input
                type="text"
                value={credentials.login}
                onChange={(e) => setCredentials({ ...credentials, login: e.target.value })}
                className="w-full mt-1 px-4 py-2 bg-muted rounded-lg border border-dashboard-border focus:outline-none focus:ring-1 focus:ring-emerald-500"
                placeholder="12345678"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Server
              </label>
              <input
                type="text"
                value={credentials.server}
                onChange={(e) => setCredentials({ ...credentials, server: e.target.value })}
                className="w-full mt-1 px-4 py-2 bg-muted rounded-lg border border-dashboard-border focus:outline-none focus:ring-1 focus:ring-emerald-500"
                placeholder="BrokerName-Live"
              />
            </div>

          </div>

          <div>
            <label className="text-sm font-medium text-muted-foreground">
              Password
            </label>
            <div className="relative mt-1">
              <input
                type={showPassword ? 'text' : 'password'}
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                className="w-full px-4 py-2 bg-muted rounded-lg border border-dashboard-border focus:outline-none focus:ring-1 focus:ring-emerald-500 pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Button
              onClick={handleConnect}
              disabled={loading || !credentials.login || !credentials.password || !credentials.server}
              className="flex-1"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Link2 className="w-4 h-4 mr-2" />
              )}
              {loading ? 'Connecting...' : 'Connect'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Sync Options */}
      {isConnected && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Download className="w-5 h-5 mr-2" />
              Sync Trade History
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Days to sync
              </label>
              <select
                value={daysBack}
                onChange={(e) => setDaysBack(parseInt(e.target.value))}
                className="w-full mt-1 px-4 py-2 bg-muted rounded-lg border border-dashboard-border focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 180 days</option>
                <option value={365}>Last year</option>
              </select>
            </div>

            <Button
              onClick={handleSync}
              disabled={syncing}
              variant="secondary"
              className="w-full"
            >
              {syncing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              {syncing ? 'Syncing...' : 'Sync Now'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Sync Result */}
      {syncResult && (
        <Card className={cn(
          syncResult.success ? "border-emerald-500/30" : "border-coral-500/30"
        )}>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3 mb-4">
              {syncResult.success ? (
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              ) : (
                <AlertCircle className="w-6 h-6 text-coral-400" />
              )}
              <p className="font-medium">
                {syncResult.success ? 'Sync Completed' : 'Sync Failed'}
              </p>
            </div>

            {syncResult.success && (
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Total Trades</p>
                  <p className="text-xl font-bold">{syncResult.total_trades}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">New Trades Imported</p>
                  <p className="text-xl font-bold text-emerald-400">{syncResult.new_trades}</p>
                </div>
              </div>
            )}

            {syncResult.errors?.length > 0 && (
              <div className="mt-4 p-3 rounded-lg bg-coral-500/10 space-y-1">
                <p className="text-sm font-medium text-coral-400">
                  {syncResult.errors.length} warning(s):
                </p>
                {syncResult.errors.map((err, i) => (
                  <p key={i} className="text-xs text-muted-foreground">{err}</p>
                ))}
              </div>
            )}

            {syncResult.success && syncResult.new_trades > 0 && (
              <Button
                onClick={() => navigate('/')}
                className="w-full mt-4"
              >
                View Dashboard
              </Button>
            )}

            {syncResult.success && syncResult.total_trades === 0 && (
              <div className="mt-4 p-3 rounded-lg bg-yellow-500/10">
                <p className="text-sm text-yellow-400">
                  💡 No closed trades found in the last {daysBack} days. Try increasing the date range or ensure MT5 terminal is open and logged in.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Card className="border-coral-500/30">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-coral-400" />
              <p className="text-coral-400">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info */}
      <Card className="bg-muted/30">
        <CardContent className="p-4 text-sm text-muted-foreground">
          <p className="font-medium mb-2">Requirements:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>MetaTrader 5 terminal must be installed and running</li>
            <li>The terminal must be logged into the account you want to sync</li>
            <li>Python with MetaTrader5 library installed on the server</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}