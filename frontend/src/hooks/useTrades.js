import { useState, useEffect, useCallback, useRef } from 'react'
import { tradesApi } from '../lib/api'

/**
 * Hook for fetching trades with filters.
 * Uses JSON serialization to avoid infinite re-renders from object identity changes.
 */
export function useTrades(filters = {}) {
  const [trades, setTrades] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [total, setTotal] = useState(0)

  // Serialize filters to stable string so useCallback doesn't fire on every render
  const filtersKey = JSON.stringify(filters)

  const fetchTrades = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Parse back from the stable string
      const params = JSON.parse(filtersKey)

      // Remove null/undefined values so API doesn't receive them
      const cleanParams = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== null && v !== undefined)
      )

      const response = await tradesApi.list(cleanParams)
      setTrades(response.data)
      setTotal(response.data.length)
    } catch (err) {
      setError(err.message || 'Failed to fetch trades')
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey])

  useEffect(() => {
    fetchTrades()
  }, [fetchTrades])

  return { trades, loading, error, total, refetch: fetchTrades }
}

/**
 * Hook for fetching available symbols
 */
export function useSymbols(accountId = null) {
  const [symbols, setSymbols] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        setLoading(true)
        const response = await tradesApi.symbols(accountId)
        setSymbols(response.data.symbols)
      } catch (err) {
        console.error('Error fetching symbols:', err)
        setSymbols([])
      } finally {
        setLoading(false)
      }
    }

    fetchSymbols()
  }, [accountId])

  return { symbols, loading }
}

/**
 * Hook for fetching magic numbers (strategies)
 */
export function useMagicNumbers(accountId = null) {
  const [magicNumbers, setMagicNumbers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMagicNumbers = async () => {
      try {
        setLoading(true)
        const response = await tradesApi.magicNumbers(accountId)
        setMagicNumbers(response.data.magic_numbers)
      } catch (err) {
        console.error('Error fetching magic numbers:', err)
        setMagicNumbers([])
      } finally {
        setLoading(false)
      }
    }

    fetchMagicNumbers()
  }, [accountId])

  return { magicNumbers, loading }
}