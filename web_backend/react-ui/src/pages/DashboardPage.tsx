import { useRef, useState, useEffect } from 'react'
import { Upload, Lock, FileText, BarChart3, TrendingUp, Briefcase, X, CheckCircle, Play, Pause, RotateCcw } from 'lucide-react'
import { StatCard } from '../components/StatCard'
import { RecentMeetingCard } from '../components/RecentMeetingCard'
import type { Meeting, Stats } from '../App'

interface DashboardPageProps {
  meetings: Meeting[]
  stats: Stats
  selectedFile: File | null
  processingStage: 'idle' | 'selected' | 'uploading' | 'transcribing' | 'cleaning' | 'summarizing' | 'completed' | 'failed'
  processingProgress: number
  onFileSelect: (file: File | null) => void
  onProcessingStageChange: (stage: any) => void
  onProcessingProgressChange: (progress: number) => void
  onMeetingAdd: (meeting: Meeting) => void
  onMeetingClick: (meeting: Meeting) => void
}

const steps = [
  { id: 'uploading', label: '上传文件', icon: Upload },
  { id: 'transcribing', label: '语音转文字', icon: FileText },
  { id: 'cleaning', label: '智能清洗', icon: RotateCcw },
  { id: 'summarizing', label: 'AI 总结', icon: BarChart3 },
]

