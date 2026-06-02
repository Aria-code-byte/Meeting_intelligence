import { useState, useEffect, useCallback, useRef } from 'react'
import { Sidebar } from './components/Sidebar'
import { TopNav } from './components/TopNav'
import { DashboardPage } from './pages/DashboardPage'
import { MeetingLibraryPage } from './pages/MeetingLibraryPage'
import { TemplatePage } from './pages/TemplatePage'
import { SummaryDetailPage } from './pages/SummaryDetailPage'
import { useMeetings, useTemplates } from './store/useAppStore'
import { meetingStorage } from './lib/storage'
import { transcribeMeetingAudio, type TranscriptionResult } from './services/transcriptionService'
import { generateMeetingSummary, type SummaryResult, markSummaryAsManual } from './services/summaryGenerationService'
import { processMeeting, getDefaultTemplate, type FallbackResult } from './services/meetingProcessingService'
import { enhanceTranscript, type EnhancementResult } from './services/enhancementService'
import type { Meeting } from './types/models'

export type PageType = 'dashboard' | 'meetings' | 'templates' | 'summary' | 'recordings' | 'action' | 'library'

// Legacy type alias for compatibility
export type MeetingStatus = Meeting['status']

// URL helper functions
function getUrlState() {
  const params = new URLSearchParams(window.location.search)
  const pageParam = params.get('page') as PageType

  // Validate page parameter
  const validPages: PageType[] = ['dashboard', 'meetings', 'templates', 'summary', 'recordings', 'action', 'library']
  const page = validPages.includes(pageParam) ? pageParam : 'dashboard'

  const meetingId = params.get('meetingId') || null

  return { page, meetingId }
}

function setUrlState(page: PageType, meetingId: string | null = null) {
  const params = new URLSearchParams()
  params.set('page', page)
  if (meetingId) {
    params.set('meetingId', meetingId)
  }
  const newUrl = `${window.location.pathname}?${params.toString()}`
  window.history.pushState({ page, meetingId }, '', newUrl)
}

/**
 * 格式化音频时长（秒 → Xm Ys 格式）
 */
