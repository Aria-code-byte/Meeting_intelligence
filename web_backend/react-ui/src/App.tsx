import { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { TopNav } from './components/TopNav'
import { DashboardPage } from './pages/DashboardPage'
import { MeetingLibraryPage } from './pages/MeetingLibraryPage'
import { TemplatePage } from './pages/TemplatePage'
import { SummaryDetailPage } from './pages/SummaryDetailPage'

export type PageType = 'dashboard' | 'meetings' | 'templates' | 'summary' | 'recordings' | 'action' | 'library'

export type MeetingStatus = 'completed' | 'processing' | 'failed' | 'transcription-completed'

export interface Meeting {
  id: number
  title: string
  date: string
  duration: string
  status: MeetingStatus
  progress: number
  participants: string[]
}

export interface Template {
  id: number
  title: string
  description: string
  category: string
  isBuiltin: boolean
  tags: string[]
}

export interface Stats {
  timeSaved: string
  actionItems: number
  transcripts: number
}

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard')
  const [currentMeeting, setCurrentMeeting] = useState<Meeting | null>(null)

  // Shared state
  const [meetings, setMeetings] = useState<Meeting[]>([
    {
      id: 1,
      title: 'Q3 Product Strategy Sync',
      date: '2024-10-24',
      duration: '45m',
      status: 'completed',
      progress: 100,
      participants: ['Alice', 'Bob', 'Charlie']
    },
    {
      id: 2,
      title: 'Interview: Senior Designer',
      date: '2024-10-25',
      duration: '1h 12m',
      status: 'processing',
      progress: 68,
      participants: ['David', 'Eve']
    },
    {
      id: 3,
      title: 'Marketing Campaign Kickoff',
      date: '2024-10-22',
      duration: '30m',
      status: 'completed',
      progress: 100,
      participants: ['Frank', 'Grace', 'Heidi']
    }
  ])

  const [templates, setTemplates] = useState<Template[]>([
    {
      id: 1,
      title: '通用会议模板',
      description: '适用于大多数商务会议，包含会议概要、关键决策和行动项',
      category: 'general',
      isBuiltin: true,
      tags: ['通用', '商务']
    },
    {
      id: 2,
      title: '技术评审模板',
      description: '专注于技术讨论和决策，包含技术细节和实施计划',
      category: 'technical',
      isBuiltin: true,
      tags: ['技术', '开发']
    },
    {
      id: 3,
      title: '面试记录模板',
      description: '用于面试记录和评估，包含候选人信息和评分',
      category: 'interview',
      isBuiltin: true,
      tags: ['HR', '面试']
    }
  ])

  const [stats, setStats] = useState<Stats>({
    timeSaved: '12.5h',
    actionItems: 84,
    transcripts: 23
  })

  // Processing state for dashboard
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processingStage, setProcessingStage] = useState<'idle' | 'selected' | 'uploading' | 'transcribing' | 'cleaning' | 'summarizing' | 'completed' | 'failed'>('idle')
  const [processingProgress, setProcessingProgress] = useState(0)

  // CRUD operations
  const deleteMeeting = (id: number) => {
    setMeetings(prev => prev.filter(m => m.id !== id))
  }

  const deleteTemplate = (id: number) => {
    setTemplates(prev => prev.filter(t => t.id !== id))
  }

  const addTemplate = (template: Omit<Template, 'id'>) => {
    const newId = Math.max(...templates.map(t => t.id), 0) + 1
    setTemplates(prev => [...prev, { ...template, id: newId }])
  }

  const updateStats = (increment: { actionItems?: number; transcripts?: number }) => {
    setStats(prev => ({
      ...prev,
      actionItems: prev.actionItems + (increment.actionItems || 0),
      transcripts: prev.transcripts + (increment.transcripts || 0)
    }))
  }

  const handlePageChange = (page: PageType) => {
    setCurrentPage(page)
  }

  const handleMeetingClick = (meeting: Meeting) => {
    setCurrentMeeting(meeting)
    setCurrentPage('summary')
  }

  const shouldShowDetailSidebar = currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library'

  return (
    <div className="flex h-screen bg-[#EEF8FC]">
      <Sidebar
        currentPage={currentPage}
        onPageChange={handlePageChange}
        showDetailVariant={shouldShowDetailSidebar}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNav currentPage={currentPage} />

        <main className="flex-1 overflow-auto px-9 py-8">
          {currentPage === 'dashboard' && (
            <DashboardPage
              meetings={meetings}
              stats={stats}
              selectedFile={selectedFile}
              processingStage={processingStage}
              processingProgress={processingProgress}
              onFileSelect={setSelectedFile}
              onProcessingStageChange={setProcessingStage}
              onProcessingProgressChange={setProcessingProgress}
              onMeetingAdd={(meeting) => {
                setMeetings(prev => [meeting, ...prev])
                updateStats({ actionItems: 5, transcripts: 1 })
              }}
              onMeetingClick={handleMeetingClick}
            />
          )}

          {currentPage === 'meetings' && (
            <MeetingLibraryPage
              meetings={meetings}
              onMeetingClick={handleMeetingClick}
              onMeetingDelete={deleteMeeting}
              onMeetingStatusChange={(id, status) => {
                setMeetings(prev => prev.map(m =>
                  m.id === id ? { ...m, status } : m
                ))
              }}
            />
          )}

          {currentPage === 'templates' && (
            <TemplatePage
              templates={templates}
              onTemplateAdd={addTemplate}
              onTemplateDelete={deleteTemplate}
            />
          )}

          {(currentPage === 'summary' || currentPage === 'recordings' || currentPage === 'action' || currentPage === 'library') && (
            <SummaryDetailPage
              currentPage={currentPage}
              meeting={currentMeeting}
              onBack={() => setCurrentPage('dashboard')}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