export function DashboardPage({
  meetings,
  stats,
  selectedFile,
  processingStage,
  processingProgress,
  onFileSelect,
  onProcessingStageChange,
  onProcessingProgressChange,
  onMeetingAdd,
  onMeetingClick
}: DashboardPageProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const handleFileSelect = (file: File) => {
    // Validate file size (2GB max)
    if (file.size > 2 * 1024 * 1024 * 1024) {
      setErrorMessage('文件大小超过 2GB 限制')
      return
    }

    // Validate file type
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'video/mp4', 'video/quicktime']
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    const validExtensions = ['mp3', 'wav', 'mp4', 'mov']

    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension || '')) {
      setErrorMessage('不支持的文件格式。请上传 MP3, WAV, MP4 或 MOV 文件。')
      return
    }

    setErrorMessage('')
    onFileSelect(file)
    onProcessingStageChange('selected')
  }

  const startProcessing = () => {
    if (!selectedFile) {
      fileInputRef.current?.click()
      return
    }

    onProcessingStageChange('uploading')
    onProcessingProgressChange(0)

    // Simulate processing progress
    intervalRef.current = setInterval(() => {
      onProcessingProgressChange(prev => {
        const newProgress = prev + 1

        // Stage transitions based on progress
        if (newProgress <= 20) {
          onProcessingStageChange('uploading')
        } else if (newProgress <= 65) {
          onProcessingStageChange('transcribing')
        } else if (newProgress <= 85) {
          onProcessingStageChange('cleaning')
        } else if (newProgress <= 100) {
          onProcessingStageChange('summarizing')
        }

        // Complete processing
        if (newProgress >= 100) {
          clearInterval(intervalRef.current!)

          setTimeout(() => {
            onProcessingStageChange('completed')

            // Create new meeting
            const newMeeting: Meeting = {
              id: Date.now(),
              title: selectedFile.name.replace(/\.[^/.]+$/, ''),
              date: new Date().toISOString().split('T')[0],
              duration: '0m', // Would be calculated from actual audio
              status: 'completed',
              progress: 100,
              participants: ['User']
            }
            onMeetingAdd(newMeeting)

            // Reset after delay
            setTimeout(() => {
              onProcessingStageChange('idle')
              onProcessingProgressChange(0)
              onFileSelect(null)
            }, 3000)
          }, 500)

          return 100
        }

        return newProgress
      })
    }, 100) // Update every 100ms for smooth animation
  }

  const cancelProcessing = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    onProcessingStageChange('idle')
    onProcessingProgressChange(0)
    onFileSelect(null)
    setErrorMessage('')
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  // Get current step index
  const getCurrentStepIndex = () => {
    const stageMap: Record<typeof processingStage, number> = {
      idle: -1,
      selected: -1,
      uploading: 0,
      transcribing: 1,
      cleaning: 2,
      summarizing: 3,
      completed: 4,
      failed: -1
    }
    return stageMap[processingStage]
  }

  const currentStepIndex = getCurrentStepIndex()

  return (
    <div className="flex gap-6">
      {/* Left Content */}
      <div className="flex-1 flex flex-col items-center">
        {processingStage === 'idle' && (
          <>
            {/* Hero Section */}
            <div className="text-center mb-8">
              <h1 className="text-[40px] font-bold text-[#06162E] mb-3">
                今天要整理哪场会议？
              </h1>
              <p className="text-lg text-[#536172]">
                上传音频或视频，Jinni AI 将自动生成文字稿、会议总结和行动项。
              </p>
            </div>

            {/* Upload Card */}
            <div
              className={`relative w-[690px] h-[500px] bg-white rounded-2xl border-2 transition-all p-12 text-center flex flex-col items-center justify-center cursor-pointer ${
                isDragging
                  ? 'border-[#061B35] bg-[#EEF8FC]'
                  : 'border-dashed border-[#061B35] hover:border-[#08213F]'
              }`}
              style={{
                backgroundImage: processingStage === 'idle'
                  ? 'radial-gradient(circle, #D6E1EA 1px, transparent 1px)'
                  : undefined,
                backgroundSize: '20px 20px'
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".mp3,.wav,.mp4,.mov,audio/*,video/*"
                onChange={handleFileInputChange}
              />

              {/* Upload Icon */}
              <div className="w-20 h-20 bg-[#DCEBFF] rounded-full flex items-center justify-center mb-6">
                <Upload className="w-10 h-10 text-[#061B35]" />
              </div>

              <h3 className="text-2xl font-semibold text-[#06162E] mb-3">
                Drag & drop files here
              </h3>

              <p className="text-[#536172] mb-8">
                Supports MP3, WAV, MP4, MOV up to 2GB. Or click to browse from your device.
              </p>

              {errorMessage && (
                <div className="mb-4 px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm">
                  {errorMessage}
                </div>
              )}

              {/* Security Note - Bottom Right */}
              <div className="absolute bottom-6 right-6 flex items-center gap-2 text-sm text-[#536172]">
                <Lock className="w-4 h-4" />
                <span>End-to-end encrypted</span>
              </div>
            </div>
          </>
        )}

        {/* Processing View */}
        {(processingStage === 'selected' || processingStage === 'uploading' || processingStage === 'transcribing' || processingStage === 'cleaning' || processingStage === 'summarizing') && (
          <div className="w-[690px]">
            <div className="bg-white rounded-2xl p-8 mb-6">
              {/* File Info */}
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-[#DCEBFF] rounded-xl flex items-center justify-center">
                    <FileText className="w-6 h-6 text-[#061B35]" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-[#06162E]">{selectedFile?.name}</h3>
                    <p className="text-sm text-[#536172]">
                      {((selectedFile?.size || 0) / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                {processingStage === 'selected' && (
                  <button
                    onClick={cancelProcessing}
                    className="w-8 h-8 rounded-lg hover:bg-[#D6E1EA] flex items-center justify-center transition-colors"
                  >
                    <X className="w-5 h-5 text-[#536172]" />
                  </button>
                )}
              </div>

              {/* Progress Bar */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-[#06162E]">
                    {processingStage === 'selected' && '准备开始处理'}
                    {processingStage === 'uploading' && '正在上传文件...'}
                    {processingStage === 'transcribing' && '正在转录音频...'}
                    {processingStage === 'cleaning' && '正在优化文字稿...'}
                    {processingStage === 'summarizing' && '正在生成 AI 总结...'}
                  </span>
                  <span className="text-sm font-medium text-[#061B35]">{processingProgress}%</span>
                </div>
                <div className="h-2 bg-[#EEF8FC] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#061B35] rounded-full transition-all duration-100"
                    style={{ width: `${processingProgress}%` }}
                  />
                </div>
              </div>

              {/* Steps */}
              <div className="space-y-4 mb-8">
                {steps.map((step, index) => {
                  const Icon = step.icon
                  const isActive = index === currentStepIndex
                  const isCompleted = index < currentStepIndex
                  const isPending = index > currentStepIndex

                  return (
                    <div
                      key={step.id}
                      className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
                        isActive ? 'bg-[#EEF8FC]' : ''
                      } ${isCompleted ? 'opacity-60' : ''} ${isPending ? 'opacity-40' : ''}`}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isCompleted ? 'bg-green-100' : isActive ? 'bg-[#061B35]' : 'bg-gray-200'
                      }`}>
                        {isCompleted ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                        )}
                      </div>
                      <span className={`font-medium ${isActive ? 'text-[#06162E]' : 'text-[#536172]'}`}>
                        {step.label}
                      </span>
                      {isActive && (
                        <div className="ml-auto flex items-center gap-2">
                          <div className="flex gap-1">
                            <span className="w-1 h-4 bg-[#061B35] rounded animate-pulse" style={{ animationDelay: '0ms' }} />
                            <span className="w-1 h-4 bg-[#061B35] rounded animate-pulse" style={{ animationDelay: '150ms' }} />
                            <span className="w-1 h-4 bg-[#061B35] rounded animate-pulse" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      )}
                      {isCompleted && (
                        <div className="ml-auto">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Action Buttons */}
              {processingStage === 'selected' && (
                <div className="flex gap-3">
                  <button
                    onClick={cancelProcessing}
                    className="flex-1 px-6 py-3 border border-[#D6E1EA] rounded-xl text-[#06162E] font-medium hover:bg-[#EEF8FC] transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={startProcessing}
                    className="flex-1 px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors flex items-center justify-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    开始处理
                  </button>
                </div>
              )}

              {(processingStage === 'uploading' || processingStage === 'transcribing' || processingStage === 'cleaning' || processingStage === 'summarizing') && (
                <button
                  onClick={cancelProcessing}
                  className="w-full px-6 py-3 border border-[#D6E1EA] rounded-xl text-[#06162E] font-medium hover:bg-[#EEF8FC] transition-colors flex items-center justify-center gap-2"
                >
                  <Pause className="w-5 h-5" />
                  取消处理
                </button>
              )}
            </div>

            {/* Live Preview */}
            <div className="bg-white rounded-2xl p-6">
              <h3 className="font-semibold text-[#06162E] mb-4">实时转录预览</h3>
              <div className="space-y-3">
                {processingStage === 'transcribing' || processingStage === 'cleaning' || processingStage === 'summarizing' ? (
                  <>
                    <div className="p-3 bg-[#EEF8FC] rounded-lg">
                      <p className="text-sm text-[#06162E]">
                        [00:00] 大家好，欢迎参加今天的会议。我们今天主要讨论一下项目进度问题。
                      </p>
                    </div>
                    <div className="p-3 bg-[#EEF8FC] rounded-lg">
                      <p className="text-sm text-[#06162E]">
                        [00:15] 首先，让我汇报一下各个模块的完成情况。前端部分已经完成了80%...
                      </p>
                    </div>
                    <div className="p-3 bg-[#EEF8FC] rounded-lg animate-pulse">
                      <p className="text-sm text-[#536172] italic">
                        正在转录中...
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="p-3 bg-[#EEF8FC] rounded-lg">
                    <p className="text-sm text-[#536172] italic">
                      等待转录开始...
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Completed View */}
        {processingStage === 'completed' && (
          <div className="w-[690px]">
            <div className="bg-white rounded-2xl p-8 mb-6">
              <div className="text-center mb-8">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-10 h-10 text-green-600" />
                </div>
                <h2 className="text-2xl font-bold text-[#06162E] mb-2">处理完成！</h2>
                <p className="text-[#536172]">您的会议已成功处理，可以查看总结和文字稿了。</p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={cancelProcessing}
                  className="flex-1 px-6 py-3 border border-[#D6E1EA] rounded-xl text-[#06162E] font-medium hover:bg-[#EEF8FC] transition-colors"
                >
                  上传新文件
                </button>
                <button
                  onClick={() => {
                    const newMeeting = meetings[0]
                    if (newMeeting) {
                      onMeetingClick(newMeeting)
                    }
                  }}
                  className="flex-1 px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors"
                >
                  查看总结
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="w-[690px] grid grid-cols-3 gap-4 mt-6">
          <StatCard
            id={1}
            icon={TrendingUp}
            label="节省时间"
            value={stats.timeSaved}
            color="bg-[#DCEBFF]"
          />
          <StatCard
            id={2}
            icon={CheckCircle}
            label="提取行动项"
            value={stats.actionItems.toString()}
            color="bg-[#CFE5FF]"
          />
          <StatCard
            id={3}
            icon={FileText}
            label="生成文字稿"
            value={stats.transcripts.toString()}
            color="bg-[#E9F3FF]"
          />
        </div>
      </div>

      {/* Right Sidebar - Recent Meetings */}
      <div className="w-[330px] flex-shrink-0">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[#06162E]">最近会议</h2>
          <button className="text-sm text-[#536172] hover:text-[#061B35]">
            查看全部
          </button>
        </div>

        <div className="space-y-4">
          {meetings.slice(0, 5).map((meeting) => (
            <div
              key={meeting.id}
              onClick={() => onMeetingClick(meeting)}
              className="cursor-pointer"
            >
              <RecentMeetingCard
                id={meeting.id}
                title={meeting.title}
                date={meeting.date}
                duration={meeting.duration}
                status={meeting.status}
                progress={meeting.progress}
                icon={meeting.status === 'completed' ? TrendingUp : Briefcase}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
