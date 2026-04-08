import { useMemo, useState } from 'react'
import { useReactTable, getCoreRowModel, getSortedRowModel, getFilteredRowModel, flexRender } from '@tanstack/react-table'
import { ArrowUpDown, ChevronUp, ChevronDown, Search } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatCurrency, formatDate, getProfitColor, cn } from '@/lib/utils'

export default function TradesTable({ trades, loading }) {
  const [sorting, setSorting] = useState([{ id: 'close_time', desc: true }])
  const [columnFilters, setColumnFilters] = useState([])
  const [globalFilter, setGlobalFilter] = useState('')

  const columns = useMemo(() => [
    {
      accessorKey: 'ticket_id',
      header: 'Ticket',
      size: 100,
    },
    {
      accessorKey: 'symbol',
      header: 'Symbol',
      size: 80,
      cell: ({ getValue }) => (
        <span className="font-mono font-semibold">{getValue()}</span>
      ),
    },
    {
      accessorKey: 'type',
      header: 'Type',
      size: 60,
      cell: ({ getValue }) => (
        <span
          className={cn(
            'px-2 py-0.5 rounded text-xs font-medium',
            getValue() === 'Buy'
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-coral-500/10 text-coral-400'
          )}
        >
          {getValue()}
        </span>
      ),
    },
    {
      accessorKey: 'lots',
      header: 'Lots',
      size: 60,
      cell: ({ getValue }) => <span>{getValue()?.toFixed(2)}</span>,
    },
    {
      accessorKey: 'open_time',
      header: 'Open Time',
      size: 140,
      cell: ({ getValue }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(getValue(), 'long')}
        </span>
      ),
    },
    {
      accessorKey: 'close_time',
      header: 'Close Time',
      size: 140,
      cell: ({ getValue }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(getValue(), 'long')}
        </span>
      ),
    },
    {
      accessorKey: 'open_price',
      header: 'Entry',
      size: 80,
      cell: ({ getValue }) => (
        <span className="font-mono">{getValue()?.toFixed(5)}</span>
      ),
    },
    {
      accessorKey: 'close_price',
      header: 'Exit',
      size: 80,
      cell: ({ getValue }) => (
        <span className="font-mono">{getValue()?.toFixed(5)}</span>
      ),
    },
    {
      accessorKey: 'profit_usd',
      header: 'Profit',
      size: 100,
      cell: ({ getValue }) => {
        const profit = getValue()
        return (
          <span className={cn('font-bold', getProfitColor(profit))}>
            {profit >= 0 ? '+' : ''}{formatCurrency(profit)}
          </span>
        )
      },
    },
    {
      accessorKey: 'magic_number',
      header: 'Magic',
      size: 80,
      cell: ({ getValue }) => (
        <span className="text-muted-foreground">
          {getValue() || '—'}
        </span>
      ),
    },
  ], [])

  const table = useReactTable({
    data: trades || [],
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-[400px]">
          <div className="animate-pulse text-muted-foreground">Loading trades...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-0">
        {/* Search */}
        <div className="p-4 border-b border-dashboard-border">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search trades..."
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-muted rounded-lg border border-dashboard-border focus:outline-none focus:ring-1 focus:ring-emerald-500 text-sm"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="border-b border-dashboard-border">
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider"
                      style={{ width: header.getSize() }}
                    >
                      {header.isPlaceholder ? null : (
                        <button
                          className="flex items-center space-x-1 hover:text-foreground transition-colors"
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
                          {header.column.getIsSorted() && (
                            header.column.getIsSorted() === 'asc' ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )
                          )}
                        </button>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-8 text-center text-muted-foreground">
                    No trades found
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-dashboard-border/50 hover:bg-muted/30 transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination info */}
        <div className="p-4 border-t border-dashboard-border text-sm text-muted-foreground">
          Showing {table.getRowModel().rows.length} of {trades?.length || 0} trades
        </div>
      </CardContent>
    </Card>
  )
}