import { ChevronRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface RecentMeetingCardProps {
  id: number
  title: string
  date: string
  duration: string
  status: 'completed' | 'processing'
  progress: number
  icon: LucideIcon
}

const statusConfig = {
  completed: {
    label: '已完成',
    bgColor: 'bg-[#E9F3FF]',
    textColor: 'text-[#061B35]',
    progressColor: 'bg-[#061B35]',
  },
  processing: {
    label: '处理中',
    bgColor: 'bg-[#FFF5EB]',
    textColor: 'text-[#B86E04]',
    progressColor: 'bg-[#FFA54D]',
  },
}

export function RecentMeetingCard({
  title,
  date,
  duration,
  status,
  progress,
  icon: Icon
}: RecentMeetingCardProps) {
  const config = statusConfig[status]

  return (
    <div className="bg-white rounded-xl p-4 border border-[#D6E1EA] hover:shadow-md transition-shadow cursor-pointer relative">
      {/* Status Badge - Top Right */}
      <div className="absolute top-4 right-4">
        <span className={`text-xs px-2.5 py-1 rounded-full ${config.bgColor} ${config.textColor}`}>
          {status === 'processing' ? `处理中 (${progress}%)` : config.label}
        </span>
      </div>

      <div className="flex items-start gap-3 mb-3 pr-20">
        <div className="w-9 h-9 bg-[#DCEBFF] rounded-lg flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-[#061B35]" />
        </div>
        <div>
          <h3 className="font-semibold text-[#06162E] text-sm">{title}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-[#536172]">{date}</span>
            <span className="text-xs text-[#536172]">•</span>
            <span className="text-xs text-[#536172]">{duration}</span>
          </div>
        </div>
      </div>

      {/* Progress Bar - Bottom */}
      {status === 'processing' && (
        <div className="w-full h-1.5 bg-[#E4F0F8] rounded-full overflow-hidden">
          <div
            className={`h-full ${config.progressColor} rounded-full transition-all`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  )
}
