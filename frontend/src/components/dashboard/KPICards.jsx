import {
  TrendingUp,
  TrendingDown,
  Target,
  Percent,
  BarChart2,
  DollarSign,
  Activity,
  Award,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { formatCurrency, formatNumber, formatPercent, getProfitColor, cn } from '@/lib/utils'

const kpiConfig = [
  {
    key: 'net_profit',
    label: 'Net Profit',
    icon: DollarSign,
    format: 'currency',
    color: 'profit',
  },
  {
    key: 'win_rate',
    label: 'Win Rate',
    icon: Percent,
    format: 'percent',
    suffix: '%',
  },
  {
    key: 'profit_factor',
    label: 'Profit Factor',
    icon: TrendingUp,
    format: 'number',
    decimals: 2,
  },
  {
    key: 'total_trades',
    label: 'Total Trades',
    icon: BarChart2,
    format: 'number',
    decimals: 0,
  },
  {
    key: 'expectancy',
    label: 'Expectancy',
    icon: Target,
    format: 'currency',
  },
  {
    key: 'recovery_factor',
    label: 'Recovery Factor',
    icon: Activity,
    format: 'number',
    decimals: 2,
  },
]

function KPICard({ label, value, icon: Icon, format, decimals, suffix }) {
  const formattedValue = (() => {
    switch (format) {
      case 'currency':
        return formatCurrency(value || 0)
      case 'percent':
        return `${(value || 0).toFixed(1)}%`
      default:
        return formatNumber(value || 0, decimals || 2)
    }
  })()

  const isProfitMetric = label.includes('Profit') || label.includes('Expectancy')
  const colorClass = isProfitMetric ? getProfitColor(value || 0) : 'text-foreground'

  return (
    <Card className="hover:border-emerald-500/30 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">
              {label}
            </p>
            <p className={cn("text-2xl font-bold tabular-nums", colorClass)}>
              {formattedValue}
              {suffix && <span className="text-sm ml-1">{suffix}</span>}
            </p>
          </div>
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center",
            isProfitMetric && value > 0 ? "bg-emerald-500/10" : isProfitMetric && value < 0 ? "bg-coral-500/10" : "bg-muted"
          )}>
            <Icon className={cn(
              "w-5 h-5",
              isProfitMetric && value > 0 ? "text-emerald-400" : isProfitMetric && value < 0 ? "text-coral-400" : "text-muted-foreground"
            )} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function KPICards({ metrics }) {
  if (!metrics?.core) return null

  const { core } = metrics

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {kpiConfig.map((kpi) => (
        <KPICard
          key={kpi.key}
          label={kpi.label}
          value={core[kpi.key]}
          icon={kpi.icon}
          format={kpi.format}
          decimals={kpi.decimals}
          suffix={kpi.suffix}
        />
      ))}
    </div>
  )
}