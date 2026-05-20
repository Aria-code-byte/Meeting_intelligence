import { useState, useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { TopNav } from './components/TopNav'
import { DashboardPage } from './pages/DashboardPage'
import { MeetingLibraryPage } from './pages/MeetingLibraryPage'
import { TemplatePage } from './pages/TemplatePage'
import { SummaryDetailPage } from './pages/SummaryDetailPage'
import { useMeetings, useTemplates } from './store/useAppStore'
import { meetingStorage } from './lib/storage'
import { processMeeting, getDefaultTemplate, type FallbackResult } from './services/meetingProcessingService'
import type { Meeting } from './types/models'

export type PageType = 'dashboard' | 'meetings' | 'templates' | 'summary' | 'recordings' | 'action' | 'library'

// Legacy type alias for compatibility
export type MeetingStatus = Meeting['status']

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard')
  const [currentMeeting, setCurrentMeeting] = useState<Meeting | null>(null)

  // Use new data store hooks
  const { meetings, loading: meetingsLoading, createMeeting, deleteMeeting, updateMeeting, getRecentMeetings } = useMeetings()
  const { templates, loading: templatesLoading, createTemplate, deleteTemplate } = useTemplates()

  // Force repair on mount to fix any existing duplicate IDs
  useEffect(() => {
    meetingStorage.repair()
  }, [])

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

      // Create meeting record with selected template
      const newMeeting = createMeeting({
        title,
        date: today,
        duration: '0m',
        participants: [],
        status: 'uploaded',
        progress: 20,
        templateId: templateId,
        audioFileName: file.name,
      })

      if (!newMeeting) {
        alert('创建会议记录失败')
        setProcessingStage('failed')
        return
      }

      setProcessingMeetingId(newMeeting.id)

      // 纯前端 fallback 模式：不调用后端
      await processMeeting({
        file,
        title,
        templateId,
        localMeetingId: newMeeting.id,
        onProgress: (stage, progress) => {
          setProcessingProgress(progress)
          setProcessingStage('uploading')
        },
        onComplete: (result: FallbackResult) => {
          // Fallback 模式：会议已创建，等待手动补全文字稿
          updateMeeting(newMeeting.id, {
            status: 'uploaded',
            progress: 20,
            errorMessage: result.message,
          })
          setProcessingStage('completed')
          setProcessingProgress(100)
          setProcessingMeetingId(null)
        },
        onError: (error) => {
          // 即使出错也保持会议记录
          updateMeeting(newMeeting.id, {
            status: 'uploaded',
            progress: 20,
            errorMessage: '后端转写服务暂不可用，请手动补充文字稿后生成总结。',
          })
          setProcessingStage('completed')
          setProcessingProgress(100)
          setProcessingMeetingId(null)
        },
      })

    } catch (error) {
      alert(`处理启动失败: ${error}`)
      setProcessingStage('failed')
      setProcessingMeetingId(null)
    }
  }

  const handlePageChange = (page: PageType) => {
    setCurrentPage(page)
  }

  const handleMeetingClick = (meeting: Meeting) => {
    setCurrentMeeting(meeting)
    setCurrentPage('summary')
  }

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
                  onFileSelect={setSelectedFile}
                  onProcessingStageChange={setProcessingStage}
                  onProcessingProgressChange={setProcessingProgress}
                  onMeetingAdd={(meeting) => {
                    // This is now handled by onStartProcessing
                  }}
                  onMeetingClick={handleMeetingClick}
                  onStartProcessing={handleStartProcessing}
                />
              )}

              {currentPage === 'meetings' && (
                <MeetingLibraryPage
                  meetings={meetings}
                  templates={templates}
                  searchQuery={meetingSearchQuery}
                  onMeetingClick={handleMeetingClick}
                  onMeetingDelete={deleteMeeting}
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
                  onTemplateAdd={createTemplate}
                  onTemplateDelete={deleteTemplate}
                />
              )}

              {(currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library') && (
                <SummaryDetailPage
                  currentPage={currentPage}
                  meeting={currentMeeting}
                  templates={templates}
                  onBack={() => setCurrentPage('dashboard')}
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
