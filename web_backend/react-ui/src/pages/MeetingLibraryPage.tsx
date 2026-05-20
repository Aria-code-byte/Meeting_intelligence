import { useState } from 'react'
import { SlidersHorizontal, ChevronLeft, ChevronRight, MoreVertical, Trash2, Eye, RotateCcw, Check, X, TrendingUp, Phone, Users, Palette, Megaphone } from 'lucide-react'
import { StatusBadge } from '../components/StatusBadge'
import { ActionMenuPortal } from '../components/ActionMenuPortal'
import type { Meeting, MeetingStatus, SummaryTemplate } from '../types/models'

interface MeetingLibraryPageProps {
  meetings: Meeting[]
  templates: SummaryTemplate[]
  searchQuery: string
  onMeetingClick: (meeting: Meeting) => void
  onMeetingDelete: (id: string) => void
  onMeetingStatusChange: (id: string, status: MeetingStatus) => void
}

const iconOptions = [TrendingUp, Phone, Users, Palette, Megaphone]

// Get icon based on meeting index (consistent for same meeting)
const getIconForMeeting = (meeting: Meeting, index: number) => {
  return iconOptions[index % iconOptions.length]
}

// Get template name based on meeting.templateId
const getTemplateForMeeting = (meeting: Meeting, templates: SummaryTemplate[]): string => {
  if (meeting.templateId) {
    const template = templates.find(t => t.id === meeting.templateId)
    if (template) {
      return template.name
    }
  }
  return '通用'
}

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'completed', label: '已完成' },
  { value: 'transcribing', label: '转录中' },
  { value: 'summarizing', label: '总结中' },
  { value: 'failed', label: '失败' },
]

