import { useRef, useState, useEffect } from 'react'
import { Upload, Lock, FileText, BarChart3, TrendingUp, Briefcase, X, CheckCircle, Play, Pause, RotateCcw, ChevronDown, AlertCircle } from 'lucide-react'
import { RecentMeetingCard } from '../components/RecentMeetingCard'
import type { Meeting, SummaryTemplate } from '../types/models'

interface DashboardPageProps {
  meetings: Meeting[]
  templates: SummaryTemplate[]
  selectedFile: File | null
  processingStage: 'idle' | 'selected' | 'uploading' | 'transcribing' | 'cleaning' | 'summarizing' | 'completed' | 'failed'
  processingProgress: number
  processingMeetingId: string | null
  onFileSelect: (file: File | null) => void
  onProcessingStageChange: (stage: any) => void
  onProcessingProgressChange: (progress: number) => void
  onMeetingAdd: (meeting: Meeting) => void
  onMeetingClick: (meeting: Meeting) => void
  onStartProcessing: (file: File, title: string, templateId: string) => void
  onResetProcessing: () => void
}

const steps = [
  { id: 'uploading', label: '上传文件', icon: Upload },
  { id: 'transcribing', label: '语音转文字', icon: FileText },
  { id: 'cleaning', label: '智能清洗', icon: RotateCcw },
  { id: 'summarizing', label: 'AI 总结', icon: BarChart3 },
]

