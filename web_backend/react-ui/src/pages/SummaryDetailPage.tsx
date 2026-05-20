import { useState } from 'react'
import { ArrowLeft, Copy, RefreshCw, Download, CheckCircle2, FileText, Users, Calendar, Clock, AlertCircle, Save } from 'lucide-react'
import { ActionItemCard } from '../components/ActionItemCard'
import { useMeetings } from '../store/useAppStore'
import { generateFallbackSummary, validateTranscript } from '../services/summaryGenerationService'
import type { PageType } from '../App'
import type { Meeting } from '../types/models'

interface SummaryDetailPageProps {
  currentPage: PageType
  meeting: Meeting | null
  templates: any[]
  onBack: () => void
}

type TabType = 'summary' | 'transcript' | 'action' | 'info'

export function SummaryDetailPage({ currentPage, meeting, templates, onBack }: SummaryDetailPageProps) {
  const [activeTab, setActiveTab] = useState<TabType>('summary')
  const [copySuccess, setCopySuccess] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [manualTranscript, setManualTranscript] = useState('')
  const [isEditingTranscript, setIsEditingTranscript] = useState(false)

  const { updateMeeting } = useMeetings()

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

  const sidebarItems = [
    { id: 'summary' as TabType, label: 'AI 总结', count: null },
    { id: 'transcript' as TabType, label: '完整文字稿', count: null },
    { id: 'action' as TabType, label: '待办事项', count: 0 },
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
    if (!meeting) return

    let content = ''
    let filename = ''

    if (activeTab === 'summary' && meeting.summary) {
      content = meeting.summary
      filename = `summary_${meeting.id}.txt`
    } else if (activeTab === 'transcript' && meeting.transcript) {
      content = meeting.transcript
      filename = `transcript_${meeting.id}.txt`
    } else if (activeTab === 'info') {
      content = `会议标题：${meeting.title}\n日期：${meeting.date}\n模板：${getTemplateName()}\n状态：${meeting.status}`
      filename = `meeting_info_${meeting.id}.txt`
    }

    if (!content) return

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleRegenerate = () => {
    if (!meeting) return

    // Check if transcript exists
    if (!meeting.transcript && !isEditingTranscript) {
      alert('请先补充会议文字稿，再重新生成总结。')
      setActiveTab('transcript')
      setIsEditingTranscript(true)
      return
    }

    setRegenerating(true)

    // Generate summary based on template
    const template = templates.find(t => t.id === meeting.templateId)
    if (!template) {
      alert('未找到会议模板')
      setRegenerating(false)
      return
    }

    // Use the new summary generation service
    const summary = generateFallbackSummary({
      transcript: meeting.transcript || '',
      template,
      meeting,
    })

    // Update meeting
    updateMeeting(meeting.id, {
      summary,
      status: 'completed',
      errorMessage: undefined,
    })

    setTimeout(() => {
      setRegenerating(false)
    }, 1000)
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

    // Get template for this meeting
    const template = templates.find(t => t.id === meeting.templateId)
    if (!template) {
      alert('未找到会议模板')
      return
    }

    // Use the new summary generation service
    const summary = generateFallbackSummary({
      transcript: transcriptToUse,
      template,
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

  // Show loading state if no meeting
  if (!meeting) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-[#536172] mx-auto mb-4" />
          <p className="text-[#536172]">未找到会议信息</p>
          <button
            onClick={onBack}
            className="mt-4 px-4 py-2 bg-[#061B35] text-white rounded-lg hover:bg-[#08213F] transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-6">
      {/* Left Sidebar */}
      <div className="w-[270px] flex-shrink-0 space-y-4">
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
          <h1 className="text-3xl font-bold text-[#06162E]">
            {meeting.title}
          </h1>
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
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-[#061B35]" />
              </div>
              <h2 className="text-xl font-semibold text-[#06162E]">会议总结</h2>
            </div>

            {meeting.summary ? (
              <div className="text-[#06162E] leading-relaxed whitespace-pre-line">
                {meeting.summary}
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
          <div className="bg-white rounded-2xl p-6 border-2 border-[#D6E1EA]">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[#061B35]" />
                </div>
                <h2 className="text-xl font-semibold text-[#06162E]">完整文字稿</h2>
              </div>
              {!isEditingTranscript && !meeting.transcript && (
                <button
                  onClick={() => setIsEditingTranscript(true)}
                  className="px-4 py-2 bg-[#061B35] text-white rounded-lg text-sm hover:bg-[#08213F] transition-colors"
                >
                  粘贴文字稿
                </button>
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

            {/* Show transcript if exists */}
            {meeting.transcript && !isEditingTranscript ? (
              <div className="space-y-4">
                {meeting.transcript.split('\n\n').map((paragraph, index) => (
                  <div key={index} className="p-4 bg-[#EEF8FC] rounded-lg">
                    <p className="text-sm text-[#06162E] whitespace-pre-line">{paragraph}</p>
                  </div>
                ))}
              </div>
            ) : !isEditingTranscript ? (
              <div className="text-center py-12">
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
            ) : (
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
                <p className="text-xs text-[#536172] mt-2">
                  系统将根据当前选择的模板「{getTemplateName()}」生成总结结构
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'action' && (
          <div className="bg-white rounded-2xl p-6 border border-[#D6E1EA]">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#FFE7E7] rounded-lg flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-[#FF6B6B]" />
              </div>
              <h2 className="text-xl font-semibold text-[#06162E]">待办事项</h2>
            </div>

            <div className="text-center py-12">
              <p className="text-[#536172]">暂无待办事项</p>
              <p className="text-sm text-[#536172] mt-2">待办事项功能将在后续版本中完善</p>
            </div>
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
    </div>
  )
}
