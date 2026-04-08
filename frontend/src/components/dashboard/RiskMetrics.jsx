import { Activity, TrendingDown, Zap, Clock } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { formatCurrency, formatNumber, getProfitColor, cn } from '@/lib/utils'

const riskMetrics = [
  {
    key: 'max_drawdown_usd',
    label: 'Max Drawdown',
    sublabel: 'USD',
    icon: TrendingDown,
    format: 'currency',
    invertColor: true,
  },
  {
    key: 'max_drawdown_pct',
    label: 'Max Drawdown',
    sublabel: '%',
    icon: TrendingDown,
    format: 'percent',
    invertColor: true,
  },
  {
    key: 'sharpe_ratio',
    label: 'Sharpe Ratio',
    icon: Activity,
    format: 'number',
    decimals: 2,
  },
  {
    key: 'sortino_ratio',
    label: 'Sortino Ratio',
    icon: Activity,
    format: 'number',
    decimals: 2,
  },
  {
    key: 'max_consecutive_wins',
    label: 'Max Consecutive Wins',
    icon: Zap,
    format: 'number',
    decimals: 0,
  },
  {
    key: 'max_consecutive_losses',
    label: 'Max Consecutive Losses',
    icon: TrendingDown,
    format: 'number',
    decimals: 0,
  },
  {
    key: 'avg_trade_duration_hours',
    label: 'Avg Trade Duration',
    sublabel: 'hours',
    icon: Clock,
    format: 'number',
    decimals: 1,
  },
]

export default function RiskMetrics({ metrics }) {
  if (!metrics?.risk) return null

  const { risk } = metrics

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {riskMetrics.map((metric) => {
            const Icon = metric.icon
            const value = risk[metric.key] || 0

            const formattedValue = metric.format === 'currency'
              ? formatCurrency(value)
              : metric.format === 'percent'
              ? `${Math.abs(value).toFixed(1)}%`
              : formatNumber(value, metric.decimals || 0)

            const isNegativeGood = metric.invertColor
            const colorClass = isNegativeGood
              ? value < 0 ? 'text-emerald-400' : 'text-coral-400'
              : getProfitColor(value)

            return (
              <div key={metric.key} className="p-3 rounded-lg bg-muted/50">
                <div className="flex items-center space-x-2 mb-1">
                  <Icon className="w-4 h-4 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{metric.label}</span>
                </div>
                <p className={cn("text-lg font-bold tabular-nums", colorClass)}>
                  {formattedValue}
                </p>
                {metric.sublabel && (
                  <p className="text-xs text-muted-foreground">{metric.sublabel}</p>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}