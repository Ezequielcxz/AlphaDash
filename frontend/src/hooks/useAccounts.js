import { useState, useEffect, useCallback } from 'react'
import { accountsApi } from '../lib/api'

/**
 * Hook for managing accounts list.
 * Auto-refreshes every 30 seconds to pick up newly synced accounts.
 */
export function useAccounts() {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAccounts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await accountsApi.list()
      setAccounts(response.data)
    } catch (err) {
      setError(err.message || 'Failed to fetch accounts')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAccounts()
    // Auto-refresh every 30s to detect newly synced accounts
    const interval = setInterval(fetchAccounts, 30000)
    return () => clearInterval(interval)
  }, [fetchAccounts])

  return { accounts, loading, error, refetch: fetchAccounts }
}

/**
 * Hook for managing selected account.
 * Syncs with fresh data from the backend to avoid stale broker names.
 */
export function useSelectedAccount() {
  const { accounts } = useAccounts()
  const [selectedAccount, setSelectedAccountState] = useState(() => {
    const saved = localStorage.getItem('selectedAccount')
    return saved ? JSON.parse(saved) : null
  })

  // Sync selectedAccount with fresh data from backend whenever accounts list updates.
  // This fixes stale broker_name values stored in localStorage from previous sessions.
  useEffect(() => {
    if (selectedAccount && accounts.length > 0) {
      const fresh = accounts.find(a => a.id === selectedAccount.id)
      if (fresh && (
        fresh.broker_name !== selectedAccount.broker_name ||
        fresh.alias_personalizado !== selectedAccount.alias_personalizado
      )) {
        setSelectedAccountState(fresh)
        localStorage.setItem('selectedAccount', JSON.stringify(fresh))
      }
    }
  }, [accounts]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectAccount = useCallback((account) => {
    setSelectedAccountState(account)
    if (account) {
      localStorage.setItem('selectedAccount', JSON.stringify(account))
    } else {
      localStorage.removeItem('selectedAccount')
    }
  }, [])

  return { selectedAccount, selectAccount }
}