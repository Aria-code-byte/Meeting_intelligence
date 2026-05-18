import { useState } from 'react'
import { ArrowLeft, Copy, RefreshCw, Download, CheckCircle2, FileText, Users, Calendar, Clock } from 'lucide-react'
import { ActionItemCard } from '../components/ActionItemCard'
import type { PageType, Meeting } from '../App'

interface SummaryDetailPageProps {
  currentPage: PageType
  meeting: Meeting | null
  onBack: () => void
}

type Priority = 'high' | 'medium' | 'low'

interface ActionItem {
  id: number
  assignee: string
  task: string
  priority: Priority
  dueDate: string
}

const mockActionItems: ActionItem[] = [
  {
    id: 1,
    assignee: 'Alice Chen',
    task: '完成 Glassmorphism 设计规范文档',
    priority: 'high',
    dueDate: '10月30日',
  },
  {
    id: 2,
    assignee: 'Bob Wang',
    task: '评估移动端 BottomNavBar 性能影响',
    priority: 'medium',
    dueDate: '11月1日',
  },
  {
    id: 3,
    assignee: 'Charlie Liu',
    task: '整理当前页面用户停留时间数据',
    priority: 'low',
    dueDate: '10月27日',
  },
]

const mockSummary = {
  title: 'Q4 产品体验升级研讨会',
  date: '2023年10月24日 14:00 - 15:30 (1.5h)',
  template: '产品研讨模板',
  category: '设计周会',
  overview: `本次会议主要探讨了 Jinni AI V2 版本的核心体验升级路径。团队就当前系统的易用性瓶颈进行了深度剖析，并一致认为下一阶段的产品重点应从"功能堆砌"转向"认知减负"。产品侧提出了引入"Glassmorphic"设计语言以增强界面呼吸感的提案，开发侧评估了相关性能开销并确认可行。`,
  keyData: '用户在设置页面的平均停留时间下降了 12%，但误操作率攀升了 4%。需要通过更清晰的层级设计来优化。',
  decisions: [
    {
      title: 'UI 风格演进方向',
      priority: '高优先级',
      status: 'pending',
      description: '确定采用 Modern Corporate + Glassmorphism 混合风格。废弃原有的大面积深色侧边栏方案，改为浅色基调加透明度模糊效果，以提升整体界面的通透感和专业度。'
    },
    {
      title: '移动端适配策略',
      priority: '已确认',
      status: 'confirmed',
      description: '在 md 断点以下，强制隐藏顶部文字导航，启用底部导航栏（BottomNavBar）。侧边栏在移动端转为抽屉式交互，确保主画布的阅读体验。'
    }
  ],
  transcript: `[00:00] 主持人：大家好，欢迎参加今天的设计周会。今天我们主要讨论 Q4 产品体验升级的相关议题。

[00:15] Alice：我先汇报一下用户调研的结果。从数据来看，用户对当前界面的满意度有所下降，主要反馈是"视觉过于沉重"、"信息层级不清晰"。

[00:45] Bob：从技术角度，我认为可以引入 Glassmorphism 设计语言。但这需要考虑性能开销，特别是模糊效果的计算成本。

[01:20] Charlie：我同意。我们可以在关键页面先试点，比如设置页面和仪表板。如果效果好，再逐步推广到全站。

[01:45] 主持人：好，那我们今天就确定这个方向。Alice，你负责制定详细的设计规范；Bob，你做性能评估；Charlie，你准备试点计划。

[02:00] 主持人：还有其他议题吗？没有的话，今天的会议就到这里。散会。`
}

type TabType = 'summary' | 'transcript' | 'action' | 'info'

