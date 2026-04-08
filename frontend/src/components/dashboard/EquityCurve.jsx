import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function EquityCurve({ data }) {
  const chartData = useMemo(() => {
    if (!data?.dates) return []

    return data.dates.map((date, index) => ({
      date,
      equity: data.equity[index],
      drawdown: data.drawdown[index],
    }))
  }, [data])

  if (!chartData.length) {
    return (
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Equity Curve</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px] flex items-center justify-center">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    )
  }

  const minEquity = Math.min(...chartData.map((d) => d.equity))
  const maxEquity = Math.max(...chartData.map((d) => d.equity))
  const startEquity = chartData[0]?.equity || 0
  const endEquity = chartData[chartData.length - 1]?.equity || 0
  const profit = endEquity - startEquity
  const profitPercent = startEquity > 0 ? ((endEquity - startEquity) / startEquity) * 100 : 0

  return (
    <Card className="col-span-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Equity Curve</CardTitle>
        <div className="flex items-center space-x-4 text-sm">
          <div className="text-right">
            <p className="text-muted-foreground">Total Return</p>
            <p className={profit >= 0 ? 'text-emerald-400 font-bold' : 'text-coral-400 font-bold'}>
              {profit >= 0 ? '+' : ''}{formatCurrency(profit)} ({profitPercent.toFixed(1)}%)
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2530" />
            <XAxis
              dataKey="date"
              stroke="#6b7280"
              tickFormatter={(value) => formatDate(value, 'short')}
              tick={{ fontSize: 11 }}
            />
            <YAxis
              stroke="#6b7280"
              tickFormatter={(value) => formatCurrency(value)}
              domain={[minEquity * 0.95, maxEquity * 1.05]}
              tick={{ fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#12161a',
                border: '1px solid #1e2530',
                borderRadius: '8px',
              }}
              labelFormatter={(label) => formatDate(label, 'long')}
              formatter={(value) => [formatCurrency(value), 'Equity']}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}