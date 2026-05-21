import { FileText, Star, Copy, Trash2, Edit, Eye } from 'lucide-react'

interface TemplateCardProps {
  id: string
  title: string
  description: string
  category: string
  isBuiltin: boolean
  isDefault: boolean
  structure?: string[]
  tags: string[]
  onCopy?: () => void
  onEdit?: () => void
  onPreview?: () => void
  onSetDefault?: () => void
  onDelete?: () => void
  showDeleteConfirm?: boolean
  onConfirmDelete?: () => void
  onCancelDelete?: () => void
}

export function TemplateCard({
  title,
  description,
  category,
  isBuiltin,
  isDefault,
  tags,
  onCopy,
  onEdit,
  onPreview,
  onSetDefault,
  onDelete,
  showDeleteConfirm,
  onConfirmDelete,
  onCancelDelete
}: TemplateCardProps) {
  return (
    <div className="bg-white rounded-2xl p-5 border border-[#D6E1EA] hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#DCEBFF] rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-[#061B35]" />
          </div>
          <span className="px-2.5 py-1 bg-[#E9F3FF] text-[#061B35] text-xs rounded-full">
            {category}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {isDefault && (
            <span className="px-2.5 py-1 bg-[#FFA54D] text-white text-xs rounded-full flex items-center gap-1">
              <Star className="w-3 h-3" />
              默认
            </span>
          )}
          <span className={`px-2.5 py-1 text-xs rounded-full ${isBuiltin ? 'bg-[#E9F3FF] text-[#061B35]' : 'bg-[#EEF8FC] text-[#536172]'}`}>
            {isBuiltin ? '内置' : '自定义'}
          </span>
        </div>
      </div>

      {/* Content */}
      <h3 className="text-lg font-semibold text-[#06162E] mb-2">{title}</h3>
      <p className="text-sm text-[#536172] line-clamp-2 mb-4">{description}</p>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {tags.map((tag) => (
            <span
              key={tag}
              className="px-2.5 py-1 bg-[#E9F3FF] text-[#061B35] text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="border-t border-[#D6E1EA] pt-4">
        {showDeleteConfirm ? (
          <div className="flex items-center justify-between">
            <span className="text-sm text-[#536172]">确认删除此模板？</span>
            <div className="flex items-center gap-2">
              <button
                onClick={onCancelDelete}
                className="px-3 py-2 text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={onConfirmDelete}
                className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                确认删除
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-sm">
            <button
              onClick={onPreview}
              className="px-3 py-2 text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors flex items-center gap-1"
            >
              <Eye className="w-4 h-4" />
              预览
            </button>
            {!isBuiltin && onEdit && (
              <>
                <span className="text-[#D6E1EA]">•</span>
                <button
                  onClick={onEdit}
                  className="px-3 py-2 text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors flex items-center gap-1"
                >
                  <Edit className="w-4 h-4" />
                  编辑
                </button>
              </>
            )}
            <span className="text-[#D6E1EA]">•</span>
            <button
              onClick={onCopy}
              className="px-3 py-2 text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors flex items-center gap-1"
            >
              <Copy className="w-4 h-4" />
              {isBuiltin ? '复制为自定义' : '复制'}
            </button>
            {!isDefault && onSetDefault && (
              <>
                <span className="text-[#D6E1EA]">•</span>
                <button
                  onClick={onSetDefault}
                  className="px-3 py-2 text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors"
                >
                  设为默认
                </button>
              </>
            )}
            {!isBuiltin && onDelete && (
              <>
                <span className="text-[#D6E1EA]">•</span>
                <button
                  onClick={onDelete}
                  className="px-3 py-2 text-[#FF6B6B] hover:bg-[#FFE7E7] rounded-lg transition-colors flex items-center gap-1"
                >
                  <Trash2 className="w-4 h-4" />
                  删除
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
