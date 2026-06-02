/**
 * Core data models for Jinni AI
 * These types define the structure of all persistent data
 */

export type MeetingStatus =
  | 'uploaded'
  | 'transcribing'
  | 'enhancing'
  | 'summarizing'
  | 'completed'
  | 'failed';

/**
 * TranscriptTurn - 说话人轮次（阶段 10B-4）
 * 用于展示 WhisperX + pyannote 生成的说话人分离转录结果
 */
export interface TranscriptTurn {
  speaker: string;
  start: number | null;
  end: number | null;
  text: string;
}

/**
 * EnhancedTranscriptTurn - LLM 优化后的说话人轮次
 * 与 TranscriptTurn 结构相同，但文本经过 LLM 优化
 */
export interface EnhancedTranscriptTurn {
  speaker: string;
  start: number | null;
  end: number | null;
  text: string;
}

export interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  participants: string[];
  status: MeetingStatus;
  progress?: number;
  templateId?: string;
  templateName?: string;
  templateSnapshot?: {
    id: string;
    name: string;
    structure?: string[];
    prompt?: string;
  };
  audioFileName?: string;
  audioFileUrl?: string;
  transcript?: string;
  // 阶段 10B-4：新增 transcriptTurns 字段
  transcriptTurns?: TranscriptTurn[];
  // LLM 优化后的说话人轮次
  enhancedTranscriptTurns?: EnhancedTranscriptTurn[];
  summary?: string;
  actionItemIds?: string[];
  errorMessage?: string;
  backendMeetingId?: string;
  // AI 处理来源字段
  // 阶段 10B-4：扩展 transcriptionProvider 支持 whisperx
  transcriptionProvider?: 'fallback' | 'backend' | 'manual' | 'whisperx';
  summaryProvider?: 'fallback' | 'backend' | 'manual';
  transcriptionIsFallback?: boolean;
  summaryIsFallback?: boolean;
  // LLM 优化相关字段
  enhancementProvider?: 'deepseek' | 'openai' | 'anthropic' | 'glm' | 'manual';
  enhancementModel?: string;
  isEnhanced?: boolean;
  enhancementTime?: string;
  // 阶段 10B-4：新增 provider metadata 字段
  transcriptionModel?: string;
  diarizationEnabled?: boolean;
  diarizationProvider?: string;
  diarizationModel?: string;
  alignmentStatus?: 'success' | 'skipped' | 'failed';
  alignmentError?: string;
  summaryModel?: string;
  processingError?: string;
  lastProcessedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SummaryTemplate {
  id: string;
  name: string;
  description: string;
  type: 'built-in' | 'custom';
  category?: string;
  tags: string[];
  prompt?: string;
  structure?: string[];
  isDefault: boolean;
  isBuiltIn: boolean;
  createdAt: string;
  updatedAt: string;
}

export type ActionItemStatus = 'todo' | 'in_progress' | 'done';

export interface ActionItem {
  id: string;
  meetingId: string;
  content: string;
  owner?: string;
  dueDate?: string;
  status: ActionItemStatus;
  createdAt: string;
  updatedAt: string;
}
