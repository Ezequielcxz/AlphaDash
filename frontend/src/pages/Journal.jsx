import { useState } from 'react'
import { useSelectedAccount, useTrades, useSymbols, useMagicNumbers } from '@/hooks'
import { TradesTable } from '@/components/journal'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RefreshCw, Filter, X } from 'lucide-react'

export default function Journal() {
  const { selectedAccount } = useSelectedAccount()
  const [filters, setFilters] = useState({
    symbol: null,
    magic_number: null,
    result_filter: null,
  })

  const { trades, loading, error, refetch } = useTrades({
    account_id: selectedAccount?.id,
    ...filters,
  })
  const { symbols } = useSymbols(selectedAccount?.id)
  const { magicNumbers } = useMagicNumbers(selectedAccount?.id)

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === 'all' ? null : value,
    }))
  }

  const clearFilters = () => {
    setFilters({
      symbol: null,
      magic_number: null,
      result_filter: null,
    })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v !== null)

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Trade Journal</h1>
          <p className="text-muted-foreground">
            Complete trade history with advanced filtering
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            {/* Symbol Filter */}
            <Select
              value={filters.symbol || 'all'}
              onValueChange={(v) => handleFilterChange('symbol', v)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Symbol" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Symbols</SelectItem>
                {symbols.map((symbol) => (
                  <SelectItem key={symbol} value={symbol}>
                    {symbol}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Strategy Filter */}
            <Select
              value={filters.magic_number || 'all'}
              onValueChange={(v) => handleFilterChange('magic_number', v)}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Strategy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Strategies</SelectItem>
                <SelectItem value="0">Manual/Unknown</SelectItem>
                {magicNumbers.filter((m) => m !== 0).map((magic) => (
                  <SelectItem key={magic} value={magic.toString()}>
                    Strategy #{magic}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Result Filter */}
            <Select
              value={filters.result_filter || 'all'}
              onValueChange={(v) => handleFilterChange('result_filter', v)}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Result" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Results</SelectItem>
                <SelectItem value="win">Winners</SelectItem>
                <SelectItem value="loss">Losers</SelectItem>
              </SelectContent>
            </Select>

            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="w-4 h-4 mr-1" />
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Trade Statistics */}
      {!loading && trades && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase">Total Trades</p>
              <p className="text-xl font-bold">{trades.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase">Winners</p>
              <p className="text-xl font-bold text-emerald-400">
                {trades.filter((t) => t.profit_usd > 0).length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase">Losers</p>
              <p className="text-xl font-bold text-coral-400">
                {trades.filter((t) => t.profit_usd < 0).length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase">Net P/L</p>
              <p
                className={`text-xl font-bold ${
                  trades.reduce((sum, t) => sum + t.profit_usd, 0) >= 0
                    ? 'text-emerald-400'
                    : 'text-coral-400'
                }`}
              >
                ${trades.reduce((sum, t) => sum + t.profit_usd, 0).toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trades Table */}
      <TradesTable trades={trades} loading={loading} />
    </div>
  )
}