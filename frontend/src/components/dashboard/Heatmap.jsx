import { useMemo } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { formatCurrency, cn } from '@/lib/utils'

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const WEEKS = 53 // ~1 year of weeks

export default function Heatmap({ data }) {
  const heatmapData = useMemo(() => {
    if (!data?.data) return []

    // Group by date
    const dateMap = new Map()
    data.data.forEach((item) => {
      dateMap.set(item.date, item.profit)
    })

    // Generate calendar grid
    const today = new Date()
    const grid = []

    // Start from 52 weeks ago
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - (WEEKS * 7))

    for (let week = 0; week < WEEKS; week++) {
      const weekData = []
      for (let day = 0; day < 7; day++) {
        const date = new Date(startDate)
        date.setDate(date.getDate() + (week * 7) + day)

        const dateStr = date.toISOString().split('T')[0]
        const profit = dateMap.get(dateStr) || 0

        weekData.push({
          date: dateStr,
          profit,
          dayOfWeek: day,
        })
      }
      grid.push(weekData)
    }

    return grid
  }, [data])

  const getIntensityColor = (profit) => {
    if (profit === 0) return 'bg-dashboard-border/30'
    if (profit > 0) {
      if (profit > 500) return 'bg-emerald-600'
      if (profit > 200) return 'bg-emerald-500'
      if (profit > 50) return 'bg-emerald-400'
      return 'bg-emerald-300'
    } else {
      const absLoss = Math.abs(profit)
      if (absLoss > 500) return 'bg-coral-600'
      if (absLoss > 200) return 'bg-coral-500'
      if (absLoss > 50) return 'bg-coral-400'
      return 'bg-coral-300'
    }
  }

  // Calculate stats
  const stats = useMemo(() => {
    if (!data?.data) return { bestDay: null, worstDay: null, avgProfit: 0 }

    const sorted = [...data.data].sort((a, b) => b.profit - a.profit)
    const bestDay = sorted[0]
    const worstDay = sorted[sorted.length - 1]
    const avgProfit = data.data.reduce((sum, d) => sum + d.profit, 0) / data.data.length

    return { bestDay, worstDay, avgProfit }
  }, [data])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Daily Performance Heatmap</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Day labels */}
          <div className="flex">
            <div className="w-8" />
            <div className="flex-1 text-xs text-muted-foreground">
              {stats.bestDay && (
                <div className="flex items-center space-x-2 mb-2">
                  <span>Best:</span>
                  <span className="text-emerald-400">
                    {formatCurrency(stats.bestDay.profit)} ({stats.bestDay.date})
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Heatmap grid */}
          <div className="flex overflow-x-auto pb-2">
            <div className="flex flex-col mr-2">
              {DAYS.map((day, i) => (
                <div key={day} className="h-3 flex items-center text-[10px] text-muted-foreground">
                  {i % 2 === 0 ? day : ''}
                </div>
              ))}
            </div>
            <div className="flex space-x-[2px]">
              {heatmapData.map((week, weekIdx) => (
                <div key={weekIdx} className="flex flex-col space-y-[2px]">
                  {week.map((day, dayIdx) => (
                    <div
                      key={`${weekIdx}-${dayIdx}`}
                      className={cn(
                        "w-3 h-3 rounded-sm",
                        getIntensityColor(day.profit)
                      )}
                      title={`${day.date}: ${formatCurrency(day.profit)}`}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-end space-x-2 text-xs text-muted-foreground mt-2">
            <span>Loss</span>
            <div className="flex space-x-1">
              <div className="w-3 h-3 rounded-sm bg-coral-300" />
              <div className="w-3 h-3 rounded-sm bg-coral-400" />
              <div className="w-3 h-3 rounded-sm bg-coral-500" />
              <div className="w-3 h-3 rounded-sm bg-coral-600" />
            </div>
            <div className="w-3 h-3 rounded-sm bg-dashboard-border/30" />
            <div className="flex space-x-1">
              <div className="w-3 h-3 rounded-sm bg-emerald-300" />
              <div className="w-3 h-3 rounded-sm bg-emerald-400" />
              <div className="w-3 h-3 rounded-sm bg-emerald-500" />
              <div className="w-3 h-3 rounded-sm bg-emerald-600" />
            </div>
            <span>Profit</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}