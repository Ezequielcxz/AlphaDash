import { TrendingUp, TrendingDown, BarChart2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { formatCurrency, formatNumber, formatPercent, getProfitColor, cn } from '@/lib/utils'

export default function StrategiesList({ strategies }) {
  if (!strategies?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Strategies</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[200px]">
          <p className="text-muted-foreground">No strategy data available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Strategies by Magic Number</CardTitle>
        <Link
          to="/strategies"
          className="text-sm text-emerald-400 hover:text-emerald-300"
        >
          View All →
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {strategies.slice(0, 5).map((strategy) => (
            <div
              key={strategy.magic_number}
              className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium">{strategy.strategy_name}</span>
                  <span className="text-xs text-muted-foreground">
                    (#{strategy.magic_number})
                  </span>
                </div>
                <div className="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                  <span>{strategy.total_trades} trades</span>
                  <span>{strategy.win_rate.toFixed(1)}% win</span>
                  <span>PF: {strategy.profit_factor.toFixed(2)}</span>
                </div>
              </div>
              <div className="text-right">
                <p className={cn("font-bold", getProfitColor(strategy.total_profit))}>
                  {formatCurrency(strategy.total_profit)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {strategy.symbols.length} symbols
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}