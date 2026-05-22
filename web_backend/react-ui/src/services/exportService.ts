/**
 * Export service for meeting data
 * Supports Markdown, TXT, and JSON export formats
 */

import type { Meeting, ActionItem, SummaryTemplate } from '../types/models';

export type ExportFormat = 'markdown' | 'txt' | 'json';

interface ExportOptions {
  format: ExportFormat;
  includeTranscript?: boolean;
  includeActionItems?: boolean;
  allTemplates?: SummaryTemplate[];
}

/**
 * Get template name with fallback priority
 */
function getTemplateName(meeting: Meeting, allTemplates?: SummaryTemplate[]): string {
  if ((meeting as any).templateSnapshot?.name) {
    return (meeting as any).templateSnapshot.name
  }
  if ((meeting as any).templateName) {
    return (meeting as any).templateName
  }
  if (meeting.templateId && allTemplates) {
    const template = allTemplates.find(t => t.id === meeting.templateId)
    if (template) return template.name
  }
  return '未知模板'
}

/**
 * Get status text in Chinese
 */
function getStatusText(status: Meeting['status']): string {
  switch (status) {
    case 'completed':
      return '已完成'
    case 'uploaded':
      return '已上传'
    case 'transcribing':
      return '转录中'
    case 'summarizing':
      return '总结中'
    case 'failed':
      return '失败'
    default:
      return status
  }
}

/**
 * Generate Markdown format meeting report
 */
function generateMarkdown(meeting: Meeting, actionItems: ActionItem[], options: ExportOptions): string {
  const lines: string[] = []

  // Title and metadata
  lines.push(`# ${meeting.title}`)
  lines.push('')
  lines.push('**会议信息**')
  lines.push('')
  lines.push(`- **日期**: ${meeting.date}`)
  lines.push(`- **时长**: ${meeting.duration}`)
  if (meeting.participants && meeting.participants.length > 0) {
    lines.push(`- **参会人员**: ${meeting.participants.join(', ')}`)
  } else {
    lines.push(`- **参会人员**: 暂无参会人员`)
  }
  if (meeting.audioFileName) {
    lines.push(`- **音频文件**: ${meeting.audioFileName}`)
  } else {
    lines.push(`- **音频文件**: 未知音频文件`)
  }
  lines.push(`- **模板**: ${getTemplateName(meeting, options.allTemplates)}`)
  if (meeting.templateId) {
    lines.push(`- **模板ID**: ${meeting.templateId}`)
  }
  lines.push(`- **状态**: ${getStatusText(meeting.status)}`)
  lines.push(`- **创建时间**: ${new Date(meeting.createdAt).toLocaleString('zh-CN')}`)
  lines.push(`- **更新时间**: ${new Date(meeting.updatedAt).toLocaleString('zh-CN')}`)

  // Status warning for processing meetings only
  if (meeting.status !== 'completed' && meeting.status !== 'failed') {
    lines.push('')
    lines.push('> ⚠️ **会议仍在处理中，部分内容可能尚未生成**')
  }
  lines.push('')

  // Summary section
  lines.push('## AI 总结')
  lines.push('')
  if (meeting.summary) {
    lines.push(meeting.summary)
  } else {
    lines.push('*暂无总结内容*')
  }
  lines.push('')

  // Transcript section
  if (options.includeTranscript) {
    lines.push('## 完整文字稿')
    lines.push('')
    if (meeting.transcript) {
      lines.push(meeting.transcript)
    } else {
      lines.push('*暂无文字稿*')
    }
    lines.push('')
  }

  // Action items section
  lines.push('## 待办事项')
  lines.push('')

  if (actionItems.length === 0) {
    lines.push('*暂无行动项*')
  } else {
    const todoItems = actionItems.filter(a => a.status === 'todo')
    const inProgressItems = actionItems.filter(a => a.status === 'in_progress')
    const doneItems = actionItems.filter(a => a.status === 'done')

    if (todoItems.length > 0) {
      lines.push('### 待处理')
      todoItems.forEach(item => {
        lines.push(`- [ ] ${item.content}${item.owner ? ` (@${item.owner})` : ''}${item.dueDate ? ` (截止: ${item.dueDate})` : ''}`)
      })
      lines.push('')
    }

    if (inProgressItems.length > 0) {
      lines.push('### 进行中')
      inProgressItems.forEach(item => {
        lines.push(`- [~] ${item.content}${item.owner ? ` (@${item.owner})` : ''}${item.dueDate ? ` (截止: ${item.dueDate})` : ''}`)
      })
      lines.push('')
    }

    if (doneItems.length > 0) {
      lines.push('### 已完成')
      doneItems.forEach(item => {
        lines.push(`- [x] ${item.content}${item.owner ? ` (@${item.owner})` : ''}`)
      })
      lines.push('')
    }
  }
  lines.push('')

  return lines.join('\n');
}

/**
 * Generate TXT format meeting report
 */
