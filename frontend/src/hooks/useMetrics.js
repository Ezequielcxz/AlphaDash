import { useState, useEffect, useCallback } from 'react'
import { metricsApi } from '../lib/api'

/**
 * Hook for fetching and managing metrics data with optional period filter.
 * @param {number|null} accountId - Account to fetch metrics for (null = global)
 * @param {number|null} days - Period filter: 1, 3, 7, 30, 90, 365 or null (all time)
 */
export function useMetrics(accountId = null, days = null) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const response = accountId
        ? await metricsApi.byAccount(accountId, days)
        : await metricsApi.global(days)

      setMetrics(response.data)
    } catch (err) {
      setError(err.message || 'Failed to fetch metrics')
      console.error('Error fetching metrics:', err)
    } finally {
      setLoading(false)
    }
  }, [accountId, days])

  useEffect(() => {
    fetchMetrics()
  }, [fetchMetrics])

  return { metrics, loading, error, refetch: fetchMetrics }
}

/**
 * Hook for fetching equity curve data with optional period filter.
 */
export function useEquityCurve(accountId = null, days = null) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await metricsApi.equityCurve(accountId, days)
        setData(response.data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [accountId, days])

  return { data, loading, error }
}

/**
 * Hook for fetching heatmap data with optional period filter.
 */
export function useHeatmap(accountId = null, days = null) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await metricsApi.heatmap(accountId, days)
        setData(response.data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [accountId, days])

  return { data, loading, error }
}

/**
 * Hook for fetching temporal metrics
 */
export function useTemporalMetrics(accountId = null) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await metricsApi.temporal(accountId)
        setData(response.data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [accountId])

  return { data, loading, error }
}