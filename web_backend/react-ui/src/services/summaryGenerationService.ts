/**
 * Summary Generation Service
 * 提供会议总结生成的统一接口
 *
 * 当前支持：
 * - 后端API调用（优先）
 * - 本地fallback模式（后端不可用时）
 */

import type { Meeting, SummaryTemplate } from '../types/models';
import { apiClient } from './apiClient';

export type SummaryProvider = 'fallback' | 'backend' | 'manual';

export interface SummaryGenerationOptions {
  transcript: string;
  template: SummaryTemplate;
  meeting: Meeting;
}

export interface GenerateSummaryInput {
  meetingId: string;
  transcript: string;
  templateId?: string;
  templateSnapshot?: {
    id: string;
    name: string;
    description?: string;
    structure?: string[];
    prompt?: string;
  };
}

export interface SummaryResult {
  summary: string;
  provider: SummaryProvider;
  isFallback: boolean;
  templateId?: string;
  templateName?: string;
  processingTime?: number;
  error?: string;
}

/**
 * 生成会议总结（统一接口）
 * 优先尝试调用后端API: /api/v1/summarize
 * 失败时回退到本地模式
 */
export async function generateMeetingSummary(input: GenerateSummaryInput): Promise<SummaryResult> {
  const { meetingId, transcript, templateSnapshot, templateId } = input;

  console.log('[SummaryGenerationService] 开始生成总结:', {
    transcriptLength: transcript.length,
    transcriptPreview: transcript.substring(0, 100),
    hasTemplate: !!templateSnapshot,
  });

  // 1. 验证文字稿非空
  const validation = validateTranscript(transcript);
  if (!validation.valid) {
    console.log('[SummaryGenerationService] Transcript 验证失败:', validation.error);
    return {
      summary: '',
      provider: 'fallback',
      isFallback: true,
      error: validation.error || '文字稿验证失败'
    };
  }

  const template = templateSnapshot;

  if (!template) {
    return {
      summary: '',
      provider: 'fallback',
      isFallback: true,
      error: '未找到有效的总结模板'
    };
  }

  try {
    // 2. 尝试调用后端 API: /api/v1/summarize
    console.log('[SummaryGenerationService] 调用后端总结 API:', {
      transcriptLength: transcript.trim().length,
      template: template.name,
    });

    const response = await apiClient.post<{
      success: boolean;
      summary?: string;
      provider: string;
      isFallback: boolean;
      templateName?: string;
      processingTimeMs?: number;
      error?: string;
    }>('/v1/summarize', {
      transcript: transcript.trim(),
      template_name: template.name,
      template_description: template.description || '',
      template_sections: template.structure || [],
      template_prompt: template.prompt || '',
    });

    console.log('[SummaryGenerationService] 后端响应:', {
      success: response.success,
      data: response.data,
      error: response.error,
    });

    if (response.success && response.data) {
      const data = response.data;

      // 检查后端是否成功生成总结
      if (data.success && data.summary) {
        console.log('[SummaryGenerationService] 后端总结成功:', {
          provider: data.provider,
          isFallback: data.isFallback,
        });
        return {
          summary: data.summary,
          provider: data.provider === 'backend' ? 'backend' : 'fallback',
          isFallback: data.isFallback,
          templateId: template.id,
          templateName: data.templateName || template.name,
          processingTime: data.processingTimeMs,
        };
      } else {
        // 后端返回失败，尝试 fallback
        throw new Error(data.error || '后端总结生成失败');
      }
    } else {
      throw new Error(response.error || '后端总结服务返回错误');
    }

  } catch (error) {
    console.error('[SummaryGenerationService] 后端总结失败:', error);

    // 不再静默回退到本地生成，明确返回错误
    const errorMessage = error instanceof Error ? error.message : '后端总结服务调用失败';

    return {
      summary: '',
      provider: 'backend',
      isFallback: false,
      error: errorMessage,
      templateId: template.id,
      templateName: template.name,
    };
  }
}

/**
 * 内部 fallback 总结生成逻辑
 */
function generateFallbackSummaryInternal(transcript: string, template: any, meetingContext?: any): string {
  // 使用模板的 structure，如果没有则使用默认章节
  const defaultSections = ['会议概要', '关键决策', '行动项'];
  const sections = (template?.structure && template.structure.length > 0)
    ? template.structure
    : defaultSections;

  // 按段落处理文字稿
  const transcriptParagraphs = transcript
    .split('\n')
    .filter(p => p.trim())
    .slice(0, 5); // 取前5段作为示例

  const participantsList = meetingContext?.participants && meetingContext.participants.length > 0
    ? meetingContext.participants.join('、')
    : '未记录';

  const title = meetingContext?.title || '会议';
  const date = meetingContext?.date || new Date().toISOString().split('T')[0];
  const duration = meetingContext?.duration || '待填写';
  const templateName = template?.name || '默认模板';

  const summaryParts = [
    `# ${title}`,
    '',
    `> 本总结基于用户手动粘贴的会议文字稿和「${templateName}」模板生成。`,
    '',
    '## 基本信息',
    `- **会议日期**: ${date}`,
    `- **会议时长**: ${duration}`,
    `- **参会人员**: ${participantsList}`,
    '',
    ...(template?.structure || ['会议概要', '关键决策', '行动项']).flatMap((section: string) => [
      `## ${section}`,
      '',
      ...transcriptParagraphs.map(p => `${p}`),
      '',
      '*请基于以上文字稿进一步整理此章节内容。*',
      '',
    ]),
  ];

  return summaryParts.join('\n');
}

/**
 * Generate fallback summary using manual transcript and template (向后兼容)
 */
export function generateFallbackSummary(options: SummaryGenerationOptions): string {
  const { transcript, template, meeting } = options;

  return generateFallbackSummaryInternal(transcript, template, meeting);
}

/**
 * Validate transcript before generating summary
 */
export function validateTranscript(transcript: string): { valid: boolean; error?: string } {
  const trimmed = transcript.trim();

  if (!trimmed) {
    return { valid: false, error: '请先粘贴会议文字稿' };
  }

  if (trimmed.length < 10) {
    return { valid: false, error: '文字稿内容过少，请补充更多内容' };
  }

  return { valid: true };
}

/**
 * 检查是否可以使用真实总结服务
 */
export async function canUseRealSummaryGeneration(): Promise<boolean> {
  try {
    const response = await apiClient.get<{
      status: string;
      summaryFallback: boolean;
    }>('/v1/health');

    return response.success && response.data?.summaryFallback === false;
  } catch {
    return false;
  }
}

/**
 * 获取总结服务状态描述
 */
export async function getSummaryServiceStatus(): Promise<{
  available: boolean;
  provider: SummaryProvider;
  description: string;
}> {
  try {
    const response = await apiClient.get<{
      summary: {
        type: string;
        available: boolean;
      };
    }>('/v1/providers/info');

    if (response.success && response.data?.summary) {
      const { type, available } = response.data.summary;
      return {
        available,
        provider: type === 'backend' ? 'backend' : 'fallback',
        description: available
          ? `使用 ${type} 模式生成会议总结`
          : '后端总结服务暂不可用，使用本地 fallback 模式'
      };
    }
  } catch {
    // 忽略错误
  }

  return {
    available: false,
    provider: 'fallback',
    description: '后端服务不可用，使用本地 fallback 模式'
  };
}

/**
 * 标记总结为手动编辑
 */
export function markSummaryAsManual(meeting: Meeting): Partial<Meeting> {
  return {
    summaryProvider: 'manual',
    summaryIsFallback: false,
    updatedAt: new Date().toISOString()
  };
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