function generateTxt(meeting: Meeting, actionItems: ActionItem[], options: ExportOptions): string {
  const lines: string[] = []

  // Title and metadata
  lines.push(`会议标题: ${meeting.title}`)
  lines.push('')
  lines.push('会议信息:')
  lines.push(`  日期: ${meeting.date}`)
  lines.push(`  时长: ${meeting.duration}`)
  if (meeting.participants && meeting.participants.length > 0) {
    lines.push(`  参会人员: ${meeting.participants.join(', ')}`)
  } else {
    lines.push(`  参会人员: 暂无参会人员`)
  }
  if (meeting.audioFileName) {
    lines.push(`  音频文件: ${meeting.audioFileName}`)
  } else {
    lines.push(`  音频文件: 未知音频文件`)
  }
  lines.push(`  模板: ${getTemplateName(meeting, options.allTemplates)}`)
  if (meeting.templateId) {
    lines.push(`  模板ID: ${meeting.templateId}`)
  }
  lines.push(`  状态: ${getStatusText(meeting.status)}`)
  lines.push(`  创建时间: ${new Date(meeting.createdAt).toLocaleString('zh-CN')}`)
  lines.push(`  更新时间: ${new Date(meeting.updatedAt).toLocaleString('zh-CN')}`)

  // Status warning for processing meetings only
  if (meeting.status !== 'completed' && meeting.status !== 'failed') {
    lines.push('')
    lines.push('⚠️  会议仍在处理中，部分内容可能尚未生成')
  }
  lines.push('')

  // Summary section
  lines.push('=== AI 总结 ===')
  lines.push('')
  if (meeting.summary) {
    lines.push(meeting.summary)
  } else {
    lines.push('暂无总结内容')
  }
  lines.push('')

  // Transcript section
  if (options.includeTranscript) {
    lines.push('=== 完整文字稿 ===')
    lines.push('')
    if (meeting.transcript) {
      lines.push(meeting.transcript)
    } else {
      lines.push('暂无文字稿')
    }
    lines.push('')
  }

  // Action items section
  lines.push('=== 待办事项 ===')
  lines.push('')

  if (actionItems.length === 0) {
    lines.push('暂无行动项')
  } else {
    actionItems.forEach(item => {
      const status = item.status === 'done' ? '[完成]' : item.status === 'in_progress' ? '[进行中]' : '[待处理]'
      lines.push(`${status} ${item.content}`)
      if (item.owner) lines.push(`  负责人: ${item.owner}`)
      if (item.dueDate) lines.push(`  截止日期: ${item.dueDate}`)
      lines.push('')
    })
  }
  lines.push('')

  return lines.join('\n')
}

/**
 * Generate JSON format meeting data
 */
function generateJson(meeting: Meeting, actionItems: ActionItem[], options: ExportOptions): string {
  const exportData = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    meeting: {
      id: meeting.id,
      title: meeting.title,
      date: meeting.date,
      duration: meeting.duration,
      participants: meeting.participants || [],
      status: meeting.status,
      audioFileName: meeting.audioFileName || null,
      templateId: meeting.templateId || null,
      templateName: getTemplateName(meeting, options.allTemplates),
      templateSnapshot: (meeting as any).templateSnapshot || null,
      summary: meeting.summary || null,
      transcript: options.includeTranscript ? (meeting.transcript || null) : undefined,
      errorMessage: meeting.errorMessage || null,
      createdAt: meeting.createdAt,
      updatedAt: meeting.updatedAt,
    },
    actionItems: options.includeActionItems ? actionItems.map(item => ({
      id: item.id,
      meetingId: item.meetingId,
      content: item.content,
      owner: item.owner || null,
      dueDate: item.dueDate || null,
      status: item.status,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt,
    })) : [],
  }

  return JSON.stringify(exportData, null, 2)
}

/**
 * Get MIME type for export format
 */
function getMimeType(format: ExportFormat): string {
  switch (format) {
    case 'markdown':
      return 'text/markdown';
    case 'json':
      return 'application/json';
    case 'txt':
    default:
      return 'text/plain';
  }
}

/**
 * Get file extension for export format
 */
function getFileExtension(format: ExportFormat): string {
  switch (format) {
    case 'markdown':
      return '.md';
    case 'json':
      return '.json';
    case 'txt':
    default:
      return '.txt';
  }
}

/**
 * Sanitize filename for safe file system usage
 */
function sanitizeFilename(name: string): string {
  return name
    .replace(/[<>:"/\\|?*]/g, '_')
    .replace(/\s+/g, '_')
    .substring(0, 100);
}

/**
 * Export meeting data to specified format
 */
export function exportMeeting(
  meeting: Meeting,
  actionItems: ActionItem[],
  options: ExportOptions
): void {
  let content: string;
  let filename: string;

  const sanitizedName = sanitizeFilename(meeting.title);
  const extension = getFileExtension(options.format);

  switch (options.format) {
    case 'markdown':
      content = generateMarkdown(meeting, actionItems, options);
      filename = `${sanitizedName}${extension}`;
      break;
    case 'json':
      content = generateJson(meeting, actionItems, options);
      filename = `${sanitizedName}${extension}`;
      break;
    case 'txt':
    default:
      content = generateTxt(meeting, actionItems, options);
      filename = `${sanitizedName}${extension}`;
      break;
  }

  // Create download
  const mimeType = getMimeType(options.format);
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Check if export is available for given content
 */
export function canExport(meeting: Meeting | null): boolean {
  if (!meeting) return false;
  return !!(meeting.summary || meeting.transcript);
}
