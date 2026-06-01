import { useState, useEffect, useCallback } from 'react'
import { ArrowLeft, Copy, RefreshCw, Download, CheckCircle2, FileText, Users, Calendar, Clock, AlertCircle, Save, Edit2, X, Plus, Trash2, FileDown, Sparkles, Loader2 } from 'lucide-react'
import { ActionItemCard } from '../components/ActionItemCard'
import { useMeetings, useActionItems } from '../store/useAppStore'
import { generateFallbackSummary, validateTranscript, generateMeetingSummary, markSummaryAsManual } from '../services/summaryGenerationService'
import { exportMeeting, canExport, type ExportFormat } from '../services/exportService'
import { getUserSettings } from '../services/settingsService'
import { enhanceTranscript } from '../services/enhancementService'
import type { PageType } from '../App'
import type { Meeting, ActionItem, TranscriptTurn, EnhancedTranscriptTurn } from '../types/models'

// 阶段 10B-4：辅助函数 - 格式化时间
function formatTimestamp(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '??:??:??.???'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(3, '0')}`
}

// 阶段 10B-4：辅助函数 - 格式化 speaker turn
function formatTranscriptTurn(turn: TranscriptTurn): string {
  const startTime = formatTimestamp(turn.start)
  const endTime = formatTimestamp(turn.end)
  return `[${startTime} - ${endTime}] ${turn.speaker}\n${turn.text}`
}

interface SummaryDetailPageProps {
  currentPage: PageType
  meetingId: string | null
  templates: any[]
  onBack: () => void
}

type TabType = 'summary' | 'transcript' | 'action' | 'info'

export function SummaryDetailPage({ currentPage, meetingId, templates, onBack }: SummaryDetailPageProps) {
  const { getMeetingById, updateMeeting } = useMeetings()
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const userSettings = getUserSettings()
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(userSettings.exportFormatPreference)
  const [includeTranscript, setIncludeTranscript] = useState(userSettings.includeTranscriptByDefault)

  // Reset export options when dialog opens
  useEffect(() => {
    if (showExportDialog) {
      const settings = getUserSettings()
      setSelectedFormat(settings.exportFormatPreference)
      setIncludeTranscript(settings.includeTranscriptByDefault)
    }
  }, [showExportDialog])

  // Load meeting from store when meetingId changes or when meeting list updates
  useEffect(() => {
    if (meetingId) {
      const loadedMeeting = getMeetingById(meetingId)
      console.log('[SummaryDetailPage] 加载会议数据:', {
        meetingId,
        summaryProvider: loadedMeeting?.summaryProvider,
        summaryIsFallback: loadedMeeting?.summaryIsFallback,
        transcriptionProvider: loadedMeeting?.transcriptionProvider,
        transcriptionIsFallback: loadedMeeting?.transcriptionIsFallback,
        showBackendBanner: loadedMeeting?.summaryProvider === 'backend' && !loadedMeeting?.summaryIsFallback,
        showFallbackBanner: loadedMeeting?.summaryProvider === 'fallback' && loadedMeeting?.summaryIsFallback,
        showManualBanner: loadedMeeting?.summaryProvider === 'manual',
      })
      setMeeting(loadedMeeting)
    } else {
      setMeeting(null)
    }
  }, [meetingId, getMeetingById])

  // Update local meeting state when data is modified (for immediate UI feedback)
  const refreshMeeting = useCallback(() => {
    if (meetingId) {
      const loadedMeeting = getMeetingById(meetingId)
      setMeeting(loadedMeeting)
    }
  }, [meetingId, getMeetingById])
  const [activeTab, setActiveTab] = useState<TabType>('summary')
  const [copySuccess, setCopySuccess] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [manualTranscript, setManualTranscript] = useState('')
  const [isEditingTranscript, setIsEditingTranscript] = useState(false)
  // LLM 优化相关状态
  const [isEnhancing, setIsEnhancing] = useState(false)
  const [enhancementError, setEnhancementError] = useState<string | null>(null)

  // 编辑状态
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const [isEditingSummary, setIsEditingSummary] = useState(false)
  const [editedSummary, setEditedSummary] = useState('')
  const [newActionContent, setNewActionContent] = useState('')
  const [isAddingAction, setIsAddingAction] = useState(false)
  const [editingActionId, setEditingActionId] = useState<string | null>(null)
  const [editActionContent, setEditActionContent] = useState('')
  const [editActionOwner, setEditActionOwner] = useState('')
  const [editActionDueDate, setEditActionDueDate] = useState('')

  const { actionItems, createActionItem, updateActionItem, deleteActionItem } = useActionItems()

  // Get template name for this meeting
  const getTemplateName = () => {
    if (!meeting) return '未知模板'

    // 优先使用模板快照名称
    if ((meeting as any).templateSnapshot?.name) {
      return (meeting as any).templateSnapshot.name
    }

    // 其次使用保存的模板名称
    if ((meeting as any).templateName) {
      return (meeting as any).templateName
    }

    // 然后从模板列表查找
    if (meeting.templateId) {
      const template = templates.find(t => t.id === meeting.templateId)
      if (template) {
        return template.name
      }
    }

    return '未知模板'
  }

  // Filter action items for current meeting
  const meetingActions = meeting ? actionItems.filter(a => a.meetingId === meeting.id) : []

  const sidebarItems = [
    { id: 'summary' as TabType, label: 'AI 总结', count: null },
    { id: 'transcript' as TabType, label: '完整文字稿', count: null },
    { id: 'action' as TabType, label: '待办事项', count: meetingActions.length },
    { id: 'info' as TabType, label: '会议信息', count: null },
  ]

  const handleCopy = async () => {
    if (!meeting) return

    let content = ''

    if (activeTab === 'summary' && meeting.summary) {
      content = meeting.summary
    } else if (activeTab === 'transcript' && meeting.transcript) {
      content = meeting.transcript
    } else if (activeTab === 'info') {
      content = `会议标题：${meeting.title}\n日期：${meeting.date}\n模板：${getTemplateName()}\n状态：${meeting.status}`
    }

    if (!content) return

    try {
      await navigator.clipboard.writeText(content)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
    if (!meeting || !canExport(meeting)) {
      alert('当前会议没有可导出的内容，请先生成总结或添加文字稿。')
      return
    }
    setShowExportDialog(true)
  }

  const handleConfirmExport = () => {
    if (!meeting) return

    exportMeeting(meeting, meetingActions, {
      format: selectedFormat,
      includeTranscript: includeTranscript,
      includeActionItems: true,
      allTemplates: templates,
    })

    setShowExportDialog(false)
  }

  const handleRegenerate = async () => {
    if (!meeting) return

    // Check if transcript exists
    if (!meeting.transcript || meeting.transcript.trim() === '') {
      alert('当前会议暂无文字稿，无法重新生成总结。\n\n请先在"完整文字稿"标签页添加会议文字稿。')
      setActiveTab('transcript')
      setIsEditingTranscript(true)
      return
    }

    setRegenerating(true)

    try {
      // Template priority: templateSnapshot > templateId lookup
      let templateToUse = templates.find(t => t.id === meeting.templateId)

      if ((meeting as any).templateSnapshot) {
        // Use template snapshot if available
        templateToUse = (meeting as any).templateSnapshot
      }

      if (!templateToUse) {
        alert('未找到会议模板，无法生成总结')
        setRegenerating(false)
        return
      }

      // Use the unified summary generation service
      const summaryResult = await generateMeetingSummary({
        meetingId: meeting.id,
        transcript: meeting.transcript,
        templateSnapshot: templateToUse ? {
          id: templateToUse.id,
          name: templateToUse.name,
          structure: templateToUse.structure,
          prompt: templateToUse.prompt,
        } : undefined,
      })

      if (!summaryResult.summary && summaryResult.error) {
        alert(summaryResult.error)
        setRegenerating(false)
        return
      }

      // Update meeting with summary and provider info
      updateMeeting(meeting.id, {
        summary: summaryResult.summary,
        summaryProvider: summaryResult.provider,
        summaryIsFallback: summaryResult.isFallback,
        status: 'completed',
        errorMessage: undefined,
        lastProcessedAt: new Date().toISOString(),
      })

      setTimeout(() => {
        setRegenerating(false)
      }, 500)
    } catch (error) {
      alert('生成总结失败，请重试')
      setRegenerating(false)
    }
  }

  const handleSaveTranscript = () => {
    if (!meeting) return

    // Validate transcript
    const validation = validateTranscript(manualTranscript)
    if (!validation.valid) {
      alert(validation.error)
      return
    }

    // Update meeting with transcript
    updateMeeting(meeting.id, {
      transcript: manualTranscript.trim(),
      errorMessage: undefined,
    })

    setIsEditingTranscript(false)
    setManualTranscript('')
  }

  const handleGenerateSummary = () => {
    if (!meeting) return

    const transcriptToUse = manualTranscript.trim() || meeting.transcript || ''

    // Validate transcript
    const validation = validateTranscript(transcriptToUse)
    if (!validation.valid) {
      alert(validation.error)
      return
    }

    // Template priority: templateSnapshot > templateId lookup
    let templateToUse = templates.find(t => t.id === meeting.templateId)

    if ((meeting as any).templateSnapshot) {
      // Use template snapshot if available
      templateToUse = (meeting as any).templateSnapshot
    }

    if (!templateToUse) {
      alert('未找到会议模板，无法生成总结')
      return
    }

    // Use the summary generation service
    const summary = generateFallbackSummary({
      transcript: transcriptToUse,
      template: templateToUse,
      meeting,
    })

    // Update meeting
    updateMeeting(meeting.id, {
      transcript: transcriptToUse,
      summary,
      status: 'completed',
      errorMessage: undefined,
    })

    if (manualTranscript) {
      setManualTranscript('')
      setIsEditingTranscript(false)
    }

    // Switch to summary tab to show result
    setActiveTab('summary')
  }

  // Title edit handlers
  const handleEditTitle = () => {
    if (!meeting) return
    setEditedTitle(meeting.title)
    setIsEditingTitle(true)
  }

  const handleSaveTitle = () => {
    if (!meeting) return

    const trimmedTitle = editedTitle.trim()
    if (!trimmedTitle) {
      alert('会议标题不能为空')
      return
    }

    if (trimmedTitle.length > 100) {
      alert('会议标题不能超过 100 个字符')
      return
    }

    updateMeeting(meeting.id, { title: trimmedTitle })
    setIsEditingTitle(false)
    refreshMeeting()
  }

  const handleCancelEditTitle = () => {
    setEditedTitle('')
    setIsEditingTitle(false)
  }

  // Summary edit handlers
  const handleEditSummary = () => {
    if (!meeting) return
    setEditedSummary(meeting.summary || '')
    setIsEditingSummary(true)
  }

  const handleSaveSummary = () => {
    if (!meeting) return

    const trimmedSummary = editedSummary.trim()
    if (trimmedSummary.length > 10000) {
      alert('总结内容不能超过 10000 个字符')
      return
    }

    // Mark as manual if user edited the summary
    const updateData = {
      summary: trimmedSummary || undefined,
      summaryProvider: 'manual' as const,
      summaryIsFallback: false,
    }

    updateMeeting(meeting.id, updateData)
    setIsEditingSummary(false)
    refreshMeeting()
  }

  const handleCancelEditSummary = () => {
    setEditedSummary('')
    setIsEditingSummary(false)
  }

  // LLM 优化功能处理
  const handleEnhanceTranscript = async () => {
    if (!meeting || !meeting.transcriptTurns || meeting.transcriptTurns.length === 0) {
      alert('该会议没有可优化的转录内容')
      return
    }

    setIsEnhancing(true)
    setEnhancementError(null)

    try {
      console.log('[handleEnhanceTranscript] 开始增强，原始 turns 数量:', meeting.transcriptTurns?.length)
      console.log('[handleEnhanceTranscript] 原始 turn 示例:', meeting.transcriptTurns?.[0])

      const response = await enhanceTranscript(
        meeting.transcriptTurns,
        'deepseek',
        'deepseek-chat'
      )

      console.log('[handleEnhanceTranscript] API 响应:', response)
      console.log('[handleEnhanceTranscript] 增强 turns 数量:', response.enhancedTranscriptTurns?.length)
      console.log('[handleEnhanceTranscript] 增强 turn 示例:', response.enhancedTranscriptTurns?.[0])

      if (response.success && response.enhancedTranscriptTurns) {
        // 检查增强后的文本是否与原始文本不同
        const firstOriginal = meeting.transcriptTurns[0]?.text || ''
        const firstEnhanced = response.enhancedTranscriptTurns[0]?.text || ''
        const hasChanges = firstOriginal !== firstEnhanced

        console.log('[handleEnhanceTranscript] 文本对比:')
        console.log('  原始:', firstOriginal.substring(0, 100))
        console.log('  增强:', firstEnhanced.substring(0, 100))
        console.log('  有变化:', hasChanges)

        // 更新会议数据
        updateMeeting(meeting.id, {
          enhancedTranscriptTurns: response.enhancedTranscriptTurns,
          enhancementProvider: 'deepseek',
          enhancementModel: 'deepseek-chat',
          isEnhanced: true,
          enhancementTime: new Date().toISOString(),
        })

        console.log('[handleEnhanceTranscript] 数据已更新，调用 refreshMeeting()')
        // 使用 setTimeout 确保 localStorage 数据已写入
        setTimeout(() => {
          refreshMeeting()
          console.log('[handleEnhanceTranscript] refreshMeeting() 完成')
        }, 100)

        // 显示成功消息
        const turnCount = response.enhancedTranscriptTurns.length
        const time = response.processingTimeMs ? `${(response.processingTimeMs / 1000).toFixed(1)}秒` : '未知'
        alert(`✅ 优化成功！已优化 ${turnCount} 条转录，耗时 ${time}`)
      } else {
        throw new Error(response.error || '优化失败')
      }
    } catch (error) {
      console.error('[SummaryDetailPage] 优化失败:', error)
      setEnhancementError(error instanceof Error ? error.message : '优化失败，请稍后重试')
      alert(`❌ 优化失败：${error instanceof Error ? error.message : '请检查网络连接和API配置'}`)
    } finally {
      setIsEnhancing(false)
    }
  }

  // Action item handlers
  const handleAddAction = () => {
    if (!meeting) return

    const trimmedContent = newActionContent.trim()
    if (!trimmedContent) {
      alert('请输入待办事项内容')
      return
    }

    if (trimmedContent.length > 200) {
      alert('待办事项内容不能超过 200 个字符')
      return
    }

    createActionItem({
      meetingId: meeting.id,
      content: trimmedContent,
      status: 'todo',
    })
    setNewActionContent('')
    setIsAddingAction(false)
  }

  const handleToggleActionStatus = (actionId: string, currentStatus: ActionItem['status']) => {
    const nextStatus: ActionItem['status'] =
      currentStatus === 'todo' ? 'in_progress' :
      currentStatus === 'in_progress' ? 'done' : 'todo'
    updateActionItem(actionId, { status: nextStatus })
  }

  const handleDeleteAction = (actionId: string) => {
    if (confirm('确定要删除这个待办事项吗？此操作不可撤销。')) {
      deleteActionItem(actionId)
    }
  }

  const handleStartEditAction = (action: ActionItem) => {
    setEditingActionId(action.id)
    setEditActionContent(action.content)
    setEditActionOwner(action.owner || '')
    setEditActionDueDate(action.dueDate || '')
  }

  const handleSaveActionEdit = () => {
    if (!editingActionId) return

    const trimmedContent = editActionContent.trim()
    if (!trimmedContent) {
      alert('待办事项内容不能为空')
      return
    }

    if (trimmedContent.length > 200) {
      alert('待办事项内容不能超过 200 个字符')
      return
    }

    // Validate due date format if provided
    if (editActionDueDate) {
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/
      if (!dateRegex.test(editActionDueDate)) {
        alert('请输入有效的截止日期格式（YYYY-MM-DD）')
        return
      }

      // Check if date is valid
      const date = new Date(editActionDueDate)
      if (isNaN(date.getTime())) {
        alert('请输入有效的截止日期')
        return
      }
    }

    updateActionItem(editingActionId, {
      content: trimmedContent,
      owner: editActionOwner.trim() || undefined,
      dueDate: editActionDueDate || undefined,
    })

    setEditingActionId(null)
    setEditActionContent('')
    setEditActionOwner('')
    setEditActionDueDate('')
  }

  const handleCancelActionEdit = () => {
    setEditingActionId(null)
    setEditActionContent('')
    setEditActionOwner('')
    setEditActionDueDate('')
  }

  // Show loading state if no meeting
  if (!meeting) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-[#536172] mx-auto mb-4" />
          <p className="text-[#536172]">未找到会议信息</p>
          <p className="text-sm text-[#536172] mt-2">该会议可能已被删除或不存在</p>
          <button
            onClick={onBack}
            className="mt-4 px-4 py-2 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors"
          >
            返回会议库
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-6">
      {/* Left Sidebar */}
      <div className="w-full max-w-[270px] flex-shrink-0 space-y-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-[#536172] hover:text-[#061B35] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">返回</span>
        </button>

        <div className="bg-white rounded-xl border border-[#D6E1EA] overflow-hidden">
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-4 py-3 text-sm transition-colors ${
                activeTab === item.id
                  ? 'bg-[#EEF8FC] text-[#061B35] font-medium'
                  : 'text-[#536172] hover:bg-[#EEF8FC]/50'
              }`}
            >
              <span>{item.label}</span>
              {item.count !== null && item.count > 0 && (
                <span className="w-5 h-5 bg-[#FF6B6B] text-white text-xs rounded-full flex items-center justify-center">
                  {item.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Header Info */}
        <div className="space-y-3">
          <span className="inline-block px-3 py-1 bg-[#E9F3FF] text-[#061B35] text-xs rounded-full">
            {getTemplateName()}
          </span>
          <div className="flex items-center gap-3">
            {isEditingTitle ? (
              <div className="flex items-center gap-2 flex-1">
                <input
                  type="text"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  className="flex-1 px-3 py-2 text-3xl font-bold text-[#06162E] border border-[#D6E1EA] rounded-lg focus:outline-none focus:border-[#061B35]"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveTitle()
                    if (e.key === 'Escape') handleCancelEditTitle()
                  }}
                />
                <button
                  onClick={handleSaveTitle}
                  className="p-2 bg-[#10B981] text-white rounded-lg hover:bg-[#059669] transition-colors"
                  title="保存"
                >
                  <Save className="w-5 h-5" />
                </button>
                <button
                  onClick={handleCancelEditTitle}
                  className="p-2 bg-[#FF6B6B] text-white rounded-lg hover:bg-[#DC2626] transition-colors"
                  title="取消"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3 flex-1">
                <h1 className="text-3xl font-bold text-[#06162E]">
                  {meeting.title}
                </h1>
                <button
                  onClick={handleEditTitle}
                  className="p-2 text-[#536172] hover:text-[#061B35] hover:bg-[#EEF8FC] rounded-lg transition-colors"
                  title="编辑标题"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-[#536172]">
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {meeting.date}
              </span>
              <span>•</span>
              <span>{meeting.duration}</span>
              <span>•</span>
              <span className={`${
                meeting.status === 'completed' ? 'text-[#10B981]' :
                meeting.status === 'failed' ? 'text-[#FF6B6B]' :
                'text-[#536172]'
              }`}>
                {meeting.status === 'completed' && '已完成'}
                {meeting.status === 'uploaded' && '已上传'}
                {meeting.status === 'transcribing' && '转录中'}
                {meeting.status === 'summarizing' && '总结中'}
                {meeting.status === 'failed' && '失败'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-2 px-4 py-2 border border-[#D6E1EA] rounded-lg text-[#06162E] hover:bg-[#EEF8FC] transition-colors"
              >
                <Copy className="w-4 h-4" />
                <span className="text-sm">{copySuccess ? '已复制' : '复制'}</span>
              </button>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="flex items-center gap-2 px-4 py-2 border border-[#D6E1EA] rounded-lg text-[#06162E] hover:bg-[#EEF8FC] transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`} />
                <span className="text-sm">{regenerating ? '生成中...' : '重新生成'}</span>
              </button>
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 px-4 py-2 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors"
              >
                <Download className="w-4 h-4" />
                <span className="text-sm">下载</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'summary' && (
          <div className="bg-white rounded-2xl p-6 border-2 border-[#D6E1EA]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[#061B35]" />
                </div>
                <h2 className="text-xl font-semibold text-[#06162E]">会议总结</h2>
              </div>
              {meeting.summary && !isEditingSummary && (
                <button
                  onClick={handleEditSummary}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-[#536172] hover:text-[#061B35] hover:bg-[#EEF8FC] rounded-lg transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                  编辑
                </button>
              )}
            </div>

            {isEditingSummary ? (
              <div className="space-y-3">
                <textarea
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  className="w-full h-64 px-4 py-3 text-[#06162E] bg-white border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] focus:ring-2 focus:ring-[#061B35]/20 transition-all resize-none text-sm leading-relaxed"
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveSummary}
                    className="flex items-center gap-2 px-4 py-2 bg-[#10B981] text-white rounded-lg text-sm hover:bg-[#059669] transition-colors"
                  >
                    <Save className="w-4 h-4" />
                    保存
                  </button>
                  <button
                    onClick={handleCancelEditSummary}
                    className="flex items-center gap-2 px-4 py-2 border border-[#D6E1EA] rounded-lg text-sm text-[#06162E] hover:bg-[#EEF8FC] transition-colors"
                  >
                    <X className="w-4 h-4" />
                    取消
                  </button>
                </div>
              </div>
            ) : meeting.summary ? (
              <div className="space-y-4">
                <div className="text-[#06162E] leading-relaxed whitespace-pre-line">
                  {meeting.summary}
                </div>
                {meeting.summaryProvider === 'fallback' && meeting.summaryIsFallback && (
                  <div className="flex items-start gap-2 px-3 py-2 bg-[#FFF7ED] rounded-lg border border-[#F59E0B] text-xs">
                    <AlertCircle className="w-4 h-4 text-[#F59E0B] mt-0.5 flex-shrink-0" />
                    <p className="text-[#F59E0B]">当前总结由本地 fallback 规则生成，尚未接入真实 AI 总结服务</p>
                  </div>
                )}
                {meeting.summaryProvider === 'backend' && !meeting.summaryIsFallback && meeting.summary && !meeting.errorMessage && (
                  <div className="flex items-start gap-2 px-3 py-2 bg-[#ECFDF5] rounded-lg border border-[#10B981] text-xs">
                    <CheckCircle2 className="w-4 h-4 text-[#10B981] mt-0.5 flex-shrink-0" />
                    <p className="text-[#10B981]">当前总结由后端总结服务生成</p>
                  </div>
                )}
                {meeting.summaryProvider === 'backend' && meeting.errorMessage && (
                  <div className="flex items-start gap-2 px-3 py-2 bg-[#FEE2E2] rounded-lg border border-[#EF4444] text-xs">
                    <AlertCircle className="w-4 h-4 text-[#EF4444] mt-0.5 flex-shrink-0" />
                    <p className="text-[#EF4444]">总结生成失败：{meeting.errorMessage}</p>
                  </div>
                )}
                {meeting.summaryProvider === 'manual' && (
                  <div className="flex items-start gap-2 px-3 py-2 bg-[#EEF8FC] rounded-lg border border-[#061B35] text-xs">
                    <CheckCircle2 className="w-4 h-4 text-[#061B35] mt-0.5 flex-shrink-0" />
                    <p className="text-[#061B35]">当前总结已由用户手动编辑</p>
                  </div>
                )}
                {/* 阶段 10B-4：Transcription provider 信息 */}
                {meeting.transcriptionProvider && (
                  <div className="flex items-center gap-2 px-3 py-2 bg-[#F0F9FF] rounded-lg border border-[#0EA5E9] text-xs">
                    <FileText className="w-4 h-4 text-[#0EA5E9] flex-shrink-0" />
                    <p className="text-[#06162E]">
                      <strong>转写：</strong>
                      {meeting.transcriptionProvider === 'whisperx' && `WhisperX / ${meeting.transcriptionModel || 'unknown'}`}
                      {meeting.transcriptionProvider === 'backend' && '后端 Whisper'}
                      {meeting.transcriptionProvider === 'fallback' && '本地 fallback'}
                      {meeting.transcriptionProvider === 'manual' && '手动输入'}
                      {meeting.diarizationEnabled && meeting.diarizationProvider && (
                        <span className="ml-2">
                          <strong>说话人分离：</strong>{meeting.diarizationProvider} / {meeting.diarizationModel || 'unknown'}
                        </span>
                      )}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-[#536172] mx-auto mb-4" />
                <p className="text-[#536172]">该会议尚未生成总结</p>
                {meeting.status === 'failed' && meeting.errorMessage && (
                  <p className="text-sm text-[#FF6B6B] mt-2">错误：{meeting.errorMessage}</p>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'transcript' && (
          <div className="space-y-4">
            {/* 对比模式标题栏 */}
            <div className="bg-white rounded-2xl p-4 border-2 border-[#D6E1EA]">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-[#061B35]" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-[#06162E]">文字稿对比</h2>
                    <p className="text-xs text-[#536172] mt-1">左侧为原始转录，右侧为 LLM 优化后的文字稿</p>
                  </div>
                </div>
                {!isEditingTranscript && !meeting.transcript && (
                  <button
                    onClick={() => setIsEditingTranscript(true)}
                    className="px-4 py-2 bg-[#061B35] text-white rounded-lg text-sm hover:bg-[#08213F] transition-colors"
                  >
                    粘贴文字稿
                  </button>
                )}
                {!isEditingTranscript && (meeting.transcriptTurns || meeting.transcript) && (
                  <div className="flex gap-2">
                    <button
                      onClick={handleEnhanceTranscript}
                      disabled={isEnhancing || !meeting.transcriptTurns || meeting.transcriptTurns.length === 0}
                      className="flex items-center gap-2 px-4 py-2 bg-[#10B981] text-white rounded-lg text-sm hover:bg-[#059669] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title={meeting.isEnhanced ? "重新生成增强文字稿" : "使用 LLM 优化转录文本"}
                    >
                      {isEnhancing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          优化中...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          {meeting.isEnhanced ? '重新优化' : 'LLM 优化'}
                        </>
                      )}
                    </button>
                    {meeting.isEnhanced && (
                      <span className="px-3 py-1.5 bg-[#D1FAE5] text-[#065F46] text-xs rounded-full flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        已优化
                      </span>
                    )}
                  </div>
                )}
                {isEditingTranscript && (
                  <button
                    onClick={() => setIsEditingTranscript(false)}
                    className="px-4 py-2 border border-[#D6E1EA] rounded-lg text-sm text-[#06162E] hover:bg-[#EEF8FC] transition-colors"
                  >
                    取消
                  </button>
                )}
              </div>
            </div>

            {/* 双栏对比布局 */}
            {!isEditingTranscript && (meeting.transcriptTurns || meeting.transcript) && (
              <div className="grid grid-cols-2 gap-4">
                {/* 左栏：原始文字稿 */}
                <div className="bg-white rounded-2xl p-5 border-2 border-[#E8E8E8]">
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b-2 border-[#E8E8E8]">
                    <div className="w-8 h-8 bg-[#F3F4F6] rounded-lg flex items-center justify-center">
                      <FileText className="w-4 h-4 text-[#666]" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-[#333]">原始文字稿</h3>
                      <p className="text-xs text-[#999] mt-0.5">Whisper 转录结果</p>
                    </div>
                  </div>

                  {/* 原始转录内容 */}
                  {meeting.transcriptTurns && meeting.transcriptTurns.length > 0 ? (
                    <div className="space-y-2">
                      {meeting.transcriptTurns.map((turn, index) => (
                        <div key={index} className="p-3 bg-[#F9F9F9] rounded-lg border-l-3 border-[#999]">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="text-xs font-medium text-[#666] bg-[#E8E8E8] px-2 py-0.5 rounded">
                              {turn.speaker}
                            </span>
                            <span className="text-xs text-[#999]">
                              {formatTimestamp(turn.start)} - {formatTimestamp(turn.end)}
                            </span>
                          </div>
                          <p className="text-sm text-[#333] whitespace-pre-line leading-relaxed">{turn.text}</p>
                        </div>
                      ))}
                    </div>
                  ) : meeting.transcript ? (
                    <div className="space-y-3">
                      {meeting.transcript.split('\n\n').map((paragraph, index) => (
                        <div key={index} className="p-3 bg-[#F9F9F9] rounded-lg">
                          <p className="text-sm text-[#333] whitespace-pre-line leading-relaxed">{paragraph}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <FileText className="w-10 h-10 text-[#CCC] mx-auto mb-3" />
                      <p className="text-sm text-[#999]">暂无原始文字稿</p>
                    </div>
                  )}
                </div>

                {/* 右栏：LLM 优化文字稿 */}
                <div className="bg-white rounded-2xl p-5 border-2 border-[#10B981]">
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b-2 border-[#10B981]/30">
                    <div className="w-8 h-8 bg-[#D1FAE5] rounded-lg flex items-center justify-center">
                      <FileText className="w-4 h-4 text-[#10B981]" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-[#06162E]">LLM 优化文字稿</h3>
                      <p className="text-xs text-[#10B981] mt-0.5">AI 智能修正后的版本</p>
                    </div>
                  </div>

                  {/* LLM 优化内容 */}
                  {meeting.enhancedTranscriptTurns && meeting.enhancedTranscriptTurns.length > 0 ? (
                    <div className="space-y-2">
                      {meeting.enhancedTranscriptTurns.map((turn, index) => (
                        <div key={index} className="p-3 bg-[#F0FDF4] rounded-lg border-l-3 border-[#10B981]">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="text-xs font-medium text-[#065F46] bg-[#D1FAE5] px-2 py-0.5 rounded">
                              {turn.speaker}
                            </span>
                            <span className="text-xs text-[#10B981]">
                              {formatTimestamp(turn.start)} - {formatTimestamp(turn.end)}
                            </span>
                          </div>
                          <p className="text-sm text-[#064E3B] whitespace-pre-line leading-relaxed">{turn.text}</p>
                        </div>
                      ))}
                      <div className="mt-3 p-2 bg-[#D1FAE5] rounded-lg border border-[#10B981]/30 text-xs text-[#065F46]">
                        <p>✨ 由 {meeting.enhancementProvider || 'AI'} ({meeting.enhancementModel || 'deepseek-chat'}) 优化</p>
                      </div>
                    </div>
                  ) : meeting.isEnhanced ? (
                    <div className="text-center py-8">
                      <FileText className="w-10 h-10 text-[#A7F3D0] mx-auto mb-3" />
                      <p className="text-sm text-[#10B981]">优化文字稿已清除</p>
                      <p className="text-xs text-[#6EE7B7] mt-1">请重新优化</p>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Sparkles className="w-10 h-10 text-[#A7F3D0] mx-auto mb-3" />
                      <p className="text-sm text-[#10B981]">暂无优化文字稿</p>
                      <p className="text-xs text-[#6EE7B7] mt-1">点击上方"LLM 优化"按钮生成</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Provider 信息 */}
            {!isEditingTranscript && (meeting.transcriptTurns || meeting.transcript) && (
              <div className="bg-white rounded-xl p-4 border border-[#D6E1EA]">
                <div className="flex items-center flex-wrap gap-6 text-xs">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#536172]" />
                    <span className="text-[#536172]">
                      <strong>转写：</strong>
                      {meeting.transcriptionProvider === 'whisperx' && `WhisperX / ${meeting.transcriptionModel || 'unknown'}`}
                      {meeting.transcriptionProvider === 'backend' && '后端 Whisper'}
                      {meeting.transcriptionProvider === 'fallback' && '本地 fallback'}
                      {meeting.transcriptionProvider === 'manual' && '手动输入'}
                    </span>
                  </div>
                  {meeting.diarizationEnabled && meeting.diarizationProvider && (
                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-[#536172]" />
                      <span className="text-[#536172]">
                        <strong>说话人分离：</strong>{meeting.diarizationProvider} / {meeting.diarizationModel || 'unknown'}
                      </span>
                    </div>
                  )}
                  {meeting.enhancementProvider && (
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[#10B981]" />
                      <span className="text-[#065F46]">
                        <strong>优化：</strong>{meeting.enhancementProvider} / {meeting.enhancementModel || 'unknown'}
                      </span>
                    </div>
                  )}
                </div>
                {meeting.alignmentStatus === 'failed' && meeting.alignmentError && (
                  <div className="flex items-start gap-2 mt-3 px-3 py-2 bg-[#FFF7ED] rounded-lg border border-[#F59E0B] text-xs">
                    <AlertCircle className="w-4 h-4 text-[#F59E0B] mt-0.5 flex-shrink-0" />
                    <p className="text-[#F59E0B]">词级对齐失败，当前使用片段时间戳。错误：{meeting.alignmentError}</p>
                  </div>
                )}
              </div>
            )}

            {/* 编辑模式 */}
            {isEditingTranscript ? (
              <div className="bg-white rounded-2xl p-6 border-2 border-[#D6E1EA]">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-[#06162E] mb-2">
                      会议文字稿
                    </label>
                    <textarea
                      value={manualTranscript}
                      onChange={(e) => setManualTranscript(e.target.value)}
                      placeholder="请粘贴会议的文字稿，然后点击下方按钮生成总结..."
                      className="w-full h-64 px-4 py-3 bg-white border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:border-[#061B35] focus:ring-2 focus:ring-[#061B35]/20 transition-all resize-none"
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleSaveTranscript}
                      disabled={!manualTranscript.trim()}
                      className="flex-1 px-4 py-2 border border-[#D6E1EA] rounded-lg text-[#06162E] hover:bg-[#EEF8FC] transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      仅保存文字稿
                    </button>
                    <button
                      onClick={handleGenerateSummary}
                      disabled={!manualTranscript.trim()}
                      className="flex-1 px-4 py-2 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center justify-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      保存并生成总结
                    </button>
                  </div>
                  <p className="text-xs text-[#536172]">
                    系统将根据当前选择的模板「{getTemplateName()}」生成总结结构
                  </p>
                </div>
              </div>
            ) : !meeting.transcript && !meeting.transcriptTurns ? (
              <div className="bg-white rounded-2xl p-12 border-2 border-[#D6E1EA] text-center">
                <AlertCircle className="w-12 h-12 text-[#536172] mx-auto mb-4" />
                <p className="text-[#536172] mb-4">该会议尚未生成文字稿</p>
                {meeting.errorMessage && (
                  <p className="text-sm text-[#FF6B6B] mb-4">{meeting.errorMessage}</p>
                )}
                <button
                  onClick={() => setIsEditingTranscript(true)}
                  className="px-6 py-2 bg-[#061B35] text-white rounded-lg text-sm hover:bg-[#08213F] transition-colors"
                >
                  粘贴会议文字稿
                </button>
              </div>
            ) : null}
          </div>
        )}

        {activeTab === 'action' && (
          <div className="bg-white rounded-2xl p-6 border border-[#D6E1EA]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#FFE7E7] rounded-lg flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-[#FF6B6B]" />
                </div>
                <h2 className="text-xl font-semibold text-[#06162E]">待办事项</h2>
                <span className="px-2 py-1 bg-[#EEF8FC] text-[#061B35] text-xs rounded-full">
                  {meetingActions.length}
                </span>
              </div>
              <button
                onClick={() => setIsAddingAction(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-[#061B35] text-white rounded-lg text-sm hover:bg-[#08213F] transition-colors"
              >
                <Plus className="w-4 h-4" />
                添加待办
              </button>
            </div>

            {/* Add new action item form */}
            {isAddingAction && (
              <div className="mb-4 p-4 bg-[#EEF8FC] rounded-xl space-y-3">
                <textarea
                  value={newActionContent}
                  onChange={(e) => setNewActionContent(e.target.value)}
                  placeholder="输入待办事项内容..."
                  className="w-full px-3 py-2 text-sm text-[#06162E] bg-white border border-[#D6E1EA] rounded-lg focus:outline-none focus:border-[#061B35] resize-none"
                  rows={2}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) handleAddAction()
                    if (e.key === 'Escape') {
                      setNewActionContent('')
                      setIsAddingAction(false)
                    }
                  }}
                />
                <div className="flex items-center justify-between">
                  <p className="text-xs text-[#536172]">Ctrl+Enter 快速保存</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setNewActionContent('')
                        setIsAddingAction(false)
                      }}
                      className="px-3 py-1.5 text-sm text-[#536172] hover:text-[#06162E] transition-colors"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleAddAction}
                      disabled={!newActionContent.trim()}
                      className="px-3 py-1.5 bg-[#10B981] text-white rounded-lg text-sm hover:bg-[#059669] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      添加
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Action items list */}
            {meetingActions.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle2 className="w-12 h-12 text-[#536172] mx-auto mb-4" />
                <p className="text-[#536172]">暂无待办事项</p>
                <p className="text-sm text-[#536172] mt-2">点击上方"添加待办"按钮创建新待办</p>
              </div>
            ) : (
              <div className="space-y-3">
                {meetingActions.map((action) => (
                  <div
                    key={action.id}
                    className={`p-4 rounded-xl border transition-all ${
                      action.status === 'done'
                        ? 'bg-[#F0FDF4] border-[#10B981] opacity-75'
                        : action.status === 'in_progress'
                        ? 'bg-[#FEF3C7] border-[#F59E0B]'
                        : 'bg-white border-[#D6E1EA]'
                    }`}
                  >
                    {editingActionId === action.id ? (
                      <div className="space-y-3">
                        <textarea
                          value={editActionContent}
                          onChange={(e) => setEditActionContent(e.target.value)}
                          placeholder="待办事项内容"
                          className="w-full px-3 py-2 text-sm text-[#06162E] bg-white border border-[#D6E1EA] rounded-lg focus:outline-none focus:border-[#061B35] resize-none"
                          rows={2}
                          autoFocus
                        />
                        <div className="grid grid-cols-2 gap-3">
                          <input
                            type="text"
                            value={editActionOwner}
                            onChange={(e) => setEditActionOwner(e.target.value)}
                            placeholder="负责人（可选）"
                            className="px-3 py-2 text-sm text-[#06162E] bg-white border border-[#D6E1EA] rounded-lg focus:outline-none focus:border-[#061B35]"
                          />
                          <input
                            type="date"
                            value={editActionDueDate}
                            onChange={(e) => setEditActionDueDate(e.target.value)}
                            className="px-3 py-2 text-sm text-[#06162E] bg-white border border-[#D6E1EA] rounded-lg focus:outline-none focus:border-[#061B35]"
                          />
                        </div>
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={handleCancelActionEdit}
                            className="px-3 py-1.5 text-sm text-[#536172] hover:text-[#06162E] transition-colors"
                          >
                            取消
                          </button>
                          <button
                            onClick={handleSaveActionEdit}
                            disabled={!editActionContent.trim()}
                            className="px-3 py-1.5 bg-[#10B981] text-white rounded-lg text-sm hover:bg-[#059669] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                          >
                            <Save className="w-3 h-3" />
                            保存
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start gap-3">
                        <button
                          onClick={() => handleToggleActionStatus(action.id, action.status)}
                          className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                            action.status === 'done'
                              ? 'bg-[#10B981] border-[#10B981] text-white'
                              : action.status === 'in_progress'
                              ? 'bg-[#F59E0B] border-[#F59E0B] text-white'
                              : 'border-[#536172] hover:border-[#061B35]'
                          }`}
                          title={action.status === 'done' ? '标记为未完成' : action.status === 'in_progress' ? '标记为已完成' : '标记为进行中'}
                        >
                          {action.status === 'done' && <CheckCircle2 className="w-3 h-3" />}
                          {action.status === 'in_progress' && <div className="w-2 h-2 bg-white rounded-full animate-pulse" />}
                        </button>
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm ${
                            action.status === 'done' ? 'line-through text-[#536172]' : 'text-[#06162E]'
                          }`}>
                            {action.content}
                          </p>
                          {action.owner && (
                            <p className="text-xs text-[#536172] mt-1">
                              负责人: {action.owner}
                            </p>
                          )}
                          {action.dueDate && (
                            <p className="text-xs text-[#536172] mt-1">
                              截止日期: {action.dueDate}
                            </p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              action.status === 'done'
                                ? 'bg-[#10B981] text-white'
                                : action.status === 'in_progress'
                                ? 'bg-[#F59E0B] text-white'
                                : 'bg-[#EEF8FC] text-[#061B35]'
                            }`}>
                              {action.status === 'done' && '已完成'}
                              {action.status === 'in_progress' && '进行中'}
                              {action.status === 'todo' && '待处理'}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleStartEditAction(action)}
                          className="flex-shrink-0 p-1.5 text-[#536172] hover:text-[#061B35] hover:bg-[#EEF8FC] rounded-lg transition-colors"
                          title="编辑待办"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteAction(action.id)}
                          className="flex-shrink-0 p-1.5 text-[#536172] hover:text-[#FF6B6B] hover:bg-[#FFE7E7] rounded-lg transition-colors"
                          title="删除待办"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'info' && (
          <div className="bg-white rounded-2xl p-6 border border-[#D6E1EA]">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-[#061B35]" />
              </div>
              <h2 className="text-xl font-semibold text-[#06162E]">会议信息</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <Calendar className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">会议日期</h3>
                  <p className="text-sm text-[#536172]">{meeting.date}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <Clock className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">会议时长</h3>
                  <p className="text-sm text-[#536172]">{meeting.duration}</p>
                </div>
              </div>

              {meeting.participants && meeting.participants.length > 0 && (
                <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                  <Users className="w-5 h-5 text-[#536172] mt-0.5" />
                  <div>
                    <h3 className="font-medium text-[#06162E] mb-1">参会人员</h3>
                    <p className="text-sm text-[#536172]">{meeting.participants.join(', ')}</p>
                  </div>
                </div>
              )}

              {meeting.audioFileName && (
                <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                  <FileText className="w-5 h-5 text-[#536172] mt-0.5" />
                  <div>
                    <h3 className="font-medium text-[#06162E] mb-1">音频文件</h3>
                    <p className="text-sm text-[#536172]">{meeting.audioFileName}</p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <FileText className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">使用模板</h3>
                  <p className="text-sm text-[#536172]">{getTemplateName()}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <AlertCircle className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">处理状态</h3>
                  <p className="text-sm text-[#536172]">
                    {meeting.status === 'completed' && '已完成'}
                    {meeting.status === 'uploaded' && '已上传，等待处理'}
                    {meeting.status === 'transcribing' && '正在转录'}
                    {meeting.status === 'summarizing' && '正在生成总结'}
                    {meeting.status === 'failed' && '处理失败'}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <Clock className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">创建时间</h3>
                  <p className="text-sm text-[#536172]">{new Date(meeting.createdAt).toLocaleString('zh-CN')}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <Clock className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">更新时间</h3>
                  <p className="text-sm text-[#536172]">{new Date(meeting.updatedAt).toLocaleString('zh-CN')}</p>
                </div>
              </div>

              {meeting.backendMeetingId && (
                <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                  <FileText className="w-5 h-5 text-[#536172] mt-0.5" />
                  <div>
                    <h3 className="font-medium text-[#06162E] mb-1">后端会议 ID</h3>
                    <p className="text-sm text-[#536172] font-mono">{meeting.backendMeetingId}</p>
                  </div>
                </div>
              )}

              {meeting.errorMessage && (
                <div className="flex items-start gap-3 p-4 bg-[#FFE7E7] rounded-lg border border-[#FF6B6B]">
                  <AlertCircle className="w-5 h-5 text-[#FF6B6B] mt-0.5" />
                  <div>
                    <h3 className="font-medium text-[#06162E] mb-1">错误信息</h3>
                    <p className="text-sm text-[#FF6B6B]">{meeting.errorMessage}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Export Dialog */}
      {showExportDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-[#06162E]">导出会议</h3>
              <button
                onClick={() => setShowExportDialog(false)}
                className="p-1.5 text-[#536172] hover:text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  导出格式
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['markdown', 'txt', 'json'] as ExportFormat[]).map((format) => (
                    <button
                      key={format}
                      onClick={() => setSelectedFormat(format)}
                      className={`px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                        selectedFormat === format
                          ? 'bg-[#061B35] text-white'
                          : 'bg-[#EEF8FC] text-[#06162E] hover:bg-[#DCEBFF]'
                      }`}
                    >
                      {format === 'markdown' && 'Markdown'}
                      {format === 'txt' && 'TXT'}
                      {format === 'json' && 'JSON'}
                    </button>
                  ))}
                </div>
                <div className="mt-2 text-xs text-[#536172]">
                  {selectedFormat === 'markdown' && '格式化的文档，适合阅读和编辑'}
                  {selectedFormat === 'txt' && '纯文本格式，兼容性最好'}
                  {selectedFormat === 'json' && '结构化数据，适合程序处理'}
                </div>
              </div>

              {/* Options */}
              <div className="space-y-2">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeTranscript}
                    onChange={(e) => setIncludeTranscript(e.target.checked)}
                    className="w-4 h-4 text-[#061B35] border-[#D6E1EA] rounded focus:ring-[#061B35]"
                  />
                  <span className="text-sm text-[#06162E]">包含完整文字稿</span>
                </label>
                {includeTranscript && !meeting?.transcript && (
                  <p className="text-xs text-[#FF6B6B] ml-7">当前会议暂无文字稿</p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowExportDialog(false)}
                  className="flex-1 px-4 py-2.5 border border-[#D6E1EA] rounded-lg text-sm text-[#06162E] hover:bg-[#EEF8FC] transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmExport}
                  className="flex-1 px-4 py-2.5 bg-[#061B35] text-white rounded-lg text-sm hover:bg-[#08213F] transition-colors flex items-center justify-center gap-2"
                >
                  <FileDown className="w-4 h-4" />
                  导出
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
