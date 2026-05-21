/**
 * Transcription Service
 * 提供音频转文字的统一接口
 *
 * 当前支持：
 * - 后端API调用（优先）：/api/v1/transcribe
 * - WhisperX + pyannote 说话人分离（阶段 10B-4）
 * - 本地fallback模式（后端不可用时）
 */

import type { Meeting, TranscriptTurn } from '../types/models';
import { apiClient } from './apiClient';

export type TranscriptionProvider = 'fallback' | 'backend' | 'manual' | 'whisperx';

export interface TranscriptionInput {
  meetingId: string;
  file?: File;
  audioFileName?: string;
}

/**
 * 阶段 10B-4：扩展 TranscriptionResult 支持 speaker turns
 */
export interface TranscriptionResult {
  transcript: string;
  // 阶段 10B-4：新增 transcriptTurns
  transcriptTurns?: TranscriptTurn[];
  provider: TranscriptionProvider;
  isFallback: boolean;
  processingTime?: number;
  error?: string;
  // 阶段 10B-4：新增 provider metadata 字段
  transcriptionModel?: string;
  diarizationEnabled?: boolean;
  diarizationProvider?: string;
  diarizationModel?: string;
  alignmentStatus?: 'success' | 'skipped' | 'failed';
  alignmentError?: string;
}

/**
 * 转录会议音频
 * 优先尝试调用后端API，失败时回退到本地模式
 */
export async function transcribeMeetingAudio(input: TranscriptionInput): Promise<TranscriptionResult> {
  const { meetingId, file, audioFileName } = input;

  // 如果没有提供文件，直接返回 fallback 模式
  if (!file) {
    return {
      transcript: '',
      provider: 'fallback',
      isFallback: true,
      error: '请提供音频文件进行转录'
    };
  }

  try {
    console.log('[TranscriptionService] 开始转录:', {
      fileName: audioFileName,
      fileSize: file?.size,
    });

    // 创建 FormData 用于文件上传
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_size', 'base');
    formData.append('language', 'zh');

    // 调用后端 API: /api/v1/transcribe
    // 阶段 10B-4：更新 API 响应类型匹配后端 WhisperXTranscriptionProvider
    const response = await apiClient.postFile<{
      success: boolean;
      data?: {
        transcript: string;
        transcriptTurns?: TranscriptTurn[];
        segments?: Array<{ start: number; end: number; text: string }>;
        language?: string;
        transcriptionProvider: string;
        transcriptionModel?: string;
        diarizationEnabled?: boolean;
        diarizationProvider?: string;
        diarizationModel?: string;
        alignmentStatus?: 'success' | 'skipped' | 'failed';
        alignmentError?: string;
      };
      provider: string;
      isFallback: boolean;
      processingTimeMs?: number;
      error?: string;
    }>('/v1/transcribe', formData);

    // 类型断言：确保 response.data 的类型正确
    const typedResponse = response as {
      success: boolean;
      data?: {
        transcript: string;
        transcriptTurns?: TranscriptTurn[];
        segments?: Array<{ start: number; end: number; text: string }>;
        language?: string;
        transcriptionProvider: string;
        transcriptionModel?: string;
        diarizationEnabled?: boolean;
        diarizationProvider?: string;
        diarizationModel?: string;
        alignmentStatus?: 'success' | 'skipped' | 'failed';
        alignmentError?: string;
      };
      provider: string;
      isFallback: boolean;
      processingTimeMs?: number;
      error?: string;
    };

    console.log('[TranscriptionService] 转录响应:', {
      success: typedResponse.success,
      hasTranscript: !!typedResponse.data?.transcript,
      hasTranscriptTurns: !!typedResponse.data?.transcriptTurns,
      transcriptLength: typedResponse.data?.transcript?.length || 0,
      turnsCount: typedResponse.data?.transcriptTurns?.length || 0,
      provider: typedResponse.data?.transcriptionProvider,
      isFallback: typedResponse.isFallback,
      error: typedResponse.error,
    });

    if (!typedResponse.success) {
      throw new Error(typedResponse.error || '转录请求失败');
    }

    const data = typedResponse.data;
    if (!data) {
      throw new Error('后端返回数据为空');
    }

    // 阶段 10B-4：检查后端返回的完整数据结构
    if (data.transcript) {
      console.log('[TranscriptionService] 转录成功，返回完整数据');
      return {
        transcript: data.transcript,
        transcriptTurns: data.transcriptTurns,
        provider: (data.transcriptionProvider === 'whisperx' ? 'whisperx' :
                  data.transcriptionProvider === 'backend' ? 'backend' : 'fallback'),
        isFallback: typedResponse.isFallback,
        processingTime: typedResponse.processingTimeMs,
        transcriptionModel: data.transcriptionModel,
        diarizationEnabled: data.diarizationEnabled,
        diarizationProvider: data.diarizationProvider,
        diarizationModel: data.diarizationModel,
        alignmentStatus: data.alignmentStatus,
        alignmentError: data.alignmentError,
      };
    } else {
      // 后端返回失败
      console.log('[TranscriptionService] 后端转录失败');
      throw new Error(typedResponse.error || '转录失败');
    }

  } catch (error) {
    // 后端调用失败，回退到本地模式
    console.warn('[TranscriptionService] 后端转录失败，使用fallback模式:', error);

    return {
      transcript: '',
      provider: 'fallback',
      isFallback: true,
      error: error instanceof Error ? error.message : '转录服务暂不可用，请手动补充文字稿'
    };
  }
}

/**
 * 检查是否可以进行真实转录
 */
export async function canUseRealTranscription(): Promise<boolean> {
  try {
    const response = await apiClient.get<{
      status: string;
      transcriptionFallback: boolean;
    }>('/v1/health');

    return response.success && response.data?.transcriptionFallback === false;
  } catch {
    return false;
  }
}

/**
 * 获取转录服务状态描述
 */
export async function getTranscriptionServiceStatus(): Promise<{
  available: boolean;
  provider: TranscriptionProvider;
  description: string;
}> {
  try {
    const response = await apiClient.get<{
      transcription: {
        type: string;
        available: boolean;
      };
    }>('/v1/providers/info');

    if (response.success && response.data?.transcription) {
      const { type, available } = response.data.transcription;
      return {
        available,
        provider: type === 'backend' ? 'backend' : 'fallback',
        description: available
          ? `使用 ${type} 模式进行语音转录`
          : '后端转录服务暂不可用，使用本地 fallback 模式'
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
 * 标记文字稿为手动编辑
 */
export function markTranscriptAsManual(meeting: Meeting): Partial<Meeting> {
  return {
    transcriptionProvider: 'manual',
    transcriptionIsFallback: false,
    updatedAt: new Date().toISOString()
  };
}
