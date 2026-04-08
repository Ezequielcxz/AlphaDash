import React, { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import { 
  format, 
  addMonths, 
  subMonths, 
  startOfMonth, 
  endOfMonth, 
  startOfWeek, 
  endOfWeek, 
  isSameMonth, 
  isSameDay, 
  addDays, 
  parseISO 
} from 'date-fns';
import { Button } from '@/components/ui/button';

export function DailyCalendar({ data = [], loading = false }) {
  // data is expected to be an array: [{ date: 'YYYY-MM-DD', profit: -14.8, trades: 2 }]
  
  // Default to current month, unless there's data, then default to the latest data month
  const initialDate = data && data.length > 0 
    ? parseISO(data[data.length - 1].date)
    : new Date();

  const [currentMonth, setCurrentMonth] = useState(startOfMonth(initialDate));

  const prevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const nextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));

  // Map data to a fast lookup dictionary by YYYY-MM-DD
  const dataMap = useMemo(() => {
    const map = {};
    if (!data) return map;
    data.forEach(d => {
      map[d.date] = d;
    });
    return map;
  }, [data]);

  const renderHeader = () => {
    return (
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <CalendarIcon className="w-5 h-5 text-emerald-400" />
          {format(currentMonth, 'MMMM yyyy')}
        </h2>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={prevMonth}>
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={nextMonth}>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    );
  };

  const renderDays = () => {
    const days = [];
    const startDate = startOfWeek(currentMonth);
    for (let i = 0; i < 7; i++) {
      days.push(
        <div key={i} className="text-center font-semibold text-sm text-slate-400 py-2">
          {format(addDays(startDate, i), 'EEE')}
        </div>
      );
    }
    return <div className="grid grid-cols-8 border-b border-slate-700/50">{days}<div className="text-center font-semibold text-sm text-slate-400 py-2 border-l border-slate-700/50">Weekly</div></div>;
  };

  const renderCells = () => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);

    const rows = [];
    let days = [];
    let day = startDate;
    let formattedDate = '';
    
    let weeklyProfit = 0;
    let weeklyTrades = 0;

    while (day <= endDate) {
      for (let i = 0; i < 7; i++) {
        formattedDate = format(day, 'yyyy-MM-dd');
        const dayData = dataMap[formattedDate];
        const isCurrentMonth = isSameMonth(day, monthStart);
        
        let cellClass = `min-h-[80px] p-2 border-r border-b border-slate-700/30 relative transition-colors `;
        
        if (!isCurrentMonth) {
          cellClass += 'bg-slate-900/40 text-slate-600 ';
        } else {
          cellClass += 'bg-slate-800/20 hover:bg-slate-800/60 ';
        }
        
        // Add color based on profit
        let profitStr = "";
        if (dayData && isCurrentMonth) {
          weeklyProfit += dayData.profit;
          weeklyTrades += dayData.trades;
          if (dayData.profit > 0) {
             cellClass = `min-h-[80px] p-2 border-r border-b border-emerald-900/50 bg-emerald-950/40 relative`;
             profitStr = `+$${dayData.profit.toFixed(2)}`;
          } else if (dayData.profit < 0) {
             cellClass = `min-h-[80px] p-2 border-r border-b border-red-900/50 bg-red-950/40 relative`;
             profitStr = `-$${Math.abs(dayData.profit).toFixed(2)}`;
          } else if (dayData.trades > 0) {
             cellClass = `min-h-[80px] p-2 border-r border-b border-slate-600 bg-slate-800 relative`;
             profitStr = `$0.00`;
          }
        }

        days.push(
          <div key={day} className={cellClass}>
            <div className="absolute top-1 right-2 text-xs font-semibold opacity-70">
              {format(day, 'd')}
            </div>
            {dayData && isCurrentMonth && (
              <div className="mt-4 flex flex-col items-center justify-center">
                <span className={`font-bold ${dayData.profit > 0 ? 'text-emerald-400' : dayData.profit < 0 ? 'text-red-400' : 'text-slate-300'}`}>
                  {profitStr}
                </span>
                <span className="text-[10px] text-slate-400 mt-1">{dayData.trades} trades</span>
              </div>
            )}
          </div>
        );
        day = addDays(day, 1);
      }
      
      // Add summary for the week
      rows.push(
        <div key={day} className="grid grid-cols-8">
          {days}
          <div className="flex flex-col items-center justify-center p-2 border-b border-slate-700/30 bg-slate-900/60">
             {weeklyTrades > 0 ? (
                <>
                  <span className={`font-bold ${weeklyProfit > 0 ? 'text-emerald-400' : weeklyProfit < 0 ? 'text-red-400' : 'text-slate-300'}`}>
                    {weeklyProfit > 0 ? '+' : ''}${weeklyProfit.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-slate-400 mt-1">{weeklyTrades} trades</span>
                </>
             ) : (
                <span className="text-slate-600 text-sm">-</span>
             )}
          </div>
        </div>
      );
      days = [];
      weeklyProfit = 0;
      weeklyTrades = 0;
    }
    return <div className="flex flex-col">{rows}</div>;
  };

  return (
    <Card className="col-span-full xl:col-span-2 border-slate-800 bg-slate-900/50 backdrop-blur">
      <CardContent className="p-6">
        {loading ? (
          <div className="h-[400px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
          </div>
        ) : (
          <div className="w-full">
            {renderHeader()}
            <div className="border border-slate-700/50 rounded-lg overflow-hidden bg-slate-950">
              {renderDays()}
              {renderCells()}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
