/**
 * Settings panel component
 * Modal dialog for managing user settings
 */

import { useState, useEffect } from 'react'
import { X, Trash2, RotateCcw } from 'lucide-react'
import { useTemplates } from '../store/useAppStore'
import { templateStorage } from '../lib/storage'
import {
  getUserSettings,
  updateDisplayName,
  updateDefaultTemplate,
  updateExportFormatPreference,
  updateIncludeTranscriptByDefault,
  clearAllLocalData,
  type UserSettings,
} from '../services/settingsService'
import type { ExportFormat } from '../services/exportService'

interface SettingsPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [settings, setSettings] = useState<UserSettings>(getUserSettings())
  const [displayNameInput, setDisplayNameInput] = useState(settings.displayName)
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  const { templates } = useTemplates()

  useEffect(() => {
    setSettings(getUserSettings())
    setDisplayNameInput(getUserSettings().displayName)
  }, [isOpen])

  const handleSaveDisplayName = () => {
    const trimmedName = displayNameInput.trim()

    if (!trimmedName) {
      alert('显示名称不能为空')
      return
    }

    if (trimmedName.length > 30) {
      alert('显示名称不能超过 30 个字符')
      return
    }

    const updated = updateDisplayName(trimmedName)
    setSettings(updated)
    setDisplayNameInput(trimmedName)
    alert('显示名称已更新')
  }

  const handleChangeDefaultTemplate = (templateId: string) => {
    const updated = updateDefaultTemplate(templateId)
    setSettings(updated)

    // Also update template store to ensure consistency
    templateStorage.setDefault(templateId)
    alert('默认模板已更新')
  }

  const handleChangeExportFormat = (format: ExportFormat) => {
    const updated = updateExportFormatPreference(format)
    setSettings(updated)
  }

  const handleChangeIncludeTranscript = (include: boolean) => {
    const updated = updateIncludeTranscriptByDefault(include)
    setSettings(updated)
  }

  const handleClearData = () => {
    if (!showClearConfirm) {
      setShowClearConfirm(true)
      return
    }

    if (confirm('确定要清除所有本地数据吗？\n\n这将删除：\n- 所有会议记录\n- 所有自定义模板\n- 所有行动项\n- 用户设置\n\n此操作不可撤销！')) {
      clearAllLocalData()
      setShowClearConfirm(false)
      alert('本地数据已清除，页面将刷新')
      window.location.reload()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#D6E1EA]">
          <h2 className="text-xl font-semibold text-[#06162E]">设置</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-[#536172] hover:text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)] space-y-8">
          {/* Display Name */}
          <section>
            <h3 className="text-lg font-medium text-[#06162E] mb-4">显示名称</h3>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={displayNameInput}
                onChange={(e) => setDisplayNameInput(e.target.value)}
                placeholder="输入显示名称"
                className="flex-1 px-4 py-2.5 bg-white border border-[#D6E1EA] rounded-xl text-sm text-[#06162E] placeholder:text-[#536172] focus:outline-none focus:border-[#061B35] focus:ring-2 focus:ring-[#061B35]/20 transition-all"
              />
              <button
                onClick={handleSaveDisplayName}
                disabled={displayNameInput.trim() === settings.displayName}
                className="px-6 py-2.5 bg-[#061B35] text-white rounded-lg text-sm hover:bg-[#08213F] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                保存
              </button>
            </div>
          </section>

          {/* Default Template */}
          <section>
            <h3 className="text-lg font-medium text-[#06162E] mb-4">默认模板</h3>
            <div className="grid grid-cols-2 gap-3">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => handleChangeDefaultTemplate(template.id)}
                  className={`px-4 py-3 rounded-xl text-left transition-all ${
                    settings.defaultTemplateId === template.id || (!settings.defaultTemplateId && template.isDefault)
                      ? 'bg-[#061B35] text-white'
                      : 'bg-[#EEF8FC] text-[#06162E] hover:bg-[#DCEBFF]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-sm">{template.name}</p>
                      <p className="text-xs opacity-80 mt-1">{template.description}</p>
                    </div>
                    {template.isDefault && !settings.defaultTemplateId && (
                      <span className="text-xs bg-white/20 px-2 py-0.5 rounded">默认</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Export Preferences */}
          <section>
            <h3 className="text-lg font-medium text-[#06162E] mb-4">导出偏好</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  默认导出格式
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['markdown', 'txt', 'json'] as ExportFormat[]).map((format) => (
                    <button
                      key={format}
                      onClick={() => handleChangeExportFormat(format)}
                      className={`px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                        settings.exportFormatPreference === format
                          ? 'bg-[#061B35] text-white'
                          : 'bg-[#EEF8FC] text-[#06162E] hover:bg-[#DCEBFF]'
                      }`}
                    >
                      {format === 'markdown' && 'Markdown'}
                      {format === 'txt' && 'TXT'}
                      {format === 'json' && 'JSON'}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.includeTranscriptByDefault}
                    onChange={(e) => handleChangeIncludeTranscript(e.target.checked)}
                    className="w-4 h-4 text-[#061B35] border-[#D6E1EA] rounded focus:ring-[#061B35]"
                  />
                  <span className="text-sm text-[#06162E]">默认包含完整文字稿</span>
                </label>
                <p className="text-xs text-[#536172] mt-1 ml-7">
                  导出时默认勾选"包含完整文字稿"选项
                </p>
              </div>
            </div>
          </section>

          {/* Data Management */}
          <section className="pt-6 border-t border-[#D6E1EA]">
            <h3 className="text-lg font-medium text-[#06162E] mb-2">数据管理</h3>
            <p className="text-sm text-[#536172] mb-4">
              当前使用本地浏览器存储数据。清除后数据将无法恢复。
            </p>
            <button
              onClick={handleClearData}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                showClearConfirm
                  ? 'bg-[#FF6B6B] text-white hover:bg-[#DC2626]'
                  : 'bg-[#EEF8FC] text-[#FF6B6B] hover:bg-[#FFE7E7]'
              }`}
            >
              {showClearConfirm ? <Trash2 className="w-4 h-4" /> : <RotateCcw className="w-4 h-4" />}
              {showClearConfirm ? '确认清除所有数据' : '清除本地数据'}
            </button>
            {showClearConfirm && (
              <p className="text-xs text-[#FF6B6B] mt-2">
                再次点击确认清除，此操作不可撤销
              </p>
            )}
          </section>

          {/* Info */}
          <section className="pt-6 border-t border-[#D6E1EA]">
            <div className="bg-[#EEF8FC] rounded-xl p-4">
              <h4 className="text-sm font-medium text-[#06162E] mb-2">当前版本</h4>
              <p className="text-xs text-[#536172]">
                Jinni AI 本地版本 v1.0
              </p>
              <p className="text-xs text-[#536172] mt-2">
                数据存储：本地浏览器 | 云同步：未启用
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