export function MeetingLibraryPage({ meetings, templates, searchQuery, onMeetingClick, onMeetingDelete, onMeetingStatusChange }: MeetingLibraryPageProps) {
  const [statusFilter, setStatusFilter] = useState('all')
  const [showMonthFilter, setShowMonthFilter] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null)
  const [menuPosition, setMenuPosition] = useState<{
    top: number
    left: number
    direction: 'down' | 'up'
  } | null>(null)

  const itemsPerPage = 10

  // Handle opening action menu with position calculation
  const handleMenuOpen = (meetingId: string, event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()

    const rect = event.currentTarget.getBoundingClientRect()
    const menuWidth = 192 // w-48 = 12rem = 192px
    const menuHeight = 144 // 预估菜单高度
    const gap = 8

    const spaceBelow = window.innerHeight - rect.bottom
    const direction = spaceBelow < menuHeight + gap ? 'up' : 'down'

    setOpenMenuId(meetingId)
    setMenuPosition({
      top: direction === 'down'
        ? rect.bottom + gap
        : rect.top - menuHeight - gap,
      left: Math.min(
        rect.right - menuWidth,
        window.innerWidth - menuWidth - 12
      ),
      direction,
    })
  }

  const handleMenuClose = () => {
    setOpenMenuId(null)
    setMenuPosition(null)
  }

  // Filter meetings
  const filteredMeetings = meetings.filter(meeting => {
    const matchesSearch = searchQuery === '' ||
      meeting.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      meeting.participants.some(p => p.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesStatus = statusFilter === 'all' || meeting.status === statusFilter

    return matchesSearch && matchesStatus
  })

  // Pagination
  const totalPages = Math.ceil(filteredMeetings.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedMeetings = filteredMeetings.slice(startIndex, endIndex)

  const handleDelete = (id: string) => {
    onMeetingDelete(id)
    setDeleteConfirmId(null)
    handleMenuClose()
  }

  const handleRegenerate = (id: string) => {
    setRegeneratingId(id)
    setTimeout(() => {
      onMeetingStatusChange(id, 'transcribing')
      setRegeneratingId(null)
      handleMenuClose()
    }, 2000)
  }

  const getParticipantsText = (participants: string[]) => {
    if (participants.length <= 2) {
      return participants.join('、')
    }
    return `${participants.length}位参与者`
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
  }

  return (
    <div className="space-y-6">
      {/* Page Description */}
      <p className="text-base text-[#536172]">
        管理和查看您的历史AI会议记录和总结。
      </p>

      {/* Filters */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {/* Status Dropdown */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation()
                const isOpen = openMenuId === 'status'
                if (isOpen) {
                  handleMenuClose()
                } else {
                  const rect = (e.currentTarget as HTMLButtonElement).getBoundingClientRect()
                  setOpenMenuId('status')
                  setMenuPosition({
                    top: rect.bottom + 8,
                    left: rect.left,
                    direction: 'down',
                  })
                }
              }}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-[#D6E1EA] rounded-xl text-[#06162E] hover:bg-[#EEF8FC] transition-colors"
            >
              <SlidersHorizontal className="w-4 h-4" />
              <span className="text-sm font-medium">
                {statusOptions.find(s => s.value === statusFilter)?.label || '全部状态'}
              </span>
            </button>

            <ActionMenuPortal
              open={openMenuId === 'status'}
              position={openMenuId === 'status' ? menuPosition : null}
              onClose={handleMenuClose}
            >
              <div className="w-48 bg-white rounded-xl border border-[#D6E1EA] shadow-lg overflow-hidden">
                {statusOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setStatusFilter(option.value)
                      handleMenuClose()
                    }}
                    className="w-full px-4 py-3 text-left text-sm hover:bg-[#EEF8FC] transition-colors flex items-center justify-between"
                  >
                    <span>{option.label}</span>
                    {statusFilter === option.value && (
                      <Check className="w-4 h-4 text-[#061B35]" />
                    )}
                  </button>
                ))}
              </div>
            </ActionMenuPortal>
          </div>

          {/* Month Filter */}
          <button
            onClick={() => setShowMonthFilter(!showMonthFilter)}
            className={`px-4 py-2.5 border rounded-xl text-sm font-medium transition-colors ${
              showMonthFilter
                ? 'bg-[#061B35] text-white border-[#061B35]'
                : 'bg-white border-[#D6E1EA] text-[#06162E] hover:bg-[#EEF8FC]'
            }`}
          >
            本月
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-[#D6E1EA] overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#D6E1EA]">
              <th className="text-left py-4 px-6 text-sm font-medium text-[#536172]">会议名称</th>
              <th className="text-left py-4 px-6 text-sm font-medium text-[#536172]">会议时间</th>
              <th className="text-left py-4 px-6 text-sm font-medium text-[#536172]">时长</th>
              <th className="text-left py-4 px-6 text-sm font-medium text-[#536172]">使用模板</th>
              <th className="text-left py-4 px-6 text-sm font-medium text-[#536172]">处理状态</th>
              <th className="text-right py-4 px-6 text-sm font-medium text-[#536172]">操作</th>
            </tr>
          </thead>
          <tbody>
            {paginatedMeetings.map((meeting, paginatedIndex) => {
              const Icon = getIconForMeeting(meeting, paginatedIndex)
              const showMenu = openMenuId === meeting.id
              const showDeleteConfirm = deleteConfirmId === meeting.id

              return (
                <tr
                  key={meeting.id}
                  className="border-b border-[#D6E1EA] hover:bg-[#EEF8FC]/50 transition-colors cursor-pointer"
                  onClick={() => !showMenu && !showDeleteConfirm && onMeetingClick(meeting)}
                >
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-[#061B35]" />
                      </div>
                      <div>
                        <div className="font-medium text-[#06162E]">{meeting.title}</div>
                        <div className="text-sm text-[#536172]">{getParticipantsText(meeting.participants)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-sm text-[#06162E]">{formatDate(meeting.date)}</td>
                  <td className="py-4 px-6 text-sm text-[#06162E]">{meeting.duration}</td>
                  <td className="py-4 px-6 text-sm text-[#06162E]">{getTemplateForMeeting(meeting, templates)}</td>
                  <td className="py-4 px-6">
                    <StatusBadge status={meeting.status} />
                  </td>
                  <td className="py-4 px-6 text-right">
                    {showDeleteConfirm ? (
                      <div className="flex items-center justify-end gap-2">
                        <span className="text-sm text-[#536172]">确认删除?</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setDeleteConfirmId(null)
                          }}
                          className="w-7 h-7 rounded-lg border border-[#D6E1EA] flex items-center justify-center hover:bg-[#EEF8FC] transition-colors"
                        >
                          <X className="w-3 h-3 text-[#536172]" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(meeting.id)
                          }}
                          className="w-7 h-7 rounded-lg bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors"
                        >
                          <Check className="w-3 h-3 text-white" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={(e) => handleMenuOpen(meeting.id, e)}
                        className="text-[#536172] hover:text-[#061B35] transition-colors p-1"
                      >
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    )}

                    {/* Action Menu - Portal to body */}
                    <ActionMenuPortal
                      open={showMenu}
                      position={showMenu ? menuPosition : null}
                      onClose={handleMenuClose}
                    >
                      <div className="w-48 bg-white rounded-xl border border-[#D6E1EA] shadow-lg overflow-hidden">
                        <button
                          onClick={() => {
                            onMeetingClick(meeting)
                            handleMenuClose()
                          }}
                          className="w-full px-4 py-3 text-left text-sm hover:bg-[#EEF8FC] transition-colors flex items-center gap-3"
                        >
                          <Eye className="w-4 h-4 text-[#536172]" />
                          <span>查看总结</span>
                        </button>
                        <button
                          onClick={() => handleRegenerate(meeting.id)}
                          disabled={regeneratingId === meeting.id}
                          className="w-full px-4 py-3 text-left text-sm hover:bg-[#EEF8FC] transition-colors flex items-center gap-3 disabled:opacity-50"
                        >
                          <RotateCcw className={`w-4 h-4 text-[#536172] ${regeneratingId === meeting.id ? 'animate-spin' : ''}`} />
                          <span>{regeneratingId === meeting.id ? '重新生成中...' : '重新生成'}</span>
                        </button>
                        <div className="border-t border-[#D6E1EA]" />
                        <button
                          onClick={() => {
                            setDeleteConfirmId(meeting.id)
                            handleMenuClose()
                          }}
                          className="w-full px-4 py-3 text-left text-sm hover:bg-red-50 text-red-600 transition-colors flex items-center gap-3"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>删除</span>
                        </button>
                      </div>
                    </ActionMenuPortal>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {/* Pagination */}
        {filteredMeetings.length > 0 && (
          <div className="flex items-center justify-between py-4 px-6 border-t border-[#D6E1EA]">
            <span className="text-sm text-[#536172]">
              显示第 {startIndex + 1} 至 {Math.min(endIndex, filteredMeetings.length)} 项结果，共 {filteredMeetings.length} 项
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="w-8 h-8 rounded-lg bg-white border border-[#D6E1EA] flex items-center justify-center hover:bg-[#EEF8FC] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4 text-[#536172]" />
              </button>
              {Array.from({ length: Math.min(3, totalPages) }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`w-8 h-8 rounded-lg font-medium transition-colors ${
                    currentPage === page
                      ? 'bg-[#061B35] text-white'
                      : 'bg-white border border-[#D6E1EA] text-[#06162E] hover:bg-[#EEF8FC]'
                  }`}
                >
                  {page}
                </button>
              ))}
              {totalPages > 3 && <span className="text-[#536172]">...</span>}
              {totalPages > 3 && (
                <button
                  onClick={() => setCurrentPage(totalPages)}
                  className={`w-8 h-8 rounded-lg font-medium transition-colors ${
                    currentPage === totalPages
                      ? 'bg-[#061B35] text-white'
                      : 'bg-white border border-[#D6E1EA] text-[#06162E] hover:bg-[#EEF8FC]'
                  }`}
                >
                  {totalPages}
                </button>
              )}
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="w-8 h-8 rounded-lg bg-white border border-[#D6E1EA] flex items-center justify-center hover:bg-[#EEF8FC] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4 text-[#536172]" />
              </button>
            </div>
          </div>
        )}

        {filteredMeetings.length === 0 && (
          <div className="py-16 text-center">
            <p className="text-[#536172]">没有找到匹配的会议记录</p>
          </div>
        )}
      </div>
    </div>
  )
}
