/**
 * Account menu component
 * Dropdown menu for account information and settings access
 */

import { useState, useEffect } from 'react'
import { User, Settings, ChevronDown } from 'lucide-react'
import { getUserSettings, getSettingsSummary } from '../services/settingsService'

interface AccountMenuProps {
  isOpen: boolean
  onClose: () => void
  onOpenSettings: () => void
}

export function AccountMenu({ isOpen, onClose, onOpenSettings }: AccountMenuProps) {
  const [settingsSummary, setSettingsSummary] = useState(getSettingsSummary())

  useEffect(() => {
    setSettingsSummary(getSettingsSummary())
  }, [isOpen])

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
      />

      {/* Menu */}
      <div className="fixed top-16 right-9 z-50 w-72 bg-white rounded-xl border border-[#D6E1EA] shadow-lg overflow-hidden">
        {/* Account Info */}
        <div className="p-4 border-b border-[#D6E1EA]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#061B35] rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[#06162E] truncate">
                {settingsSummary.displayName}
              </p>
              <p className="text-xs text-[#536172]">本地账户</p>
            </div>
          </div>
        </div>

        {/* Account Details */}
        <div className="p-4 border-b border-[#D6E1EA] space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-[#536172]">数据存储</span>
            <span className="text-[#06162E] font-medium">{settingsSummary.storageType}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[#536172]">同步状态</span>
            <span className="text-[#536172]">未启用云同步</span>
          </div>
        </div>

        {/* Actions */}
        <div className="p-2">
          <button
            onClick={() => {
              onClose()
              onOpenSettings()
            }}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[#06162E] hover:bg-[#EEF8FC] transition-colors"
          >
            <Settings className="w-4 h-4 text-[#536172]" />
            <span>打开设置</span>
          </button>
        </div>

        {/* Footer Info */}
        <div className="p-3 bg-[#EEF8FC]">
          <p className="text-xs text-[#536172] text-center">
            账户登录功能即将支持
          </p>
        </div>
      </div>
    </>
  )
}
