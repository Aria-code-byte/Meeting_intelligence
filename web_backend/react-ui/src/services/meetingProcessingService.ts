/**
 * Meeting Processing Service
 * 当前后端状态轮询接口不稳定，阶段 3A 使用纯前端 fallback 流程
 */

import type { Meeting, SummaryTemplate } from '../types/models';

export interface ProcessingOptions {
  file: File;
  title: string;
  templateId: string;
  localMeetingId: string;
  onProgress?: (stage: ProcessingStage, progress: number, data?: any) => void;
  onComplete?: (result: FallbackResult) => void;
  onError?: (error: string) => void;
}

export interface FallbackResult {
  mode: 'fallback';
  meetingId: string;
  templateId: string;
  message: string;
  transcript?: string;
  summary?: string;
}

export type ProcessingStage =
  | 'uploading'
  | 'uploaded'
  | 'transcribing'
  | 'summarizing'
  | 'completed'
  | 'failed';

/**
 * Process a meeting file
 * 阶段 3A: 纯前端 fallback，不调用后端轮询接口
 * 创建会议记录后，等待用户手动补充文字稿
 */
export async function processMeeting(options: ProcessingOptions): Promise<FallbackResult> {
  const {
    file,
    title,
    templateId,
    localMeetingId,
    onProgress = () => {},
    onComplete = () => {},
    onError = () => {},
  } = options;

  try {
    // 纯前端模式：只创建会议记录，不调用后端
    onProgress('uploaded', 20, { localMeetingId, templateId });

    const result: FallbackResult = {
      mode: 'fallback',
      meetingId: localMeetingId,
      templateId,
      message: '后端转写服务暂不可用，请手动补充文字稿后生成总结。',
    };

    onComplete(result);
    return result;

  } catch (error) {
    onError('后端转写服务暂不可用，请手动补充文字稿后生成总结。');
    throw error;
  }
}

/**
 * Get the default template from localStorage
 */
export function getDefaultTemplate(templates: SummaryTemplate[]): SummaryTemplate | null {
  const defaultTemplate = templates.find(t => t.isDefault);
  return defaultTemplate || templates[0] || null;
}

/**
 * Convert backend template format to frontend SummaryTemplate
 * 保留用于未来后端集成
 */
export function convertBackendTemplate(backendTemplate: any): SummaryTemplate {
  const now = new Date().toISOString()
  return {
    id: String(backendTemplate.id),
    name: backendTemplate.name,
    description: backendTemplate.description,
    type: backendTemplate.is_builtin ? 'built-in' : 'custom',
    category: backendTemplate.category || 'general',
    tags: [],
    prompt: backendTemplate.prompt,
    structure: backendTemplate.sections,
    isDefault: backendTemplate.id === 'general_meeting',
    isBuiltIn: backendTemplate.is_builtin === true,
    createdAt: now,
    updatedAt: now,
  };
}