export function DashboardPage({
  meetings,
  templates,
  selectedFile,
  processingStage,
  processingProgress,
  processingMeetingId,
  onFileSelect,
  onProcessingStageChange,
  onProcessingProgressChange,
  onMeetingAdd,
  onMeetingClick,
  onStartProcessing,
  onResetProcessing
}: DashboardPageProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentProgress, setCurrentProgress] = useState(0)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [showTemplateDropdown, setShowTemplateDropdown] = useState(false)
  const [meetingTitle, setMeetingTitle] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const intervalRef = useRef<number | null>(null)

  // 调试：验证代码是否被加载
  console.log('[DashboardPage] 组件已加载 - VITE_RELOAD_TEST', new Date().toISOString())

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  // Initialize with default template
  useEffect(() => {
    if (templates.length > 0 && !selectedTemplateId) {
      const defaultTemplate = templates.find(t => t.isDefault) || templates[0]
      setSelectedTemplateId(defaultTemplate.id)
    }
  }, [templates, selectedTemplateId])

  // Sync progress to parent
  useEffect(() => {
    onProcessingProgressChange(currentProgress)
  }, [currentProgress, onProcessingProgressChange])

  // Note: Removed auto-reset for completed/failed states to allow users to click buttons
  // State reset happens when:
  // 1. User clicks "上传新文件" / "继续上传" button
  // 2. User navigates to other pages (handled in App.tsx)
  // 3. User starts a new upload

  const handleFileSelect = (file: File) => {
    // Validate file size (500MB max as per Stage 9A requirements)
    const maxSize = 500 * 1024 * 1024 // 500MB
    if (file.size > maxSize) {
      setErrorMessage('文件过大，请上传 500MB 以内的文件')
      return
    }

    // Validate file type - more comprehensive format check
    const validTypes = [
      'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave', 'audio/x-wav',
      'audio/m4a', 'audio/x-m4a', 'audio/mp4', 'audio/x-m4p',
      'video/mp4', 'video/quicktime', 'video/x-m4v', 'video/webm'
    ]
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    const validExtensions = ['mp3', 'wav', 'wave', 'm4a', 'mp4', 'mov', 'webm']

    // Check both MIME type and extension for better compatibility
    const isValidType = validTypes.includes(file.type) || validExtensions.includes(fileExtension || '')

    if (!isValidType) {
      setErrorMessage('暂不支持该文件格式，请上传音频或视频文件（支持 MP3、WAV、M4A、MP4、MOV、WEBM）')
      return
    }

    // Check if file is empty
    if (file.size === 0) {
      setErrorMessage('文件为空，请选择有效的音频或视频文件')
      return
    }

    setErrorMessage('')

    // Initialize meeting title from filename (without extension)
    const defaultTitle = file.name.replace(/\.[^/.]+$/, '')
    setMeetingTitle(defaultTitle)

    onFileSelect(file)
    onProcessingStageChange('selected')
  }

  const startProcessing = () => {
    if (!selectedFile) {
      fileInputRef.current?.click()
      return
    }

    // Prevent starting if already processing
    if (isProcessing) {
      alert('正在处理中，请稍候')
      return
    }

    // Validate meeting title
    const title = meetingTitle.trim()
    if (!title) {
      setErrorMessage('请输入会议名称')
      return
    }

    if (title.length > 80) {
      setErrorMessage('会议名称不能超过 80 个字符')
      return
    }

    // Validate template selection
    if (!selectedTemplateId) {
      setErrorMessage('请先选择总结模板')
      return
    }

    setIsProcessing(true)
    onProcessingStageChange('uploading')
    setCurrentProgress(0)
    setErrorMessage('')

    // Call parent component to start real processing with user's title
    onStartProcessing(selectedFile, title, selectedTemplateId)
  }

  const cancelProcessing = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsProcessing(false)
    setCurrentProgress(0)
    onProcessingStageChange('idle')
    onFileSelect(null)
    setMeetingTitle('')
    setErrorMessage('')
    onResetProcessing()
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

            {/* Template Selection */}
            <div className="w-[690px] mb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-[#06162E]">总结模板：</span>
                <div className="relative">
                  <button
                    onClick={() => setShowTemplateDropdown(!showTemplateDropdown)}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-[#D6E1EA] rounded-xl text-[#06162E] hover:bg-[#EEF8FC] transition-colors min-w-[200px] justify-between"
                  >
                    <span className="text-sm">
                      {templates.find(t => t.id === selectedTemplateId)?.name || '选择模板'}
                    </span>
                    <ChevronDown className="w-4 h-4 text-[#536172]" />
                  </button>

                  {showTemplateDropdown && (
                    <div className="absolute top-full left-0 mt-2 w-full bg-white border border-[#D6E1EA] rounded-xl shadow-lg z-10 max-h-[300px] overflow-y-auto">
                      {templates.map((template) => (
                        <button
                          key={template.id}
                          onClick={() => {
                            setSelectedTemplateId(template.id)
                            setShowTemplateDropdown(false)
                          }}
                          className={`w-full px-4 py-3 text-left text-sm hover:bg-[#EEF8FC] transition-colors flex items-center justify-between ${
                            template.id === selectedTemplateId ? 'bg-[#EEF8FC]' : ''
                          }`}
                        >
                          <span>{template.name}</span>
                          {template.isDefault && (
                            <span className="text-xs text-[#536172] bg-[#EEF8FC] px-2 py-1 rounded">默认</span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              {selectedTemplateId && (
                <p className="text-xs text-[#536172] mt-2">
                  {templates.find(t => t.id === selectedTemplateId)?.description}
                </p>
              )}
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
              {/* Error Message */}
              {errorMessage && (
                <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm">
                  <p className="font-medium">处理失败</p>
                  <p className="mt-1">{errorMessage}</p>
                </div>
              )}

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

              {/* Meeting Title Input */}
              {processingStage === 'selected' && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-[#06162E] mb-2">
                    会议名称
                  </label>
                  <input
                    type="text"
                    value={meetingTitle}
                    onChange={(e) => setMeetingTitle(e.target.value)}
                    maxLength={80}
                    placeholder="请输入会议名称"
                    className="w-full px-4 py-3 bg-white border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:border-[#061B35] focus:ring-2 focus:ring-[#061B35]/20 transition-all"
                  />
                  <p className="text-xs text-[#536172] mt-1">
                    {meetingTitle.length}/80 个字符
                  </p>
                </div>
              )}

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
                    disabled={isProcessing}
                    className="flex-1 px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
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

        {/* Failed View - Backend unavailable */}
        {(processingStage === 'idle' || processingStage === 'failed') && errorMessage && (
          <div className="w-[690px]">
            <div className="bg-white rounded-2xl p-8 border-2 border-[#FFE7E7]">
              <div className="text-center mb-6">
                <AlertCircle className="w-16 h-16 text-[#FF6B6B] mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-[#06162E] mb-2">后端服务暂不可用</h2>
                <p className="text-[#536172] mb-6">
                  后端转写服务暂时不可用，会议记录已保存。
                  你可以稍后重试，或在会议详情页手动补充文字稿继续生成总结。
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setErrorMessage('')
                    onFileSelect(null)
                  }}
                  className="flex-1 px-6 py-3 border border-[#D6E1EA] rounded-xl text-[#06162E] font-medium hover:bg-[#EEF8FC] transition-colors"
                >
                  返回首页
                </button>
                <button
                  onClick={() => {
                    const lastMeeting = meetings[0]
                    if (lastMeeting) {
                      onMeetingClick(lastMeeting)
                    }
                  }}
                  className="flex-1 px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors"
                >
                  去会议详情页
                </button>
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
                    console.log('[DashboardPage] 查看总结按钮被点击:', {
                      processingMeetingId,
                      meetingsCount: meetings.length,
                      allMeetingIds: meetings.map(m => m.id),
                    })
                    const newMeeting = processingMeetingId ? meetings.find(m => m.id === processingMeetingId) : null
                    console.log('[DashboardPage] 找到的会议:', {
                      found: !!newMeeting,
                      meetingId: newMeeting?.id,
                      summaryProvider: newMeeting?.summaryProvider,
                      summaryIsFallback: newMeeting?.summaryIsFallback,
                    })
                    if (newMeeting) {
                      onMeetingClick(newMeeting)
                    } else {
                      // No meeting found, just reset to idle
                      console.log('[DashboardPage] 未找到会议，重置状态')
                      cancelProcessing()
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

        {/* Fallback: Should never reach here, but if we do, show upload UI */}
        {!['idle', 'selected', 'uploading', 'transcribing', 'cleaning', 'summarizing', 'completed', 'failed'].includes(processingStage) && (
          <div className="w-[690px]">
            <div className="bg-white rounded-2xl p-12 text-center">
              <p className="text-[#536172] mb-4">状态异常，请重试</p>
              <button
                onClick={() => {
                  onProcessingStageChange('idle')
                  onFileSelect(null)
                }}
                className="px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors"
              >
                返回首页
              </button>
            </div>
          </div>
        )}

        {/* DEFAULT FALLBACK - 永远显示上传入口 */}
        {(!['idle', 'selected', 'uploading', 'transcribing', 'cleaning', 'summarizing', 'completed', 'failed'].includes(processingStage)) && (
          <div className="w-[690px]">
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-8 text-center mb-6">
              <AlertCircle className="w-16 h-16 text-yellow-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-[#06162E] mb-2">状态异常</h2>
              <p className="text-[#536172] mb-6">当前处理状态异常，请重试</p>
              <button
                onClick={() => {
                  onProcessingStageChange('idle')
                  onFileSelect(null)
                }}
                className="px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors"
              >
                重置状态
              </button>
            </div>
          </div>
        )}
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
                progress={meeting.progress || 0}
                icon={meeting.status === 'completed' ? TrendingUp : Briefcase}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
