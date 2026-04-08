import { useState, useCallback } from 'react'
import { useSelectedAccount, useMetrics, useEquityCurve, useHeatmap } from '@/hooks'
import { KPICards, EquityCurve, Heatmap, StrategiesList, RiskMetrics, DailyCalendar } from '@/components/dashboard'
import { Card, CardContent } from '@/components/ui/card'
import { RefreshCw, AlertCircle, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'

const PERIOD_OPTIONS = [
  { label: 'Last Day',      value: 1 },
  { label: 'Last 3 Days',   value: 3 },
  { label: 'Last Week',     value: 7 },
  { label: 'Last Month',    value: 30 },
  { label: 'Last 3 Months', value: 90 },
  { label: 'Last Year',     value: 365 },
  { label: 'All Time',      value: null },
]

export default function Dashboard() {
  const { selectedAccount } = useSelectedAccount()
  const [activePeriod, setActivePeriod] = useState(null) // null = All Time

  const { metrics, loading: metricsLoading, error: metricsError, refetch } = useMetrics(
    selectedAccount?.id,
    activePeriod
  )
  const { data: equityData, loading: equityLoading } = useEquityCurve(selectedAccount?.id, activePeriod)
  const { data: heatmapData, loading: heatmapLoading } = useHeatmap(selectedAccount?.id, activePeriod)

  const handlePeriodChange = useCallback((value) => {
    setActivePeriod(value)
  }, [])

  if (metricsError) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <AlertCircle className="w-12 h-12 text-coral-400 mx-auto mb-4" />
            <h2 className="text-lg font-semibold mb-2">Error Loading Data</h2>
            <p className="text-muted-foreground mb-4">{metricsError}</p>
            <Button onClick={refetch}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">
            {selectedAccount
              ? selectedAccount.alias_personalizado || `Account ${selectedAccount.account_number}`
              : 'Global Portfolio'}
          </h1>
          <p className="text-muted-foreground">
            {selectedAccount?.broker_name || 'All accounts combined'}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Period Filter */}
          <div className="flex items-center gap-1 bg-muted/50 p-1 rounded-xl border border-dashboard-border">
            <Calendar className="w-3.5 h-3.5 text-muted-foreground ml-2 mr-1 flex-shrink-0" />
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={String(opt.value)}
                onClick={() => handlePeriodChange(opt.value)}
                className={`
                  px-3 py-1 rounded-lg text-xs font-medium transition-all duration-200
                  ${activePeriod === opt.value
                    ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-500/30'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'}
                `}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={refetch} disabled={metricsLoading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${metricsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      {metricsLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="h-16 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <KPICards metrics={metrics} />
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {equityLoading ? (
          <Card className="col-span-2">
            <CardContent className="h-[300px] flex items-center justify-center">
              <div className="h-full w-full bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ) : (
          <EquityCurve data={equityData} />
        )}
        {heatmapLoading ? (
          <Card>
            <CardContent className="h-[300px] flex items-center justify-center">
              <div className="h-full w-full bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ) : (
          <Heatmap data={heatmapData} />
        )}
      </div>

      {/* Risk Metrics */}
      {metrics && !metricsLoading && <RiskMetrics metrics={metrics} />}

      {/* Daily Profit Calendar */}
      {metrics?.temporal?.calendar && !metricsLoading && (
        <DailyCalendar data={metrics.temporal.calendar} loading={metricsLoading} />
      )}

      {/* Strategies Preview */}
      {metrics?.strategies && !metricsLoading && (
        <StrategiesList strategies={metrics.strategies} />
      )}
    </div>
  )
}