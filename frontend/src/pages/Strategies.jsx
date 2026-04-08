import { useState, useMemo } from 'react'
import { useSelectedAccount, useMetrics } from '@/hooks'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { formatCurrency, formatNumber, getProfitColor, cn } from '@/lib/utils'
import { TrendingUp, TrendingDown, BarChart2, PieChart } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPie,
  Pie,
  Cell,
  Legend,
} from 'recharts'

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#06b6d4']

export default function Strategies() {
  const { selectedAccount } = useSelectedAccount()
  const { metrics, loading, refetch } = useMetrics(selectedAccount?.id)
  const [viewMode, setViewMode] = useState('table')

  const strategies = useMemo(() => metrics?.strategies || [], [metrics])

  const pieData = useMemo(() => {
    return strategies.map((s, index) => ({
      name: s.strategy_name,
      value: Math.abs(s.total_profit),
      profit: s.total_profit,
      fill: s.total_profit >= 0 ? '#10b981' : '#ef4444',
    }))
  }, [strategies])

  const barData = useMemo(() => {
    return strategies.slice(0, 10).map((s) => ({
      name: s.magic_number === 0 ? 'Manual' : `#${s.magic_number}`,
      profit: s.total_profit,
      trades: s.total_trades,
      winRate: s.win_rate,
    }))
  }, [strategies])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-pulse text-muted-foreground">Loading strategies...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Strategies Analysis</h1>
        <p className="text-muted-foreground">
          {strategies.length} strategies detected via Magic Numbers
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Active Strategies</span>
            </div>
            <p className="text-2xl font-bold mt-2">{strategies.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <span className="text-sm text-muted-foreground">Profitable</span>
            </div>
            <p className="text-2xl font-bold mt-2 text-emerald-400">
              {strategies.filter((s) => s.total_profit > 0).length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-5 h-5 text-coral-400" />
              <span className="text-sm text-muted-foreground">Unprofitable</span>
            </div>
            <p className="text-2xl font-bold mt-2 text-coral-400">
              {strategies.filter((s) => s.total_profit < 0).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Profit by Strategy</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2530" />
                <XAxis dataKey="name" stroke="#6b7280" tick={{ fontSize: 11 }} />
                <YAxis stroke="#6b7280" tickFormatter={(v) => formatCurrency(v)} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12161a',
                    border: '1px solid #1e2530',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => [formatCurrency(value), 'Profit']}
                />
                <Bar
                  dataKey="profit"
                  fill="#10b981"
                  radius={[4, 4, 0, 0]}
                >
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.profit >= 0 ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Win Rate by Strategy</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2530" />
                <XAxis dataKey="name" stroke="#6b7280" tick={{ fontSize: 11 }} />
                <YAxis stroke="#6b7280" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#12161a',
                    border: '1px solid #1e2530',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => [`${value.toFixed(1)}%`, 'Win Rate']}
                />
                <Bar dataKey="winRate" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Strategies Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Strategies</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dashboard-border">
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                    Strategy
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                    Trades
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                    Win Rate
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                    Profit Factor
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                    Total Profit
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">
                    Symbols
                  </th>
                </tr>
              </thead>
              <tbody>
                {strategies.map((strategy) => (
                  <tr
                    key={strategy.magic_number}
                    className="border-b border-dashboard-border/50 hover:bg-muted/30"
                  >
                    <td className="px-4 py-3">
                      <span className="font-medium">{strategy.strategy_name}</span>
                      {strategy.magic_number !== 0 && (
                        <span className="text-xs text-muted-foreground ml-2">
                          #{strategy.magic_number}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 tabular-nums">{strategy.total_trades}</td>
                    <td className="px-4 py-3 tabular-nums">
                      <span
                        className={cn(
                          strategy.win_rate >= 50 ? 'text-emerald-400' : 'text-coral-400'
                        )}
                      >
                        {strategy.win_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 tabular-nums">
                      <span
                        className={cn(
                          strategy.profit_factor >= 1.5 ? 'text-emerald-400' :
                          strategy.profit_factor >= 1 ? 'text-yellow-400' : 'text-coral-400'
                        )}
                      >
                        {strategy.profit_factor.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn('font-bold tabular-nums', getProfitColor(strategy.total_profit))}>
                        {formatCurrency(strategy.total_profit)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {strategy.symbols.slice(0, 3).map((symbol) => (
                          <span
                            key={symbol}
                            className="px-2 py-0.5 bg-muted rounded text-xs"
                          >
                            {symbol}
                          </span>
                        ))}
                        {strategy.symbols.length > 3 && (
                          <span className="text-xs text-muted-foreground">
                            +{strategy.symbols.length - 3} more
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}