function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0m'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  if (minutes === 0) {
    return `${remainingSeconds}s`
  } else if (remainingSeconds === 0) {
    return `${minutes}m`
  } else {
    return `${minutes}m ${remainingSeconds}s`
  }
}

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>(() => getUrlState().page)
  const [currentMeetingId, setCurrentMeetingId] = useState<string | null>(() => getUrlState().meetingId)

  // Use new data store hooks
  const { meetings, loading: meetingsLoading, createMeeting, deleteMeeting, updateMeeting, getRecentMeetings, getMeetingById } = useMeetings()
  const { templates, loading: templatesLoading, createTemplate, deleteTemplate, updateTemplate, setDefaultTemplate } = useTemplates()

  // Get current meeting from store based on meetingId
  const currentMeeting = currentMeetingId ? getMeetingById(currentMeetingId) : null

  // Force repair on mount to fix any existing duplicate IDs
  useEffect(() => {
    meetingStorage.repair()
  }, [])

  // Sync URL with state changes
  useEffect(() => {
    const handlePopState = () => {
      const urlState = getUrlState()
      setCurrentPage(urlState.page)
      setCurrentMeetingId(urlState.meetingId)
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // Clear invalid meetingId
  useEffect(() => {
    if (currentMeetingId && !currentMeeting) {
      setCurrentMeetingId(null)
      if (currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library') {
        setCurrentPage('meetings')
        setUrlState('meetings', null)
      }
    }

    // Handle summary page without meetingId
    if ((currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library') && !currentMeetingId) {
      setCurrentPage('meetings')
      setUrlState('meetings', null)
    }
  }, [currentMeetingId, currentMeeting, currentPage])

  // Processing state for dashboard
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processingStage, setProcessingStage] = useState<'idle' | 'selected' | 'uploading' | 'transcribing' | 'enhancing' | 'summarizing' | 'completed' | 'failed'>('idle')
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingMeetingId, setProcessingMeetingId] = useState<string | null>(null)

  // Search state for meetings and templates
  const [meetingSearchQuery, setMeetingSearchQuery] = useState('')
  const [templateSearchQuery, setTemplateSearchQuery] = useState('')

  // 阶段 10B-5-Q5-R3：用于去重进度日志的 ref
  const lastProgressLogRef = useRef<{
    stage?: string
    progress?: number
    message?: string
  } | null>(null)

  // Handle start processing with template selection
  const handleStartProcessing = async (file: File, title: string, templateId: string) => {
    console.log('[App.tsx] handleStartProcessing 被调用:', {
      fileName: file.name,
      fileSize: file.size,
      title,
      templateId,
    });
    try {
      // Check for duplicate meeting (same title and date)
      const today = new Date().toISOString().split('T')[0]
      const isDuplicate = meetings.some(m =>
        m.title === title &&
        m.date === today
      )

      if (isDuplicate) {
        alert('今天已经存在同名会议，请使用不同的标题。')
        setProcessingStage('idle')
        setProcessingProgress(0)
        setSelectedFile(null)
        return
      }

      // Get template for snapshot
      const selectedTemplate = templates.find(t => t.id === templateId)

      // Create meeting record with selected template and snapshot
      const newMeeting = createMeeting({
        title,
        date: today,
        duration: '0m',
        participants: [],
        status: 'uploaded',
        progress: 20,
        templateId: templateId,
        templateName: selectedTemplate?.name,
        templateSnapshot: selectedTemplate ? {
          id: selectedTemplate.id,
          name: selectedTemplate.name,
          structure: selectedTemplate.structure,
          prompt: selectedTemplate.prompt,
        } : undefined,
        audioFileName: file.name,
        transcriptionProvider: 'fallback',
        transcriptionIsFallback: true,
      })

      if (!newMeeting) {
        alert('创建会议记录失败')
        setProcessingStage('failed')
        return
      }

      setProcessingMeetingId(newMeeting.id)

      // 步骤 1: 调用转录服务
      let transcriptionResult: TranscriptionResult
      try {
        setProcessingStage('transcribing');
        setProcessingProgress(10);

        transcriptionResult = await transcribeMeetingAudio({
          meetingId: newMeeting.id,
          file,
          audioFileName: file.name,
          // 阶段 10B-5-Q4：传入进度回调，更新真实进度
          // 阶段 10B-5-Q5-R3：使用 useRef 去重，避免日志刷屏
          onProgress: (stage, progress, message) => {
            // 阶段 10B-5-Q5-R3：日志去重，只在状态真正变化时打印
            const current = { stage, progress, message }
            const prev = lastProgressLogRef.current

            const changed =
              !prev ||
              prev.stage !== current.stage ||
              prev.progress !== current.progress ||
              prev.message !== current.message

            if (changed) {
              console.log('[App.tsx] 转录进度更新:', current)
              lastProgressLogRef.current = current
            }

            // UI 更新必须每次都执行，不要被日志去重逻辑挡住
            // 后端进度范围：10-100
            setProcessingProgress(Math.max(10, Math.min(90, progress)))
          }
        })
      } catch (error) {
        console.error('[App.tsx] 转录服务调用失败:', error);
        transcriptionResult = {
          transcript: '',
          provider: 'fallback',
          isFallback: true,
          error: '转录服务暂不可用'
        }
      }

      // 暂存所有更新数据，最后一次性更新
      const meetingUpdateData: any = {
        transcript: transcriptionResult.transcript,
        transcriptTurns: transcriptionResult.transcriptTurns,
        transcriptionProvider: transcriptionResult.provider,
        transcriptionModel: transcriptionResult.transcriptionModel,
        diarizationEnabled: transcriptionResult.diarizationEnabled,
        diarizationProvider: transcriptionResult.diarizationProvider,
        diarizationModel: transcriptionResult.diarizationModel,
        alignmentStatus: transcriptionResult.alignmentStatus,
        alignmentError: transcriptionResult.alignmentError,
        transcriptionIsFallback: transcriptionResult.isFallback,
        duration: transcriptionResult.audioDuration
          ? formatDuration(transcriptionResult.audioDuration)
          : '0m',
        status: 'transcribing',
        progress: 40,
        lastProcessedAt: new Date().toISOString(),
      }

      // 阶段 10B-5-R：检查 transcript 是否有效
      const hasValidTranscript = transcriptionResult.transcript &&
                                 transcriptionResult.transcript.trim().length > 0;

      if (!hasValidTranscript) {
        console.warn('[App.tsx] 转录结果为空，中断总结流程');
        updateMeeting(newMeeting.id, {
          ...meetingUpdateData,
          status: 'failed',
          errorMessage: transcriptionResult.error || '转录失败：未获取到文字稿',
          summary: '',
          summaryProvider: undefined,
          summaryIsFallback: undefined,
        });
        setProcessingStage('failed');
        return;
      }

      // 步骤 1.5: 调用 LLM 增强服务
      let enhancedTranscriptTurns = null
      if (transcriptionResult.transcriptTurns && transcriptionResult.transcriptTurns.length > 0) {
        try {
          console.log('[App.tsx] 开始 LLM 增强转录，turns 数量:', transcriptionResult.transcriptTurns.length)
          setProcessingStage('enhancing')
          setProcessingProgress(60)

          const enhancementResult: EnhancementResult = await enhanceTranscript(
            transcriptionResult.transcriptTurns,
            'deepseek',
            'deepseek-chat'
          )

          console.log('[App.tsx] LLM 增强响应:', {
            success: enhancementResult.success,
            hasEnhancedTurns: !!enhancementResult.enhancedTranscriptTurns,
            enhancedTurnsCount: enhancementResult.enhancedTranscriptTurns?.length || 0,
            provider: enhancementResult.provider,
            model: enhancementResult.model,
            error: enhancementResult.error,
            processingTimeMs: enhancementResult.processingTimeMs,
          })

          if (enhancementResult.success && enhancementResult.enhancedTranscriptTurns) {
            enhancedTranscriptTurns = enhancementResult.enhancedTranscriptTurns
            console.log('[App.tsx] LLM 增强成功，turns 数量:', enhancedTranscriptTurns.length)
            // 暂存到 updateData，稍后统一更新
            meetingUpdateData.enhancedTranscriptTurns = enhancedTranscriptTurns
            meetingUpdateData.enhancementProvider = 'deepseek'
            meetingUpdateData.enhancementModel = 'deepseek-chat'
            meetingUpdateData.isEnhanced = true
            meetingUpdateData.enhancementTime = new Date().toISOString()
          } else {
            console.warn('[App.tsx] LLM 增强失败:', enhancementResult.error)
          }
        } catch (error) {
          console.error('[App.tsx] LLM 增强调用失败:', error)
          console.error('[App.tsx] 错误详情:', error instanceof Error ? error.message : String(error))
        }
      } else {
        console.log('[App.tsx] 跳过 LLM 增强：没有 transcriptTurns')
      }

      // 步骤 2: 调用总结服务
      let summaryResult: SummaryResult
      try {
        setProcessingStage('summarizing')
        setProcessingProgress(92)

        summaryResult = await generateMeetingSummary({
          meetingId: newMeeting.id,
          transcript: transcriptionResult.transcript || '',
          templateSnapshot: selectedTemplate ? {
            id: selectedTemplate.id,
            name: selectedTemplate.name,
            structure: selectedTemplate.structure,
            prompt: selectedTemplate.prompt,
          } : undefined,
        })

        setProcessingProgress(100)
      } catch (error) {
        console.error('[App.tsx] 总结服务调用失败:', error)
        summaryResult = {
          summary: '',
          provider: 'backend',
          isFallback: false,
          error: error instanceof Error ? error.message : '总结服务调用失败'
        }
      }

      // 一次性更新所有数据（转录 + 增强 + 总结）
      console.log('[App.tsx] 写入完整会议数据:', {
        hasTranscript: !!meetingUpdateData.transcript,
        hasTranscriptTurns: !!meetingUpdateData.transcriptTurns,
        hasEnhanced: !!meetingUpdateData.enhancedTranscriptTurns,
        summaryProvider: summaryResult.provider,
        summaryLength: summaryResult.summary?.length || 0,
      })

      updateMeeting(newMeeting.id, {
        ...meetingUpdateData,
        summary: summaryResult.summary,
        summaryProvider: summaryResult.provider,
        summaryIsFallback: summaryResult.isFallback,
        templateId: selectedTemplate?.id,
        status: summaryResult.error ? 'failed' : 'completed',
        progress: summaryResult.error ? 0 : 100,
        errorMessage: summaryResult.error,
      })

      setProcessingStage(summaryResult.error ? 'failed' : 'completed')
      setProcessingProgress(100)
      // Keep processingMeetingId for "View Results" button to use

    } catch (error) {
      alert(`处理启动失败: ${error}`)
      setProcessingStage('failed')
      setProcessingMeetingId(null)
    }
  }

  const handlePageChange = (page: PageType) => {
    setCurrentPage(page)
    setUrlState(page, null)

    // Reset processing state when returning to dashboard
    if (page === 'dashboard') {
      setProcessingStage('idle')
      setSelectedFile(null)
      setProcessingProgress(0)
      setProcessingMeetingId(null)
    }
  }

  // 阶段 5 回归修复：处理新建模板按钮点击
  const handleCreateTemplate = () => {
    console.log('[App.tsx] 新建模板按钮被点击')
    // 导航到模板页面并触发创建 modal
    setCurrentPage('templates')
    setUrlState('templates', null)
    // 使用 URL 参数触发 modal 打开
    const url = new URL(window.location.href)
    url.searchParams.set('create', 'true')
    window.history.replaceState({}, '', url)
    // 触发事件通知 TemplatePage
    window.dispatchEvent(new CustomEvent('open-template-create'))
  }

  const handleMeetingClick = (meeting: Meeting) => {
    // Verify meeting still exists in store
    const exists = meetings.find(m => m.id === meeting.id)
    if (!exists) {
      alert('该会议已被删除')
      return
    }
    console.log('[App.tsx] handleMeetingClick 被调用:', {
      meetingId: meeting.id,
      summaryProvider: meeting.summaryProvider,
      summaryIsFallback: meeting.summaryIsFallback,
    })
    setCurrentMeetingId(meeting.id)
    setCurrentPage('summary')
    setUrlState('summary', meeting.id)
  }

  // Wrap deleteMeeting to clear currentMeeting if needed
  const handleDeleteMeeting = (id: string) => {
    const deleted = deleteMeeting(id)
    if (deleted && currentMeetingId === id) {
      setCurrentMeetingId(null)
      setCurrentPage('meetings')
      setUrlState('meetings', null)
    }
    return deleted
  }

  // Clear currentMeeting if it was deleted elsewhere
  useEffect(() => {
    if (currentMeetingId && !getMeetingById(currentMeetingId)) {
      setCurrentMeetingId(null)
      if (currentPage === 'summary') {
        setCurrentPage('meetings')
        setUrlState('meetings', null)
      }
    }
  }, [meetings, currentMeetingId, currentPage, getMeetingById])

  const shouldShowDetailSidebar = currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library'

  return (
    <div className="flex h-screen bg-[#EEF8FC]">
      <Sidebar
        currentPage={currentPage}
        onPageChange={handlePageChange}
        showDetailVariant={shouldShowDetailSidebar}
        forceHighlight={currentPage === 'summary' ? 'meetings' : undefined}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNav
          currentPage={currentPage}
          meetingSearchQuery={meetingSearchQuery}
          onMeetingSearchChange={setMeetingSearchQuery}
          templateSearchQuery={templateSearchQuery}
          onTemplateSearchChange={setTemplateSearchQuery}
          onCreateTemplate={handleCreateTemplate}
        />

        <main className="flex-1 overflow-auto px-9 py-8">
          {meetingsLoading || templatesLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#536172]">加载中...</div>
            </div>
          ) : (
            <>
              {currentPage === 'dashboard' && (
                <DashboardPage
                  meetings={meetings}
                  templates={templates}
                  selectedFile={selectedFile}
                  processingStage={processingStage}
                  processingProgress={processingProgress}
                  processingMeetingId={processingMeetingId}
                  onFileSelect={setSelectedFile}
                  onProcessingStageChange={setProcessingStage}
                  onProcessingProgressChange={setProcessingProgress}
                  onMeetingAdd={(meeting) => {
                    // This is now handled by onStartProcessing
                  }}
                  onMeetingClick={handleMeetingClick}
                  onStartProcessing={handleStartProcessing}
                  onResetProcessing={() => {
                    setProcessingMeetingId(null)
                  }}
                />
              )}

              {currentPage === 'meetings' && (
                <MeetingLibraryPage
                  meetings={meetings}
                  templates={templates}
                  searchQuery={meetingSearchQuery}
                  onMeetingClick={handleMeetingClick}
                  onMeetingDelete={handleDeleteMeeting}
                  onMeetingStatusChange={(id, status) => {
                    updateMeeting(id, { status })
                  }}
                  onMeetingRename={(id, newTitle) => {
                    updateMeeting(id, { title: newTitle })
                  }}
                />
              )}

              {currentPage === 'templates' && (
                <TemplatePage
                  templates={templates}
                  searchQuery={templateSearchQuery}
                  onTemplateAdd={createTemplate}
                  onTemplateUpdate={updateTemplate}
                  onTemplateDelete={deleteTemplate}
                  onSetDefault={setDefaultTemplate}
                />
              )}

              {(currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library') && (
                <SummaryDetailPage
                  currentPage={currentPage}
                  meetingId={currentMeetingId}
                  templates={templates}
                  onBack={() => {
                    setCurrentPage('meetings')
                    setUrlState('meetings', null)
                  }}
                />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
