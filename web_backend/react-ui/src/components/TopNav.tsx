import { useState } from 'react'
import { Search, Bell, Plus, Download, HelpCircle } from 'lucide-react'
import type { PageType } from '../App'
import { NotificationCenter } from './NotificationCenter'
import { HelpPanel } from './HelpPanel'
import { AccountMenu } from './AccountMenu'
import { SettingsPanel } from './SettingsPanel'
import { useMeetings, useActionItems } from '../store/useAppStore'

interface TopNavProps {
  currentPage: PageType
  meetingSearchQuery?: string
  onMeetingSearchChange?: (query: string) => void
  templateSearchQuery?: string
  onTemplateSearchChange?: (query: string) => void
  onCreateTemplate?: () => void
}

export function TopNav({
  currentPage,
  meetingSearchQuery = '',
  onMeetingSearchChange,
  templateSearchQuery = '',
  onTemplateSearchChange,
  onCreateTemplate
}: TopNavProps) {
  const { meetings } = useMeetings()
  const { actionItems } = useActionItems()

  const [showNotificationCenter, setShowNotificationCenter] = useState(false)
  const [showHelpPanel, setShowHelpPanel] = useState(false)
  const [showAccountMenu, setShowAccountMenu] = useState(false)
  const [showSettingsPanel, setShowSettingsPanel] = useState(false)

  const handleExportClick = () => {
    alert('导出功能请在会议详情页或会议库中使用')
  }

  // Common action buttons for all pages
  const commonActions = (
    <>
      <button
        onClick={() => setShowNotificationCenter(!showNotificationCenter)}
        className="w-10 h-10 rounded-lg bg-[#DCEBFF] text-[#061B35] flex items-center justify-center hover:bg-[#CFE5FF] transition-colors"
        title="通知"
      >
        <Bell className="w-5 h-5" />
      </button>
      <button
        onClick={() => setShowHelpPanel(!showHelpPanel)}
        className="w-10 h-10 rounded-lg bg-[#DCEBFF] text-[#061B35] flex items-center justify-center hover:bg-[#CFE5FF] transition-colors"
        title="帮助"
      >
        <HelpCircle className="w-5 h-5" />
      </button>
      <button
        onClick={() => setShowAccountMenu(!showAccountMenu)}
        className="w-10 h-10 bg-[#061B35] rounded-lg flex items-center justify-center hover:bg-[#08213F] transition-colors"
        title="用户账户"
      >
        <span className="text-white font-medium">U</span>
      </button>
    </>
  )

  // Dashboard shows "工作台" without tabs
  if (currentPage === 'dashboard') {
    return (
      <>
        <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
          <h1 className="text-2xl font-semibold text-[#06162E]">工作台</h1>
          <div className="flex items-center gap-3">
            {commonActions}
          </div>
        </div>
        <NotificationCenter
          isOpen={showNotificationCenter}
          onClose={() => setShowNotificationCenter(false)}
          meetings={meetings}
          actionItems={actionItems}
        />
        <HelpPanel
          isOpen={showHelpPanel}
          onClose={() => setShowHelpPanel(false)}
        />
        <AccountMenu
          isOpen={showAccountMenu}
          onClose={() => setShowAccountMenu(false)}
          onOpenSettings={() => {
            setShowAccountMenu(false)
            setShowSettingsPanel(true)
          }}
        />
        <SettingsPanel
          isOpen={showSettingsPanel}
          onClose={() => setShowSettingsPanel(false)}
        />
      </>
    )
  }

  // Meetings page shows search bar
  if (currentPage === 'meetings') {
    return (
      <>
        <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
          <h1 className="text-2xl font-semibold text-[#06162E]">会议库</h1>
          <div className="flex items-center gap-3">
            <div className="relative w-96">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#536172]" />
              <input
                type="text"
                placeholder="搜索会议名称或参与者..."
                value={meetingSearchQuery}
                onChange={(e) => onMeetingSearchChange?.(e.target.value)}
                className="w-full pl-12 pr-4 py-2.5 bg-[#EEF8FC] border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:ring-2 focus:ring-[#061B35]/20 focus:bg-white transition-all"
              />
            </div>
            {commonActions}
          </div>
        </div>
        <NotificationCenter
          isOpen={showNotificationCenter}
          onClose={() => setShowNotificationCenter(false)}
          meetings={meetings}
          actionItems={actionItems}
        />
        <HelpPanel
          isOpen={showHelpPanel}
          onClose={() => setShowHelpPanel(false)}
        />
        <AccountMenu
          isOpen={showAccountMenu}
          onClose={() => setShowAccountMenu(false)}
          onOpenSettings={() => {
            setShowAccountMenu(false)
            setShowSettingsPanel(true)
          }}
        />
        <SettingsPanel
          isOpen={showSettingsPanel}
          onClose={() => setShowSettingsPanel(false)}
        />
      </>
    )
  }

  // Templates page shows search and add button
  if (currentPage === 'templates') {
    return (
      <>
        <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
          <h1 className="text-2xl font-semibold text-[#06162E]">模板管理</h1>
          <div className="flex items-center gap-3">
            <div className="relative w-80">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#536172]" />
              <input
                type="text"
                placeholder="搜索模板..."
                value={templateSearchQuery}
                onChange={(e) => onTemplateSearchChange?.(e.target.value)}
                className="w-full pl-12 pr-4 py-2.5 bg-[#EEF8FC] border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:ring-2 focus:ring-[#061B35]/20 focus:bg-white transition-all"
              />
            </div>
            <button
              onClick={() => {
                console.log('[TopNav] 新建模板按钮点击')
                onCreateTemplate?.()
              }}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">新建模板</span>
            </button>
            {commonActions}
          </div>
        </div>
        <NotificationCenter
          isOpen={showNotificationCenter}
          onClose={() => setShowNotificationCenter(false)}
          meetings={meetings}
          actionItems={actionItems}
        />
        <HelpPanel
          isOpen={showHelpPanel}
          onClose={() => setShowHelpPanel(false)}
        />
        <AccountMenu
          isOpen={showAccountMenu}
          onClose={() => setShowAccountMenu(false)}
          onOpenSettings={() => {
            setShowAccountMenu(false)
            setShowSettingsPanel(true)
          }}
        />
        <SettingsPanel
          isOpen={showSettingsPanel}
          onClose={() => setShowSettingsPanel(false)}
        />
      </>
    )
  }

  // Detail pages show title and action buttons
  return (
    <>
      <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
        <div className="flex items-center gap-8">
          <h1 className="text-2xl font-semibold text-[#06162E]">
            {currentPage === 'summary' && 'AI 总结详情'}
            {currentPage === 'recordings' && '录音文件'}
            {currentPage === 'action' && '行动项'}
            {currentPage === 'library' && '团队知识库'}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportClick}
            className="flex items-center gap-2 px-5 py-2.5 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm font-medium">Export</span>
          </button>
          {commonActions}
        </div>
      </div>
      <NotificationCenter
        isOpen={showNotificationCenter}
        onClose={() => setShowNotificationCenter(false)}
        meetings={meetings}
        actionItems={actionItems}
      />
      <HelpPanel
        isOpen={showHelpPanel}
        onClose={() => setShowHelpPanel(false)}
      />
      <AccountMenu
        isOpen={showAccountMenu}
        onClose={() => setShowAccountMenu(false)}
        onOpenSettings={() => {
          setShowAccountMenu(false)
          setShowSettingsPanel(true)
        }}
      />
      <SettingsPanel
        isOpen={showSettingsPanel}
        onClose={() => setShowSettingsPanel(false)}
      />
    </>
  )
}
