import { useState } from 'react'
import { Plus, X, Check } from 'lucide-react'
import { TemplateCard } from '../components/TemplateCard'
import type { Template } from '../App'

interface TemplatePageProps {
  templates: Template[]
  onTemplateAdd: (template: Omit<Template, 'id'>) => void
  onTemplateDelete: (id: number) => void
}

const categories = [
  { id: 'all', label: '全部模板' },
  { id: 'builtin', label: '内置模板' },
  { id: 'custom', label: '自定义模板' },
]

export function TemplatePage({ templates, onTemplateAdd, onTemplateDelete }: TemplatePageProps) {
  const [activeCategory, setActiveCategory] = useState('all')
  const [showNewTemplateModal, setShowNewTemplateModal] = useState(false)
  const [newTemplate, setNewTemplate] = useState({
    title: '',
    description: '',
    category: '',
    tags: [] as string[],
    currentTag: ''
  })
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  // Filter templates based on category
  const filteredTemplates = templates.filter(template => {
    if (activeCategory === 'all') return true
    if (activeCategory === 'builtin') return template.isBuiltin
    if (activeCategory === 'custom') return !template.isBuiltin
    return true
  })

  const handleAddTag = () => {
    if (newTemplate.currentTag.trim() && !newTemplate.tags.includes(newTemplate.currentTag.trim())) {
      setNewTemplate(prev => ({
        ...prev,
        tags: [...prev.tags, prev.currentTag.trim()],
        currentTag: ''
      }))
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setNewTemplate(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  const handleSaveTemplate = () => {
    if (!newTemplate.title.trim() || !newTemplate.description.trim()) {
      return
    }

    onTemplateAdd({
      title: newTemplate.title,
      description: newTemplate.description,
      category: newTemplate.category || 'general',
      isBuiltin: false,
      tags: newTemplate.tags
    })

    // Reset form
    setNewTemplate({
      title: '',
      description: '',
      category: '',
      tags: [],
      currentTag: ''
    })
    setShowNewTemplateModal(false)
  }

  const handleDeleteTemplate = (id: number) => {
    onTemplateDelete(id)
    setDeleteConfirmId(null)
  }

  const handleCopyTemplate = (template: Template) => {
    onTemplateAdd({
      title: `${template.title} (副本)`,
      description: template.description,
      category: template.category,
      isBuiltin: false,
      tags: [...template.tags]
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-[#06162E] mb-2">模板管理</h1>
          <p className="text-lg text-[#536172]">
            创建、编辑和管理不同会议场景下的总结模板。
          </p>
        </div>
        <button
          onClick={() => setShowNewTemplateModal(true)}
          className="flex items-center gap-2 px-5 py-3 bg-[#061B35] text-white rounded-xl hover:bg-[#08213F] transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">新建模板</span>
        </button>
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-6 border-b border-[#D6E1EA]">
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

      {/* Template Grid */}
      <div className="grid grid-cols-3 gap-5">
        {filteredTemplates.map((template) => (
          <TemplateCard
            key={template.id}
            {...template}
            onCopy={() => handleCopyTemplate(template)}
            onDelete={
              !template.isBuiltin
                ? () => setDeleteConfirmId(deleteConfirmId === template.id ? null : template.id)
                : undefined
            }
            showDeleteConfirm={deleteConfirmId === template.id}
            onConfirmDelete={() => handleDeleteTemplate(template.id)}
            onCancelDelete={() => setDeleteConfirmId(null)}
          />
        ))}

        {/* Create New Template Card */}
        <div
          onClick={() => setShowNewTemplateModal(true)}
          className="bg-white rounded-2xl border-2 border-dashed border-[#D6E1EA] p-6 flex flex-col items-center justify-center text-center hover:border-[#061B35] transition-colors cursor-pointer min-h-[280px]"
        >
          <div className="w-14 h-14 bg-[#DCEBFF] rounded-full flex items-center justify-center mb-4">
            <Plus className="w-7 h-7 text-[#061B35]" />
          </div>
          <h3 className="text-lg font-semibold text-[#06162E] mb-2">
            创建自定义模板
          </h3>
          <p className="text-sm text-[#536172]">
            （自定义输出结构、摘要格式和 AI 提示词）
          </p>
        </div>
      </div>

      {/* New Template Modal */}
      {showNewTemplateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-[#06162E]">创建新模板</h2>
              <button
                onClick={() => setShowNewTemplateModal(false)}
                className="w-8 h-8 rounded-lg hover:bg-[#EEF8FC] flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-[#536172]" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  模板名称 *
                </label>
                <input
                  type="text"
                  value={newTemplate.title}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="例如：客户沟通模板"
                  className="w-full px-4 py-2.5 border border-[#D6E1EA] rounded-xl focus:outline-none focus:border-[#061B35] transition-colors"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  模板描述 *
                </label>
                <textarea
                  value={newTemplate.description}
                  onChange={(e) => setNewTemplate(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="描述此模板的用途和特点..."
                  rows={3}
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
                  <option value="">选择分类</option>
                  <option value="general">通用</option>
                  <option value="technical">技术</option>
                  <option value="business">商务</option>
                  <option value="hr">人力资源</option>
                </select>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-[#06162E] mb-2">
                  标签
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newTemplate.currentTag}
                    onChange={(e) => setNewTemplate(prev => ({ ...prev, currentTag: e.target.value }))}
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
                onClick={() => setShowNewTemplateModal(false)}
                className="flex-1 px-6 py-3 border border-[#D6E1EA] rounded-xl text-[#06162E] font-medium hover:bg-[#EEF8FC] transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSaveTemplate}
                disabled={!newTemplate.title.trim() || !newTemplate.description.trim()}
                className="flex-1 px-6 py-3 bg-[#061B35] text-white rounded-xl font-medium hover:bg-[#08213F] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Check className="w-5 h-5" />
                保存模板
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
