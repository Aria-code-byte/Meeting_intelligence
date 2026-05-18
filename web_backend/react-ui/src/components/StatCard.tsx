import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  icon: LucideIcon
  label: string
  value: string
  color: string
}

export function StatCard({ icon: Icon, label, value, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 border border-[#D6E1EA] flex items-center gap-3">
      <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center flex-shrink-0`}>
        <Icon className="w-6 h-6 text-[#061B35]" />
      </div>
      <div>
        <div className="text-2xl font-bold text-[#06162E]">{value}</div>
        <div className="text-xs text-[#536172]">{label}</div>
      </div>
    </div>
  )
}
