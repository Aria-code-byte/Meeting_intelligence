/**
 * Help panel component
 * Static help content with usage instructions and current limitations
 */

import { X, Upload, FileText, CheckSquare, Download, AlertCircle } from 'lucide-react'

interface HelpPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function HelpPanel({ isOpen, onClose }: HelpPanelProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#D6E1EA]">
          <h2 className="text-xl font-semibold text-[#06162E]">使用帮助</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-[#536172] hover:text-[#06162E] hover:bg-[#EEF8FC] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)] space-y-6">
          {/* How to Upload */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Upload className="w-5 h-5 text-[#061B35]" />
              <h3 className="text-lg font-medium text-[#06162E]">如何上传会议</h3>
            </div>
            <ol className="list-decimal list-inside space-y-2 text-sm text-[#536172]">
              <li>在工作台点击上传区域选择音频文件</li>
              <li>输入会议标题</li>
              <li>选择总结模板（默认为"通用会议模板"）</li>
              <li>点击"开始处理"</li>
              <li>处理完成后可手动补充文字稿并生成总结</li>
            </ol>
          </section>

          {/* How to Select Template */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-[#061B35]" />
              <h3 className="text-lg font-medium text-[#06162E]">如何选择总结模板</h3>
            </div>
            <ul className="list-disc list-inside space-y-2 text-sm text-[#536172]">
              <li>上传时在右侧模板选择器中选择</li>
              <li>不同模板有不同的总结结构和提示词</li>
              <li>可在"设置"中修改默认模板</li>
              <li>支持自定义模板（模板管理页面）</li>
            </ul>
          </section>

          {/* How to Edit Summary */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-5 h-5 text-[#061B35]" />
              <h3 className="text-lg font-medium text-[#06162E]">如何编辑总结</h3>
            </div>
            <ul className="list-disc list-inside space-y-2 text-sm text-[#536172]">
              <li>打开会议详情页，在"AI 总结"标签页点击编辑按钮</li>
              <li>可直接修改总结内容</li>
              <li>点击"保存"按钮保存修改</li>
              <li>也可编辑会议标题和重新生成总结</li>
            </ul>
          </section>

          {/* How to Manage Action Items */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <CheckSquare className="w-5 h-5 text-[#061B35]" />
              <h3 className="text-lg font-medium text-[#06162E]">如何管理行动项</h3>
            </div>
            <ul className="list-disc list-inside space-y-2 text-sm text-[#536172]">
              <li>在"待办事项"标签页查看所有行动项</li>
              <li>点击"+"按钮添加新行动项</li>
              <li>点击行动项旁的编辑按钮修改内容、负责人、截止日期</li>
              <li>点击状态图标切换状态（待处理→进行中→已完成）</li>
              <li>点击删除按钮移除行动项</li>
            </ul>
          </section>

          {/* How to Export */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Download className="w-5 h-5 text-[#061B35]" />
              <h3 className="text-lg font-medium text-[#06162E]">如何导出数据</h3>
            </div>
            <ul className="list-disc list-inside space-y-2 text-sm text-[#536172]">
              <li>在会议详情页或会议库中点击"下载/导出"按钮</li>
              <li>选择导出格式：Markdown、TXT 或 JSON</li>
              <li>可选择是否包含完整文字稿</li>
              <li>点击"导出"按钮下载文件</li>
            </ul>
          </section>

          {/* Current Limitations */}
          <section className="pt-6 border-t border-[#D6E1EA]">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-5 h-5 text-[#F59E0B]" />
              <h3 className="text-lg font-medium text-[#06162E]">当前限制</h3>
            </div>
            <div className="bg-[#EEF8FC] rounded-xl p-4 space-y-2 text-sm text-[#536172]">
              <p>• <strong>数据存储</strong>：当前使用本地浏览器存储数据，清除浏览器数据会丢失所有内容</p>
              <p>• <strong>真实转录</strong>：暂未接入后端转录服务，需手动粘贴文字稿</p>
              <p>• <strong>云同步</strong>：未启用云端同步功能</p>
              <p>• <strong>导出格式</strong>：暂不支持 PDF、DOCX 导出</p>
              <p>• <strong>分享功能</strong>：分享链接功能即将支持</p>
              <p>• <strong>账户系统</strong>：账户登录功能即将支持</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
