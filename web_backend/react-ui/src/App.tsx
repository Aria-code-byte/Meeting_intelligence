import { useState, useEffect, useCallback } from 'react'
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
  const [processingStage, setProcessingStage] = useState<'idle' | 'selected' | 'uploading' | 'transcribing' | 'cleaning' | 'summarizing' | 'completed' | 'failed'>('idle')
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingMeetingId, setProcessingMeetingId] = useState<string | null>(null)

  // Search state for meetings and templates
  const [meetingSearchQuery, setMeetingSearchQuery] = useState('')
  const [templateSearchQuery, setTemplateSearchQuery] = useState('')

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
        transcriptionResult = await transcribeMeetingAudio({
          meetingId: newMeeting.id,
          file,
          audioFileName: file.name,
        })
      } catch (error) {
        transcriptionResult = {
          transcript: '',
          provider: 'fallback',
          isFallback: true,
          error: '转录服务暂不可用'
        }
      }

      // 更新转录结果
      updateMeeting(newMeeting.id, {
        transcript: transcriptionResult.transcript,
        transcriptionProvider: transcriptionResult.provider,
        transcriptionIsFallback: transcriptionResult.isFallback,
        status: 'transcribing',
        progress: 40,
        errorMessage: transcriptionResult.error,
        lastProcessedAt: new Date().toISOString(),
      })

      // 步骤 2: 调用总结服务
      let summaryResult: SummaryResult
      try {
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
      } catch (error) {
        summaryResult = {
          summary: '',
          provider: 'fallback',
          isFallback: true,
          error: '总结服务暂不可用'
        }
      }

      // 更新总结结果
      console.log('[App.tsx] 写入总结结果到 Meeting:', {
        summaryProvider: summaryResult.provider,
        summaryIsFallback: summaryResult.isFallback,
        summaryLength: summaryResult.summary.length,
      });
      updateMeeting(newMeeting.id, {
        summary: summaryResult.summary,
        summaryProvider: summaryResult.provider,
        summaryIsFallback: summaryResult.isFallback,
        status: summaryResult.error ? 'failed' : 'completed',
        progress: summaryResult.error ? 0 : 100,
        errorMessage: summaryResult.error,
        lastProcessedAt: new Date().toISOString(),
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
