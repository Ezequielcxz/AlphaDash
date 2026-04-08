import { useState } from 'react'
import { ChevronDown, Globe, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAccounts, useSelectedAccount } from '@/hooks'

export default function AccountSelector() {
  const { accounts, loading } = useAccounts()
  const { selectedAccount, selectAccount } = useSelectedAccount()

  return (
    <div className="flex items-center space-x-2">
      <Select
        value={selectedAccount?.id?.toString() || 'global'}
        onValueChange={(value) => {
          if (value === 'global') {
            selectAccount(null)
          } else {
            const account = accounts.find((a) => a.id.toString() === value)
            selectAccount(account)
          }
        }}
      >
        <SelectTrigger className="w-[220px]">
          <Globe className="w-4 h-4 mr-2" />
          <SelectValue placeholder="Select Account">
            {selectedAccount
              ? selectedAccount.alias_personalizado ||
                `Account ${selectedAccount.account_number}`
              : 'Global Portfolio'}
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="global">
            <div className="flex items-center">
              <Globe className="w-4 h-4 mr-2" />
              <span>Global Portfolio</span>
              {!selectedAccount && <Check className="w-4 h-4 ml-auto" />}
            </div>
          </SelectItem>
          {accounts.map((account) => (
            <SelectItem key={account.id} value={account.id.toString()}>
              <div className="flex items-center justify-between w-full">
                <span>
                  {account.alias_personalizado ||
                    `Account ${account.account_number}`}
                </span>
                <span className="text-xs text-muted-foreground ml-2">
                  {account.broker_name}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}