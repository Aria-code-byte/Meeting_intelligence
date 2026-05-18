import { Mic, CheckCircle2, Clock, Circle, Sparkles } from 'lucide-react'

interface ProcessingPageProps {
  onClose: () => void
}

const steps = [
  { id: 1, label: '上传完成', status: 'completed' },
  { id: 2, label: '语音识别中', status: 'current' },
  { id: 3, label: '文本清洗', status: 'pending' },
  { id: 4, label: '生成纪要', status: 'pending' },
]

const transcriptPreview = [
  { speaker: 'Speaker A', text: 'We need to finalize the Q3 marketing budget by next Tuesday.' },
  { speaker: 'Speaker B', text: "Agreed. I've already drafted the initial projections." },
  { speaker: 'Speaker A', text: "That looks great. Let's r..." },
]

export function ProcessingPage({ onClose }: ProcessingPageProps) {
  return (
    <div className="min-h-screen bg-[#EEF8FC] flex flex-col items-center justify-center p-8">
      {/* Logo Outside Card */}
      <div className="flex flex-col items-center mb-8">
        <div className="w-16 h-16 bg-[#061B35] rounded-2xl flex items-center justify-center mb-4">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-[#06162E]">Jinni AI</h1>
      </div>

      {/* White Card */}
      <div className="w-full max-w-[760px] bg-white rounded-3xl p-12 shadow-lg">
        <div className="flex flex-col items-center text-center">
          {/* Wave Icon */}
          <div className="w-20 h-20 bg-[#DCEBFF] rounded-full flex items-center justify-center mb-8">
            <Mic className="w-10 h-10 text-[#061B35]" />
          </div>

          <h2 className="text-3xl font-bold text-[#06162E] mb-3">
            正在进行 AI 深度转录
          </h2>
          <p className="text-lg text-[#536172] mb-8">
            Whisper 正在识别发言内容，并整理会议语义
          </p>

          {/* Progress Bar */}
          <div className="w-full mb-12">
            <div className="flex items-center justify-between text-sm text-[#536172] mb-3">
              <span>00:00</span>
              <span className="text-lg font-semibold text-[#061B35]">68%</span>
              <span>45:20</span>
            </div>
            <div className="w-full h-2 bg-[#E4F0F8] rounded-full overflow-hidden relative">
              <div
                className="h-full bg-[#061B35] rounded-full"
                style={{ width: '68%' }}
              />
              <div
                className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-[#FFA54D] rounded-full border-2 border-white shadow-md"
                style={{ left: '68%' }}
              />
            </div>
          </div>

          <div className="w-full flex items-start justify-between gap-12">
            {/* Steps */}
            <div className="flex-1 space-y-6">
              {steps.map((step) => {
                const isCompleted = step.status === 'completed'
                const isCurrent = step.status === 'current'

                return (
                  <div key={step.id} className="flex items-center gap-3">
                    <div className={`
                      w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0
                      ${isCompleted
                        ? 'bg-[#DCEBFF] text-[#061B35]'
                        : isCurrent
                          ? 'bg-[#FFA54D] text-white'
                          : 'border-2 border-[#DCEBFF] text-transparent'
                      }
                    `}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : isCurrent ? (
                        <Clock className="w-4 h-4" />
                      ) : (
                        <Circle className="w-4 h-4" />
                      )}
                    </div>
                    <span className={`text-sm ${isCurrent ? 'font-semibold text-[#06162E]' : 'text-[#536172]'}`}>
                      {step.label}
                    </span>
                  </div>
                )
              })}
            </div>

            {/* Transcript Preview */}
            <div className="flex-1 bg-[#EEF8FC] rounded-xl p-5 text-left">
              <h3 className="text-xs font-semibold text-[#536172] mb-4 uppercase">
                实时转录预览
              </h3>
              <div className="space-y-3">
                {transcriptPreview.map((item, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className={`
                      px-2 py-0.5 text-xs rounded-full flex-shrink-0
                      ${item.speaker === 'Speaker A'
                        ? 'bg-[#061B35] text-white'
                        : 'bg-[#DCEBFF] text-[#061B35]'
                      }
                    `}>
                      {item.speaker}
                    </span>
                    <span className="text-sm text-[#06162E]">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons - Outside Card */}
      <div className="flex items-center gap-4 mt-8">
        <button
          onClick={onClose}
          className="px-8 py-3 text-[#536172] hover:text-[#061B35] transition-colors"
        >
          取消
        </button>
        <button
          onClick={onClose}
          className="px-8 py-3 bg-[#061B35] text-white rounded-xl hover:bg-[#08213F] transition-colors"
        >
          返回
        </button>
      </div>
    </div>
  )
}
