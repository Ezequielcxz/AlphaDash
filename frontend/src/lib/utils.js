import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/**
 * Format a number as currency
 */
export function formatCurrency(value, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Format a number with thousands separator
 */
export function formatNumber(value, decimals = 2) {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Format a percentage
 */
export function formatPercent(value, decimals = 1) {
  return `${value.toFixed(decimals)}%`
}

/**
 * Format a date
 */
export function formatDate(date, format = 'short') {
  const d = new Date(date)
  if (format === 'short') {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
  if (format === 'long') {
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  return d.toLocaleDateString('en-US')
}

/**
 * Get color class based on profit/loss
 */
export function getProfitColor(value) {
  if (value > 0) return 'text-emerald-400'
  if (value < 0) return 'text-coral-400'
  return 'text-muted-foreground'
}

/**
 * Get background color class based on profit/loss
 */
export function getProfitBgColor(value) {
  if (value > 0) return 'bg-emerald-500/10 border-emerald-500/30'
  if (value < 0) return 'bg-coral-500/10 border-coral-500/30'
  return 'bg-muted/50'
}

/**
 * Abbreviate large numbers
 */
export function abbreviateNumber(value) {
  if (Math.abs(value) >= 1e6) {
    return (value / 1e6).toFixed(1) + 'M'
  }
  if (Math.abs(value) >= 1e3) {
    return (value / 1e3).toFixed(1) + 'K'
  }
  return value.toFixed(2)
}

/**
 * Calculate time ago
 */
export function timeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return formatDate(date, 'short')
}