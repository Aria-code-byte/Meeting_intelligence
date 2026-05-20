import type { LucideIcon } from 'lucide-react'
import {
  Sparkles,
  Home,
  FolderOpen,
  FileText,
  Settings,
  User,
  ChevronRight,
  Mic,
  CheckSquare,
  ListTodo,
  Users
} from 'lucide-react'
import type { PageType } from '../App'

interface SidebarProps {
  currentPage: PageType
  onPageChange: (page: PageType) => void
  showDetailVariant?: boolean
  forceHighlight?: PageType
}

interface MenuItem {
  id: PageType
  label: string
  icon: LucideIcon
  badge?: string
}

interface BottomMenuItem {
  id: 'settings' | 'account'
  label: string
  icon: LucideIcon
}

const mainMenus: MenuItem[] = [
  { id: 'dashboard', label: '首页', icon: Home },
  { id: 'meetings', label: '会议库', icon: FolderOpen },
  { id: 'templates', label: '模板管理', icon: FileText },
]

const detailMenus: MenuItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'recordings', label: 'Recordings', icon: Mic },
  { id: 'summary', label: 'AI Summaries', icon: CheckSquare },
  { id: 'action', label: 'Action Items', icon: ListTodo },
  { id: 'library', label: 'Team Library', icon: Users },
]

const bottomMenus: BottomMenuItem[] = [
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'account', label: 'Account', icon: User },
]

export function Sidebar({ currentPage, onPageChange, showDetailVariant, forceHighlight }: SidebarProps) {
  const menus = showDetailVariant ? detailMenus : mainMenus
  const activePage = forceHighlight || currentPage

  return (
    <div className="w-[300px] h-screen bg-[#E4F0F8] flex flex-col border-r border-[#D6E1EA]">
      {/* Logo Section */}
      <div className="p-6 border-b border-[#D6E1EA]">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-[#061B35] rounded-xl flex items-center justify-center">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[#06162E]">Jinni AI</h1>
            <p className="text-sm text-[#536172]">Intelligent Assistant</p>
          </div>
        </div>
      </div>

      {/* Main Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menus.map((menu) => {
          const Icon = menu.icon
          const isActive = activePage === menu.id

          return (
            <button
              key={menu.id}
              onClick={() => onPageChange(menu.id)}
              className={`
                w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all
                ${isActive
                  ? 'bg-white text-[#061B35] shadow-sm'
                  : 'text-[#536172] hover:bg-white/50 hover:text-[#06162E]'
                }
              `}
            >
              {isActive && <div className="w-1 h-8 bg-[#061B35] rounded-full" />}
              <Icon className="w-5 h-5" />
              <span className="font-medium">{menu.label}</span>
              {menu.badge && (
                <span className="ml-auto bg-[#FFA54D] text-white text-xs px-2 py-0.5 rounded-full">
                  {menu.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Bottom Menu */}
      <nav className="p-4 border-t border-[#D6E1EA] space-y-2">
        {bottomMenus.map((menu) => {
          const Icon = menu.icon
          return (
            <button
              key={menu.id}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[#536172] hover:bg-white/50 hover:text-[#06162E] transition-all"
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{menu.label}</span>
              <ChevronRight className="w-4 h-4 ml-auto" />
            </button>
          )
        })}
      </nav>
    </div>
  )
}
