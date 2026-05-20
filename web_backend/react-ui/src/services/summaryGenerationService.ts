/**
 * Summary Generation Service
 * 前端 fallback 总结生成服务
 * 使用手动输入的文字稿和模板生成总结
 */

import type { Meeting, SummaryTemplate } from '../types/models';

export interface SummaryGenerationOptions {
  transcript: string;
  template: SummaryTemplate;
  meeting: Meeting;
}

/**
 * Generate fallback summary using manual transcript and template
 */
export function generateFallbackSummary(options: SummaryGenerationOptions): string {
  const { transcript, template, meeting } = options;

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

  const participantsList = meeting.participants && meeting.participants.length > 0
    ? meeting.participants.join('、')
    : '未记录';

  const summaryParts = [
    `# ${meeting.title}`,
    '',
    `> 本总结基于用户手动粘贴的会议文字稿和「${template?.name || '默认模板'}」模板生成。`,
    '',
    '## 基本信息',
    `- **会议日期**: ${meeting.date}`,
    `- **会议时长**: ${meeting.duration}`,
    `- **参会人员**: ${participantsList}`,
    '',
    ...sections.flatMap(section => [
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