export function SummaryDetailPage({ currentPage, meeting, onBack }: SummaryDetailPageProps) {
  const [activeTab, setActiveTab] = useState<TabType>('summary')
  const [copySuccess, setCopySuccess] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [actionItems] = useState<ActionItem[]>(mockActionItems)

  const sidebarItems = [
    { id: 'summary' as TabType, label: 'AI 总结', count: null },
    { id: 'transcript' as TabType, label: '完整文字稿', count: null },
    { id: 'action' as TabType, label: '待办事项', count: actionItems.length },
    { id: 'info' as TabType, label: '会议信息', count: null },
  ]

  const handleCopy = async () => {
    let content = ''

    if (activeTab === 'summary') {
      content = `${mockSummary.title}\n\n会议概要：\n${mockSummary.overview}\n\n关键数据：\n${mockSummary.keyData}\n\n关键决策：\n${mockSummary.decisions.map(d => `- ${d.title}: ${d.description}`).join('\n')}`
    } else if (activeTab === 'transcript') {
      content = mockSummary.transcript
    } else if (activeTab === 'action') {
      content = actionItems.map(item => `${item.assignee}: ${item.task} (${item.dueDate})`).join('\n')
    } else if (activeTab === 'info') {
      content = `${mockSummary.title}\n时间：${mockSummary.date}\n模板：${mockSummary.template}\n分类：${mockSummary.category}`
    }

    try {
      await navigator.clipboard.writeText(content)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
    let content = ''
    let filename = ''

    if (activeTab === 'summary') {
      content = `${mockSummary.title}\n\n会议概要：\n${mockSummary.overview}\n\n关键数据：\n${mockSummary.keyData}\n\n关键决策：\n${mockSummary.decisions.map(d => `- ${d.title}: ${d.description}`).join('\n')}`
      filename = `summary_${Date.now()}.txt`
    } else if (activeTab === 'transcript') {
      content = mockSummary.transcript
      filename = `transcript_${Date.now()}.txt`
    } else if (activeTab === 'action') {
      content = actionItems.map(item => `${item.assignee}: ${item.task} (${item.dueDate})`).join('\n')
      filename = `action_items_${Date.now()}.txt`
    } else if (activeTab === 'info') {
      content = `${mockSummary.title}\n时间：${mockSummary.date}\n模板：${mockSummary.template}\n分类：${mockSummary.category}`
      filename = `meeting_info_${Date.now()}.txt`
    }

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
    setRegenerating(true)
    setTimeout(() => {
      setRegenerating(false)
    }, 3000)
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
            {mockSummary.category}
          </span>
          <h1 className="text-3xl font-bold text-[#06162E]">
            {mockSummary.title}
          </h1>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-[#536172]">
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {mockSummary.date}
              </span>
              <span>•</span>
              <span>{mockSummary.template}</span>
              <span>•</span>
              <span className="text-[#10B981]">已结束</span>
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
          <>
            {/* Summary Card */}
            <div className="bg-white rounded-2xl p-6 border-2 border-[#D6E1EA]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[#061B35]" />
                </div>
                <h2 className="text-xl font-semibold text-[#06162E]">会议概要</h2>
              </div>

              <p className="text-[#06162E] leading-relaxed mb-6">
                {mockSummary.overview}
              </p>

              <div className="bg-[#E9F3FF] rounded-xl p-5 border border-[#DCEBFF]">
                <h3 className="text-sm font-semibold text-[#061B35] mb-2">关键数据提及</h3>
                <p className="text-sm text-[#536172]">
                  {mockSummary.keyData}
                </p>
              </div>
            </div>

            {/* Decisions Card */}
            <div className="bg-[#FFF5EB] rounded-2xl p-6 border border-[#FFE5D0]">
              <h2 className="text-xl font-semibold text-[#B86E04] mb-4">关键决策</h2>

              <div className="space-y-4">
                {mockSummary.decisions.map((decision, index) => (
                  <div key={index} className="bg-white rounded-xl p-5 border-l-4 border-[#FFA54D]">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-[#06162E]">{decision.title}</h3>
                      <span className={`px-2 py-1 text-xs rounded-full flex-shrink-0 ${
                        decision.status === 'confirmed' ? 'bg-[#10B981] text-white' : 'bg-[#FFA54D] text-white'
                      }`}>
                        {decision.priority}
                      </span>
                    </div>
                    <p className="text-sm text-[#536172] leading-relaxed">
                      {decision.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {activeTab === 'transcript' && (
          <div className="bg-white rounded-2xl p-6 border-2 border-[#D6E1EA]">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-[#061B35]" />
              </div>
              <h2 className="text-xl font-semibold text-[#06162E]">完整文字稿</h2>
            </div>

            <div className="space-y-4">
              {mockSummary.transcript.split('\n\n').map((paragraph, index) => (
                <div key={index} className="p-4 bg-[#EEF8FC] rounded-lg">
                  <p className="text-sm text-[#06162E] whitespace-pre-line">{paragraph}</p>
                </div>
              ))}
            </div>
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

            <div className="space-y-3">
              {actionItems.map((item) => (
                <ActionItemCard key={item.id} {...item} />
              ))}
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
                  <h3 className="font-medium text-[#06162E] mb-1">会议时间</h3>
                  <p className="text-sm text-[#536172]">{mockSummary.date}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <Clock className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">会议时长</h3>
                  <p className="text-sm text-[#536172]">1小时30分钟</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <FileText className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">使用模板</h3>
                  <p className="text-sm text-[#536172]">{mockSummary.template}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-[#EEF8FC] rounded-lg">
                <Users className="w-5 h-5 text-[#536172] mt-0.5" />
                <div>
                  <h3 className="font-medium text-[#06162E] mb-1">参会人员</h3>
                  <p className="text-sm text-[#536172]">主持人、Alice、Bob、Charlie</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
