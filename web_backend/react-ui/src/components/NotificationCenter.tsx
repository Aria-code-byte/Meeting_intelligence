/**
 * Notification center component
 * Panel displaying local notifications based on store data
 */

import { Bell, CheckCircle2, AlertCircle, Clock } from 'lucide-react'
import type { Meeting, ActionItem } from '../types/models'

interface NotificationCenterProps {
  isOpen: boolean
  onClose: () => void
  meetings: Meeting[]
  actionItems: ActionItem[]
}

export function NotificationCenter({ isOpen, onClose, meetings, actionItems }: NotificationCenterProps) {
  if (!isOpen) return null

  // Generate notifications from local data
  const failedMeetings = meetings.filter(m => m.status === 'failed')
  const processingMeetings = meetings.filter(m => m.status === 'uploaded' || m.status === 'transcribing' || m.status === 'summarizing')
  const incompleteActions = actionItems.filter(a => a.status !== 'done')

  const hasNotifications = failedMeetings.length > 0 || processingMeetings.length > 0 || incompleteActions.length > 0

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed top-16 right-20 z-50 w-80 bg-white rounded-xl border border-[#D6E1EA] shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#D6E1EA]">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-[#06162E]" />
            <h3 className="text-sm font-medium text-[#06162E]">通知中心</h3>
          </div>
          <button
            onClick={onClose}
            className="text-xs text-[#536172] hover:text-[#06162E] transition-colors"
          >
            关闭
          </button>
        </div>

        {/* Content */}
        <div className="max-h-96 overflow-y-auto">
          {!hasNotifications ? (
            <div className="p-8 text-center">
              <Bell className="w-12 h-12 text-[#536172] mx-auto mb-3" />
              <p className="text-sm text-[#536172]">暂无通知</p>
            </div>
          ) : (
            <div className="p-2 space-y-2">
              {/* Failed Meetings */}
              {failedMeetings.length > 0 && (
                <div className="p-3 bg-[#FFE7E7] rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-[#FF6B6B] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-[#06162E]">
                        {failedMeetings.length} 个会议处理失败
                      </p>
                      <p className="text-xs text-[#FF6B6B] mt-1">
                        {failedMeetings.map(m => m.title).join('、')}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Processing Meetings */}
              {processingMeetings.length > 0 && (
                <div className="p-3 bg-[#DCEBFF] rounded-lg">
                  <div className="flex items-start gap-2">
                    <Clock className="w-4 h-4 text-[#061B35] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-[#06162E]">
                        {processingMeetings.length} 个会议正在处理中
                      </p>
                      <p className="text-xs text-[#536172] mt-1">
                        请稍候片刻
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Incomplete Actions */}
              {incompleteActions.length > 0 && (
                <div className="p-3 bg-[#FEF3C7] rounded-lg">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[#F59E0B] mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-[#06162E]">
                        {incompleteActions.length} 个待办事项未完成
                      </p>
                      <p className="text-xs text-[#536172] mt-1">
                        {incompleteActions.slice(0, 3).map(a => a.content).join('、')}
                        {incompleteActions.length > 3 && '...'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-[#EEF8FC] border-t border-[#D6E1EA]">
          <p className="text-xs text-[#536172] text-center">
            当前仅显示本地通知，系统通知功能即将支持
          </p>
        </div>
      </div>
    </>
  )
}
