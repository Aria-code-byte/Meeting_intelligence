import { useState, useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { TopNav } from './components/TopNav'
import { DashboardPage } from './pages/DashboardPage'
import { MeetingLibraryPage } from './pages/MeetingLibraryPage'
import { TemplatePage } from './pages/TemplatePage'
import { SummaryDetailPage } from './pages/SummaryDetailPage'
import { useMeetings, useTemplates } from './store/useAppStore'
import type { Meeting, SummaryTemplate } from './types/models'

export type PageType = 'dashboard' | 'meetings' | 'templates' | 'summary' | 'recordings' | 'action' | 'library'

// Legacy type aliases for compatibility with existing components
export type MeetingStatus = Meeting['status']

// Map new Meeting model to legacy component interface
export interface LegacyMeeting {
  id: number
  title: string
  date: string
  duration: string
  status: Meeting['status']
  progress: number
  participants: string[]
}

// Map new Template model to legacy component interface
export interface LegacyTemplate {
  id: number
  title: string
  description: string
  category: string
  isBuiltin: boolean
  tags: string[]
}

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard')
  const [currentMeeting, setCurrentMeeting] = useState<Meeting | null>(null)

  // Use new data store hooks
  const { meetings, loading: meetingsLoading, createMeeting, deleteMeeting, updateMeeting, getRecentMeetings } = useMeetings()
  const { templates, loading: templatesLoading, createTemplate, deleteTemplate } = useTemplates()

  // Processing state for dashboard
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processingStage, setProcessingStage] = useState<'idle' | 'selected' | 'uploading' | 'transcribing' | 'cleaning' | 'summarizing' | 'completed' | 'failed'>('idle')
  const [processingProgress, setProcessingProgress] = useState(0)

  const handlePageChange = (page: PageType) => {
    setCurrentPage(page)
  }

  const handleMeetingClick = (meeting: Meeting) => {
    setCurrentMeeting(meeting)
    setCurrentPage('summary')
  }

  const shouldShowDetailSidebar = currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library'

  // Convert new data models to legacy format for existing components
  const legacyMeetings: LegacyMeeting[] = meetings.map((m, index) => ({
    id: parseInt(m.id) || index + 1,
    title: m.title,
    date: m.date,
    duration: m.duration,
    status: m.status,
    progress: m.progress || (m.status === 'completed' ? 100 : m.status === 'processing' ? 50 : 0),
    participants: m.participants,
  }))

  const legacyTemplates: LegacyTemplate[] = templates.map((t, index) => ({
    id: parseInt(t.id) || index + 1,
    title: t.name,
    description: t.description,
    category: t.category || 'general',
    isBuiltin: t.isBuiltIn,
    tags: t.tags,
  }))

  // Wrap delete functions to work with legacy numeric IDs
  const handleDeleteMeeting = (id: number) => {
    // Find the meeting by numeric ID and delete using string ID
    const meeting = meetings.find((m, index) => parseInt(m.id) || (index + 1) === id)
    if (meeting) {
      return deleteMeeting(meeting.id)
    }
    return false
  }

  const handleDeleteTemplate = (id: number) => {
    // Find the template by numeric ID and delete using string ID
    const template = templates.find((t, index) => parseInt(t.id) || (index + 1) === id)
    if (template) {
      return deleteTemplate(template.id)
    }
    return false
  }

  const handleAddTemplate = (template: Omit<LegacyTemplate, 'id'>) => {
    return createTemplate({
      name: template.title,
      description: template.description,
      type: template.isBuiltin ? 'built-in' : 'custom',
      category: template.category,
      tags: template.tags,
      isDefault: false,
      isBuiltIn: template.isBuiltin,
    })
  }

  return (
    <div className="flex h-screen bg-[#EEF8FC]">
      <Sidebar
        currentPage={currentPage}
        onPageChange={handlePageChange}
        showDetailVariant={shouldShowDetailSidebar}
        forceHighlight={currentPage === 'summary' ? 'meetings' : undefined}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNav currentPage={currentPage} />

        <main className="flex-1 overflow-auto px-9 py-8">
          {meetingsLoading || templatesLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[#536172]">加载中...</div>
            </div>
          ) : (
            <>
              {currentPage === 'dashboard' && (
                <DashboardPage
                  meetings={legacyMeetings}
                  selectedFile={selectedFile}
                  processingStage={processingStage}
                  processingProgress={processingProgress}
                  onFileSelect={setSelectedFile}
                  onProcessingStageChange={setProcessingStage}
                  onProcessingProgressChange={setProcessingProgress}
                  onMeetingAdd={(meeting) => {
                    // Convert legacy meeting to new format
                    const newMeeting = createMeeting({
                      title: meeting.title,
                      date: meeting.date,
                      duration: meeting.duration,
                      participants: meeting.participants,
                      status: meeting.status,
                      progress: meeting.progress,
                    })
                  }}
                  onMeetingClick={(legacyMeeting) => {
                    // Convert legacy meeting back to new format
                    const meeting = meetings.find((m, index) =>
                      parseInt(m.id) || (index + 1) === legacyMeeting.id
                    )
                    if (meeting) {
                      handleMeetingClick(meeting)
                    }
                  }}
                />
              )}

              {currentPage === 'meetings' && (
                <MeetingLibraryPage
                  meetings={legacyMeetings}
                  onMeetingClick={(legacyMeeting) => {
                    const meeting = meetings.find((m, index) =>
                      parseInt(m.id) || (index + 1) === legacyMeeting.id
                    )
                    if (meeting) {
                      handleMeetingClick(meeting)
                    }
                  }}
                  onMeetingDelete={handleDeleteMeeting}
                  onMeetingStatusChange={(id, status) => {
                    const meeting = meetings.find((m, index) =>
                      parseInt(m.id) || (index + 1) === id
                    )
                    if (meeting) {
                      updateMeeting(meeting.id, { status })
                    }
                  }}
                />
              )}

              {currentPage === 'templates' && (
                <TemplatePage
                  templates={legacyTemplates}
                  onTemplateAdd={handleAddTemplate}
                  onTemplateDelete={handleDeleteTemplate}
                />
              )}

              {(currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library') && (
                <SummaryDetailPage
                  currentPage={currentPage}
                  meeting={currentMeeting}
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
