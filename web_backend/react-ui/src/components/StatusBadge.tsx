import { CheckCircle2, Clock, XCircle, FileText } from 'lucide-react'

interface StatusBadgeProps {
  status: string
}

const statusConfig = {
  'summary-completed': {
    label: '总结完成',
    bgColor: 'bg-[#E9F3FF]',
    textColor: 'text-[#061B35]',
    icon: CheckCircle2,
  },
  'processing': {
    label: '处理中...',
    bgColor: 'bg-[#FFF5EB]',
    textColor: 'text-[#B86E04]',
    icon: Clock,
  },
  'failed': {
    label: '失败',
    bgColor: 'bg-[#FFE7E7]',
    textColor: 'text-[#FF6B6B]',
    icon: XCircle,
  },
  'transcription-completed': {
    label: '转录完成',
    bgColor: 'bg-[#F0E6FF]',
    textColor: 'text-[#6B46FF]',
    icon: FileText,
  },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status as keyof typeof statusConfig]
  if (!config) return null

  const Icon = config.icon

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
      <Icon className="w-3.5 h-3.5" />
      {config.label}
    </span>
  )
}
