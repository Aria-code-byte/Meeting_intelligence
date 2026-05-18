import { User, Calendar } from 'lucide-react'

interface ActionItemCardProps {
  id: number
  assignee: string
  task: string
  priority: 'high' | 'medium' | 'low'
  dueDate: string
}

const priorityConfig = {
  high: {
    label: '高',
    bgColor: 'bg-[#FFE7E7]',
    textColor: 'text-[#FF6B6B]',
  },
  medium: {
    label: '中',
    bgColor: 'bg-[#FFF5EB]',
    textColor: 'text-[#B86E04]',
  },
  low: {
    label: '低',
    bgColor: 'bg-[#E9F3FF]',
    textColor: 'text-[#061B35]',
  },
}

export function ActionItemCard({ assignee, task, priority, dueDate }: ActionItemCardProps) {
  const config = priorityConfig[priority]

  return (
    <div className="flex items-center gap-4 p-4 bg-[#EEF8FC] rounded-xl">
      <div className="w-10 h-10 bg-[#DCEBFF] rounded-full flex items-center justify-center flex-shrink-0">
        <User className="w-5 h-5 text-[#061B35]" />
      </div>

      <div className="flex-1">
        <p className="text-sm font-medium text-[#06162E] mb-1">{task}</p>
        <div className="flex items-center gap-3 text-xs text-[#536172]">
          <span>{assignee}</span>
          <span>•</span>
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            <span>{dueDate}</span>
          </div>
        </div>
      </div>

      <span className={`px-2 py-1 text-xs rounded-full ${config.bgColor} ${config.textColor} flex-shrink-0`}>
        {config.label}优先级
      </span>
    </div>
  )
}
