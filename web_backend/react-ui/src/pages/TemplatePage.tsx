import { useState, useEffect } from 'react'
import { Plus, X, Check, Eye } from 'lucide-react'
import { TemplateCard } from '../components/TemplateCard'
import type { SummaryTemplate } from '../types/models'

interface TemplatePageProps {
  templates: SummaryTemplate[]
  searchQuery: string
  onTemplateAdd: (template: Omit<SummaryTemplate, 'id' | 'createdAt' | 'updatedAt'>) => void
  onTemplateUpdate: (id: string, patch: Partial<Omit<SummaryTemplate, 'id' | 'createdAt'>>) => void
  onTemplateDelete: (id: string) => void
  onSetDefault: (id: string) => void
}

interface TemplateForm {
  title: string
  description: string
  category: string
  tags: string[]
  structure: string[]
  prompt: string
}

const categories = [
  { id: 'all', label: '全部模板' },
  { id: 'builtin', label: '内置模板' },
  { id: 'custom', label: '自定义模板' },
]

const defaultForm: TemplateForm = {
  title: '',
  description: '',
  category: 'general',
  tags: [],
  structure: ['会议概要', '关键决策', '行动项'],
  prompt: '',
}

export function TemplatePage({
  templates,
  searchQuery,
  onTemplateAdd,
  onTemplateUpdate,
  onTemplateDelete,
  onSetDefault,
}: TemplatePageProps) {
  const [activeCategory, setActiveCategory] = useState('all')
  const [showNewTemplateModal, setShowNewTemplateModal] = useState(false)
  const [showEditTemplateModal, setShowEditTemplateModal] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<SummaryTemplate | null>(null)
  const [previewTemplate, setPreviewTemplate] = useState<SummaryTemplate | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const [newTemplate, setNewTemplate] = useState<TemplateForm>(defaultForm)
  const [currentTag, setCurrentTag] = useState('')

  // 阶段 5 回归修复：监听新建模板事件
  useEffect(() => {
    const handleOpenCreate = () => {
      console.log('[TemplatePage] 收到 open-template-create 事件')
      resetForm()
      setShowNewTemplateModal(true)
    }

    window.addEventListener('open-template-create', handleOpenCreate)
    return () => window.removeEventListener('open-template-create', handleOpenCreate)
  }, [])

  // 重置表单
  const resetForm = () => {
    setNewTemplate(defaultForm)
    setCurrentTag('')
  }

  // 添加标签
  const handleAddTag = () => {
    if (currentTag.trim() && !newTemplate.tags.includes(currentTag.trim())) {
      setNewTemplate(prev => ({
        ...prev,
        tags: [...prev.tags, currentTag.trim()],
      }))
      setCurrentTag('')
    }
  }

  // 移除标签
  const handleRemoveTag = (tagToRemove: string) => {
    setNewTemplate(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove),
    }))
  }

  // 添加结构章节
  const handleAddStructure = () => {
    const section = prompt('请输入章节名称：')
    if (section && section.trim()) {
      setNewTemplate(prev => ({
        ...prev,
        structure: [...prev.structure, section.trim()],
      }))
    }
  }

  // 移除结构章节
  const handleRemoveStructure = (index: number) => {
    if (newTemplate.structure.length <= 1) {
      alert('总结结构至少需要一个章节')
      return
    }
    setNewTemplate(prev => ({
      ...prev,
      structure: prev.structure.filter((_, i) => i !== index),
    }))
  }

  // 保存新模板
  const handleSaveTemplate = () => {
    const trimmedTitle = newTemplate.title.trim()
    const trimmedDescription = newTemplate.description.trim()

    if (!trimmedTitle) {
      alert('请输入模板名称')
      return
    }

    if (trimmedTitle.length > 50) {
      alert('模板名称不能超过 50 个字符')
      return
    }

    if (trimmedDescription.length > 200) {
      alert('模板描述不能超过 200 个字符')
      return
    }

    if (newTemplate.structure.length === 0) {
      alert('总结结构至少需要一个章节')
      return
    }

    onTemplateAdd({
      name: trimmedTitle,
      description: trimmedDescription,
      type: 'custom',
      category: newTemplate.category,
      tags: newTemplate.tags,
      structure: newTemplate.structure,
      prompt: newTemplate.prompt || undefined,
      isDefault: false,
      isBuiltIn: false,
    })

    resetForm()
    setShowNewTemplateModal(false)
  }

  // 打开编辑模板
  const handleEditTemplate = (template: SummaryTemplate) => {
    setEditingTemplate(template)
    setNewTemplate({
      title: template.name,
      description: template.description,
      category: template.category || 'general',
      tags: template.tags,
      structure: template.structure || ['会议概要', '关键决策', '行动项'],
      prompt: template.prompt || '',
    })
    setShowEditTemplateModal(true)
  }

  // 保存编辑
  const handleSaveEdit = () => {
    if (!editingTemplate) return

    const trimmedTitle = newTemplate.title.trim()
    const trimmedDescription = newTemplate.description.trim()

    if (!trimmedTitle) {
      alert('请输入模板名称')
      return
    }

    if (trimmedTitle.length > 50) {
      alert('模板名称不能超过 50 个字符')
      return
    }

    if (trimmedDescription.length > 200) {
      alert('模板描述不能超过 200 个字符')
      return
    }

    if (newTemplate.structure.length === 0) {
      alert('总结结构至少需要一个章节')
      return
    }

    onTemplateUpdate(editingTemplate.id, {
      name: trimmedTitle,
      description: trimmedDescription,
      category: newTemplate.category,
      tags: newTemplate.tags,
      structure: newTemplate.structure,
      prompt: newTemplate.prompt || undefined,
    })

    resetForm()
    setEditingTemplate(null)
    setShowEditTemplateModal(false)
  }

  // 删除模板
  const handleDeleteTemplate = (id: string) => {
    const template = templates.find(t => t.id === id)
    const templateName = template?.name || '该模板'

    if (confirm(`确定要删除模板"${templateName}"吗？\n\n历史会议会继续使用已保存的模板快照。此操作不可撤销。`)) {
      onTemplateDelete(id)
      setDeleteConfirmId(null)
    } else {
      setDeleteConfirmId(null)
    }
  }

  // 复制模板
  const handleCopyTemplate = (template: SummaryTemplate) => {
    onTemplateAdd({
      name: `${template.name} (副本)`,
      description: template.description,
      type: 'custom',
      category: template.category || 'general',
      tags: [...template.tags],
      structure: template.structure ? [...template.structure] : undefined,
      prompt: template.prompt,
      isDefault: false,
      isBuiltIn: false,
    })
  }

  // 预览模板
  const handlePreviewTemplate = (template: SummaryTemplate) => {
    setPreviewTemplate(template)
    setShowPreviewModal(true)
  }

  // 设置默认模板
  const handleSetDefault = (id: string) => {
    onSetDefault(id)
  }

  // 过滤模板
  const filteredTemplates = templates.filter(template => {
    const matchesCategory =
      activeCategory === 'all' ||
      (activeCategory === 'builtin' && template.isBuiltIn) ||
      (activeCategory === 'custom' && !template.isBuiltIn)

    const searchLower = searchQuery.toLowerCase()
    const matchesSearch =
      searchQuery === '' ||
      template.name.toLowerCase().includes(searchLower) ||
      template.description.toLowerCase().includes(searchLower) ||
      template.tags.some(tag => tag.toLowerCase().includes(searchLower)) ||
      (template.category && template.category.toLowerCase().includes(searchLower))

    return matchesCategory && matchesSearch
  })

  // 获取表单标题
  const getFormTitle = () => {
    return showEditTemplateModal ? '编辑模板' : '创建新模板'
  }

  return (
    <div className="space-y-6">
      {/* Page Description */}
      <p className="text-base text-[#536172]">
        创建、编辑和管理不同会议场景下的总结模板。
      </p>

      {/* Category Tabs */}
      <div className="flex items-center justify-between gap-6 border-b border-[#D6E1EA]">
        <div className="flex items-center gap-6">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`py-3 px-1 text-sm font-medium transition-colors relative ${
                activeCategory === category.id
                  ? 'text-[#061B35]'
                  : 'text-[#536172] hover:text-[#06162E]'
              }`}
            >
              {category.label}
              {activeCategory === category.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#061B35] rounded-full" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Template Grid */}
      {filteredTemplates.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-2xl border border-[#D6E1EA]">
          {activeCategory === 'custom' && !searchQuery.trim() ? (
            <>
              <p className="text-lg font-medium text-[#06162E] mb-2">暂无自定义模板</p>
              <p className="text-sm text-[#536172]">点击右上角「新建模板」创建你的第一个模板。</p>
            </>
          ) : (
            <>
              <p className="text-lg font-medium text-[#06162E] mb-2">没有找到符合条件的模板</p>
              <p className="text-sm text-[#536172]">请调整搜索关键词或筛选条件。</p>
            </>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-5">
          {filteredTemplates.map((template) => (
            <TemplateCard
              key={template.id}
              id={template.id}
              title={template.name}
              description={template.description}
              category={template.category || 'general'}
              isBuiltin={template.isBuiltIn}
              isDefault={template.isDefault}
              structure={template.structure}
              tags={template.tags}
              onCopy={() => handleCopyTemplate(template)}
              onEdit={!template.isBuiltIn ? () => handleEditTemplate(template) : undefined}
              onPreview={() => handlePreviewTemplate(template)}
              onSetDefault={!template.isDefault ? () => handleSetDefault(template.id) : undefined}
              onDelete={
                !template.isBuiltIn
                  ? () => setDeleteConfirmId(deleteConfirmId === template.id ? null : template.id)
                  : undefined
              }
              showDeleteConfirm={deleteConfirmId === template.id}
              onConfirmDelete={() => handleDeleteTemplate(template.id)}
              onCancelDelete={() => setDeleteConfirmId(null)}
            />
          ))}
        </div>
      )}

      {/* New/Edit Template Modal */}
      {(showNewTemplateModal || showEditTemplateModal) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-[#06162E]">{getFormTitle()}</h2>
              <button
                onClick={() => {
                  resetForm()
                  setEditingTemplate(null)
                  setShowNewTemplateModal(false)
                  setShowEditTemplateModal(false)
                }}
                className="w-8 h-8 rounded-lg hover:bg-[#EEF8FC] flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-[#536172]" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  模板名称 * <span className="text-[#536172] font-normal">（最多 50 个字符）</span>
                </label>
                <input
                  type="text"
                  value={newTemplate.title}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="例如：客户沟通模板"
                  maxLength={50}
                  className="w-full px-4 py-2.5 border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] transition-colors"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  模板描述 * <span className="text-[#536172] font-normal">（最多 200 个字符）</span>
                </label>
                <textarea
                  value={newTemplate.description}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="描述此模板的用途和特点..."
                  rows={3}
                  maxLength={200}
                  className="w-full px-4 py-2.5 border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] transition-colors resize-none"
                />
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  模板分类
                </label>
                <select
                  value={newTemplate.category}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] transition-colors"
                >
                  <option value="general">通用</option>
                  <option value="technical">技术</option>
                  <option value="business">商务</option>
                  <option value="hr">人力资源</option>
                  <option value="education">教育</option>
                  <option value="finance">财务</option>
                </select>
              </div>

              {/* Structure */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  总结结构 * <span className="text-[#536172] font-normal">（至少一个章节）</span>
                </label>
                <div className="space-y-2 mb-2">
                  {newTemplate.structure.map((section, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className="flex-1 px-4 py-2 bg-[#EEF8FC] rounded-lg text-sm text-[#06162E]">
                        {section}
                      </span>
                      <button
                        onClick={() => handleRemoveStructure(index)}
                        className="w-8 h-8 rounded-lg hover:bg-red-50 flex items-center justify-center transition-colors text-red-500"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleAddStructure}
                  className="w-full px-4 py-2 border border-dashed border-[#D6E1EA] rounded-lg text-sm text-[#536172] hover:border-[#061B35] hover:text-[#06162E] transition-colors"
                >
                  + 添加章节
                </button>
              </div>

              {/* Prompt */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  生成要求 / Prompt <span className="text-[#536172] font-normal">（可选）</span>
                </label>
                <textarea
                  value={newTemplate.prompt}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, prompt: e.target.value }))}
                  placeholder="输入 AI 生成要求或自定义提示词..."
                  rows={4}
                  className="w-full px-4 py-2.5 border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] transition-colors resize-none"
                />
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  标签
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={currentTag}
                    onChange={(e) => setCurrentTag(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                    placeholder="输入标签后按回车或点击添加"
                    className="flex-1 px-4 py-2.5 border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] transition-colors"
                  />
                  <button
                    onClick={handleAddTag}
                    className="px-4 py-2.5 bg-[#061B35] text-white rounded-xl hover:bg-[#08213F] transition-colors"
                  >
                    添加
                  </button>
                </div>
                {newTemplate.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {newTemplate.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-[#EEF8FC] text-[#06162E] rounded-lg text-sm"
                      >
                        {tag}
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="hover:text-red-500 transition-colors"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  resetForm()
                  setEditingTemplate(null)
                  setShowNewTemplateModal(false)
                  setShowEditTemplateModal(false)
                }}
                className="flex-1 px-6 py-3 border border-[#D6E1EA] rounded-xl text-[#06162E] font-medium hover:bg-[#EEF8FC] transition-colors"
              >
                取消
              </button>
              <button
                onClick={showEditTemplateModal ? handleSaveEdit : handleSaveTemplate}
                className="flex-1 px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors flex items-center justify-center gap-2"
              >
                <Check className="w-5 h-5" />
                {showEditTemplateModal ? '保存修改' : '创建模板'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreviewModal && previewTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-[#06162E]">模板预览</h2>
              <button
                onClick={() => {
                  setPreviewTemplate(null)
                  setShowPreviewModal(false)
                }}
                className="w-8 h-8 rounded-lg hover:bg-[#EEF8FC] flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-[#536172]" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Basic Info */}
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
                    <Eye className="w-6 h-6 text-[#061B35]" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-[#06162E]">{previewTemplate.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2.5 py-1 text-xs rounded-full ${previewTemplate.isDefault ? 'bg-[#FFA54D] text-white' : 'bg-[#E9F3FF] text-[#061B35]'}`}>
                        {previewTemplate.isDefault ? '默认模板' : previewTemplate.isBuiltIn ? '内置模板' : '自定义模板'}
                      </span>
                      <span className="px-2.5 py-1 bg-[#EEF8FC] text-[#536172] text-xs rounded-full">
                        {previewTemplate.category || 'general'}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-[#536172]">{previewTemplate.description}</p>
              </div>

              {/* Tags */}
              {previewTemplate.tags.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-[#06162E] mb-2">标签</h4>
                  <div className="flex flex-wrap gap-2">
                    {previewTemplate.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-[#E9F3FF] text-[#061B35] text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Structure */}
              <div>
                <h4 className="text-sm font-medium text-[#06162E] mb-2">总结结构</h4>
                <div className="space-y-2">
                  {(previewTemplate.structure || ['会议概要', '关键决策', '行动项']).map((section, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className="w-6 h-6 bg-[#DCEBFF] rounded-full flex items-center justify-center text-xs text-[#061B35] font-medium">
                        {index + 1}
                      </span>
                      <span className="text-sm text-[#06162E]">{section}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Prompt */}
              {previewTemplate.prompt && (
                <div>
                  <h4 className="text-sm font-medium text-[#06162E] mb-2">生成要求 / Prompt</h4>
                  <div className="p-4 bg-[#EEF8FC] rounded-xl text-sm text-[#06162E] whitespace-pre-wrap">
                    {previewTemplate.prompt}
                  </div>
                </div>
              )}
            </div>

            {/* Close Button */}
            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setPreviewTemplate(null)
                  setShowPreviewModal(false)
                }}
                className="px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
