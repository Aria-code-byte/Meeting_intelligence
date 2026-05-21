/**
 * Transcription Service
 * 提供音频转文字的统一接口
 *
 * 当前支持：
 * - 后端API调用（优先）：/api/v1/transcribe
 * - 本地fallback模式（后端不可用时）
 */

import type { Meeting } from '../types/models';
import { apiClient } from './apiClient';

export type TranscriptionProvider = 'fallback' | 'backend' | 'manual';

export interface TranscriptionInput {
  meetingId: string;
  file?: File;
  audioFileName?: string;
}

export interface TranscriptionResult {
  transcript: string;
  provider: TranscriptionProvider;
  isFallback: boolean;
  processingTime?: number;
  error?: string;
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
    const response = await apiClient.postFile<{
      success: boolean;
      transcript?: string;
      segments?: Array<{ start: string; speaker: string; text: string }>;
      provider: string;
      isFallback: boolean;
      processingTimeMs?: number;
      error?: string;
    }>('/v1/transcribe', formData);

    console.log('[TranscriptionService] 转录响应:', {
      success: response.success,
      hasTranscript: !!response.data?.transcript,
      transcriptLength: response.data?.transcript?.length || 0,
      provider: response.data?.provider,
      isFallback: response.data?.isFallback,
      error: response.error,
    });

    if (!response.success) {
      throw new Error(response.error || '转录请求失败');
    }

    const data = response.data;
    if (!data) {
      throw new Error('后端返回数据为空');
    }

    // 检查是否成功
    if (data.success && data.transcript) {
      console.log('[TranscriptionService] 转录成功，返回 transcript');
      return {
        transcript: data.transcript,
        provider: data.provider === 'backend' ? 'backend' : 'fallback',
        isFallback: data.isFallback,
        processingTime: data.processingTimeMs,
      };
    } else {
      // 后端返回失败，尝试 fallback
      console.log('[TranscriptionService] 后端转录失败，返回空 transcript');
      throw new Error(data.error || '转录失败');
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
