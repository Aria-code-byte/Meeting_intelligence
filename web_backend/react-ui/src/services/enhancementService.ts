/**
 * 文字稿优化服务
 * 调用后端 API 进行 LLM 优化
 */

import type { TranscriptTurn, EnhancedTranscriptTurn } from '../types/models';

const API_BASE = 'http://localhost:8000/api/v1';

export interface EnhancementRequest {
  transcriptTurns: TranscriptTurn[];
  provider?: string;
  model?: string;
}

export interface EnhancementResponse {
  success: boolean;
  enhancedTranscriptTurns: EnhancedTranscriptTurn[] | null;
  provider: string;
  model: string;
  error?: string;
  processingTimeMs?: number;
  metadata?: {
    processedAt: string;
    turnCount: number;
  };
}

// 类型别名，用于App.tsx
export type EnhancementResult = EnhancementResponse;

/**
 * 优化会议转录
 */
export async function enhanceTranscript(
  transcriptTurns: TranscriptTurn[],
  provider: string = 'deepseek',
  model: string = 'deepseek-chat'
): Promise<EnhancementResponse> {
  try {
    const response = await fetch(`${API_BASE}/enhancement/enhance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        transcriptTurns,
        provider,
        model,
      } as EnhancementRequest),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || '优化请求失败');
    }

    return await response.json() as EnhancementResponse;
  } catch (error) {
    console.error('[enhancementService] 优化失败:', error);
    throw error;
  }
}

/**
 * 获取可用的优化提供商
 */
export async function getEnhancementProviders(): Promise<{
  providers: Array<{ id: string; name: string; models: string[] }>;
  default: string;
}> {
  try {
    const response = await fetch(`${API_BASE}/enhancement/providers`);
    if (!response.ok) {
      throw new Error('获取提供商列表失败');
    }
    return await response.json();
  } catch (error) {
    console.error('[enhancementService] 获取提供商失败:', error);
    // 返回默认值
    return {
      providers: [
        { id: 'deepseek', name: 'DeepSeek', models: ['deepseek-chat'] },
      ],
      default: 'deepseek',
    };
  }
}
