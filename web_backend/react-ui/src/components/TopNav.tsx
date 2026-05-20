import { Search, Bell, Plus, Download, HelpCircle } from 'lucide-react'
import type { PageType } from '../App'

interface TopNavProps {
  currentPage: PageType
}

export function TopNav({ currentPage }: TopNavProps) {
  // Common action buttons for all pages
  const commonActions = (
    <>
      <button className="w-10 h-10 rounded-lg bg-[#DCEBFF] text-[#061B35] flex items-center justify-center hover:bg-[#CFE5FF] transition-colors" title="通知">
        <Bell className="w-5 h-5" />
      </button>
      <button className="w-10 h-10 rounded-lg bg-[#DCEBFF] text-[#061B35] flex items-center justify-center hover:bg-[#CFE5FF] transition-colors" title="帮助">
        <HelpCircle className="w-5 h-5" />
      </button>
      <button className="w-10 h-10 bg-[#061B35] rounded-lg flex items-center justify-center" title="用户账户">
        <span className="text-white font-medium">U</span>
      </button>
    </>
  )

  // Dashboard shows "工作台" without tabs
  if (currentPage === 'dashboard') {
    return (
      <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
        <h1 className="text-2xl font-semibold text-[#06162E]">工作台</h1>
        <div className="flex items-center gap-3">
          {commonActions}
        </div>
      </div>
    )
  }

  // Meetings page shows search bar
  if (currentPage === 'meetings') {
    return (
      <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
        <h1 className="text-2xl font-semibold text-[#06162E]">会议库</h1>
        <div className="flex items-center gap-3">
          <div className="relative w-96">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#536172]" />
            <input
              type="text"
              placeholder="搜索会议名称或参与者..."
              className="w-full pl-12 pr-4 py-2.5 bg-[#EEF8FC] border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:ring-2 focus:ring-[#061B35]/20 focus:bg-white transition-all"
            />
          </div>
          {commonActions}
        </div>
      </div>
    )
  }

  // Templates page shows search and add button
  if (currentPage === 'templates') {
    return (
      <div className="h-16 bg-white border-b border-[#D6E1EA] flex items-center justify-between px-9">
        <h1 className="text-2xl font-semibold text-[#06162E]">模板管理</h1>
        <div className="flex items-center gap-3">
          <div className="relative w-80">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#536172]" />
            <input
              type="text"
              placeholder="搜索模板..."
              className="w-full pl-12 pr-4 py-2.5 bg-[#EEF8FC] border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:ring-2 focus:ring-[#061B35]/20 focus:bg-white transition-all"
            />
          </div>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors">
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">新建模板</span>
          </button>
          {commonActions}
        </div>
      </div>
    )
  }

  // Detail pages show title and action buttons
  return (
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
        <button className="flex items-center gap-2 px-5 py-2.5 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors">
          <Download className="w-4 h-4" />
          <span className="text-sm font-medium">Export</span>
        </button>
        {commonActions}
      </div>
    </div>
  )
}
